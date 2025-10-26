from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404
import json
import logging
from django.db.models import Q
from .mistral_client import get_client
from .models import Conversation, Message, MediaFile
from io import BytesIO


@csrf_exempt
def send_message(request):
    """HTTP fallback: accept POST with JSON {student_id, assistant_id, content, language}
    Returns final assistant text. This is synchronous and intended as a fallback for clients
    that cannot use WebSockets.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    content = payload.get('content', '')
    language = payload.get('language', 'fr')
    assistant_id = payload.get('assistant_id')

    try:
        client = get_client()
    except Exception as e:
        return JsonResponse({'error': f'Assistant unavailable: {str(e)}'}, status=503)

    # Collect all chunks (blocking) and return the concatenated result
    try:
        chunks = list(client.stream_generate(content, system='', language=language))
        text = ''.join(chunks)
        return JsonResponse({'text': text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@require_GET
def history_view(request):
    """Return simple conversation history for a student (most recent conversations).

    Query params:
      - student_id (required) - this is the User.id, not Student.id
            - limit (optional, default 5)

    Response format:
    {
      "conversations": [
                 {"id":..., "title":..., "started_at":..., "messages":[{"id":<msg_id>,"sender_type":"student","content":...}, ...] }
      ]
    }
    """
    user_id = request.GET.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
        student_id = student.id
    except Student.DoesNotExist:
        return JsonResponse({'conversations': []})  # No conversations if no student profile

    try:
        limit = int(request.GET.get('limit', '5'))
    except ValueError:
        limit = 5

    convs = Conversation.objects.filter(student_id=student_id).order_by('-started_at')[:limit]
    out = []
    for c in convs:
        msgs = []
        for m in c.messages.order_by('created_at'):
            msg_entry = {
                'id': m.id,
                'sender_type': m.sender_type,
                'message_type': m.message_type,
                'content': m.content,
                'created_at': m.created_at.isoformat(),
            }
            # include file url if present
            try:
                if m.file and getattr(m.file, 'name', None):
                    msg_entry['file_url'] = m.file.url
            except Exception:
                msg_entry['file_url'] = None
            msgs.append(msg_entry)

        out.append({
            'id': c.id,
            'title': c.title,
            'topic': c.topic,
            'started_at': c.started_at.isoformat(),
            'messages': msgs,
        })

    return JsonResponse({'conversations': out})


@require_GET
def conversation_detail(request, conversation_id: int):
    """Return all messages for a specific conversation (owned by the student)."""
    user_id = request.GET.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'student not found'}, status=404)

    conv = get_object_or_404(Conversation, id=conversation_id, student_id=student.id)
    messages = []
    for m in conv.messages.order_by('created_at'):
        # Skip internal/system messages that are intended for programmatic access only
        try:
            meta = m.metadata or {}
            if isinstance(meta, dict) and meta.get('internal'):
                continue
        except Exception:
            # if metadata isn't accessible, fall back to including the message
            pass
        msg_entry = {
            'id': m.id,
            'sender_type': m.sender_type,
            'message_type': m.message_type,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
        }
        try:
            if m.file and getattr(m.file, 'name', None):
                msg_entry['file_url'] = m.file.url
        except Exception:
            msg_entry['file_url'] = None
        messages.append(msg_entry)
    # include media files related to the conversation (images/pdf)
    media_list = []
    try:
        for mf in conv.media_files.order_by('-created_at'):
            media_list.append({
                'id': mf.id,
                'media_type': mf.media_type,
                'file_url': mf.file.url if mf.file and getattr(mf.file, 'name', None) else None,
                'thumbnail_url': mf.thumbnail.url if mf.thumbnail and getattr(mf.thumbnail, 'name', None) else None,
                'caption': mf.caption,
                'created_at': mf.created_at.isoformat(),
            })
    except Exception:
        media_list = []
    # include quizzes saved for this conversation
    quizzes_list = []
    try:
        for q in conv.quizzes.order_by('-created_at'):
            qobj = {'id': q.id, 'title': q.title, 'topic': q.topic, 'created_at': q.created_at.isoformat(), 'questions': []}
            for qq in q.questions.order_by('order'):
                opts = [ { 'index': o.index, 'text': o.text } for o in qq.options.order_by('index') ]
                qobj['questions'].append({ 'id': qq.id, 'order': qq.order, 'text': qq.text, 'correct_choice_index': qq.correct_choice_index, 'options': opts })
            # include attempts and per-question answers for this quiz
            try:
                attempts = []
                for a in q.attempts.order_by('-created_at'):
                    ans_list = []
                    for aa in a.answers.order_by('id'):
                        ans_list.append({
                            'id': aa.id,
                            'question_id': aa.question_id,
                            'selected_index': aa.selected_index,
                            'selected_text': aa.selected_text,
                            'is_correct': aa.is_correct,
                            'feedback': aa.feedback,
                            'created_at': aa.created_at.isoformat() if getattr(aa, 'created_at', None) else None,
                        })
                    attempts.append({
                        'id': a.id,
                        'student_id': a.student_id,
                        'total': a.total,
                        'correct': a.correct,
                        'score': a.score,
                        'created_at': a.created_at.isoformat() if getattr(a, 'created_at', None) else None,
                        'answers': ans_list,
                    })
                qobj['attempts'] = attempts
            except Exception:
                qobj['attempts'] = []
            quizzes_list.append(qobj)
    except Exception:
        quizzes_list = []
    return JsonResponse({
        'conversation': {
            'id': conv.id,
            'title': conv.title,
            'topic': conv.topic,
            'started_at': conv.started_at.isoformat(),
            'messages': messages,
            'media_files': media_list,
            'quizzes': quizzes_list,
        }
    })


@require_GET
def search_conversations(request):
    """Search student's conversations by title or message keywords.

    Query params:
      - student_id (required, User.id)
      - q (required): search query
      - limit (optional, default 10)
    """
    q = request.GET.get('q', '').strip()
    user_id = request.GET.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)
    if not q:
        return JsonResponse({'results': []})

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'results': []})

    try:
        limit = int(request.GET.get('limit', '10'))
    except ValueError:
        limit = 10

    # Conversations matching by title or topic
    conv_qs = Conversation.objects.filter(
        student_id=student.id
    ).filter(
        Q(title__icontains=q) | Q(topic__icontains=q)
    )

    # Conversations matching by message content
    msg_qs = Message.objects.filter(conversation__student_id=student.id, content__icontains=q).values_list('conversation_id', flat=True)

    conv_ids = set(conv_qs.values_list('id', flat=True)) | set(msg_qs)
    conversations = Conversation.objects.filter(id__in=list(conv_ids)).order_by('-started_at')[:limit]

    results = [
        {
            'id': c.id,
            'title': c.title,
            'started_at': c.started_at.isoformat(),
        }
        for c in conversations
    ]
    return JsonResponse({'results': results})


@csrf_exempt
def delete_conversation(request, conversation_id: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    # Accept user_id in body or GET to validate ownership
    user_id = request.GET.get('student_id')
    try:
        if not user_id and request.body:
            payload = json.loads(request.body.decode('utf-8'))
            user_id = payload.get('student_id')
    except Exception:
        user_id = None
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'student not found'}, status=404)

    conv = get_object_or_404(Conversation, id=conversation_id, student_id=student.id)
    conv.delete()
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def edit_message(request, message_id: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    user_id = payload.get('student_id')
    new_content = payload.get('content', '').strip()
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)
    if not new_content:
        return JsonResponse({'error': 'content is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'student not found'}, status=404)

    msg = get_object_or_404(Message, id=message_id, conversation__student_id=student.id)
    if msg.sender_type != 'student':
        return JsonResponse({'error': "Seuls les messages de l'élève peuvent être modifiés."}, status=403)
    msg.content = new_content
    msg.save(update_fields=['content'])
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def delete_message(request, message_id: int):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    user_id = payload.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'student not found'}, status=404)

    msg = get_object_or_404(Message, id=message_id, conversation__student_id=student.id)
    if msg.sender_type != 'student':
        return JsonResponse({'error': "Seuls les messages de l'élève peuvent être supprimés."}, status=403)
    msg.delete()
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def bulk_delete_old_conversations(request):
    """Delete conversations older than N days for the student or keep the last N conversations.

    Accepts JSON body: { student_id: <User.id>, older_than_days: 30 } OR { keep_recent: 5 }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    user_id = payload.get('student_id')
    older_than_days = payload.get('older_than_days')
    keep_recent = payload.get('keep_recent')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)

    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'student not found'}, status=404)

    qs = Conversation.objects.filter(student_id=student.id).order_by('-started_at')
    deleted = 0
    if older_than_days is not None:
        try:
            days = int(older_than_days)
        except ValueError:
            return JsonResponse({'error': 'older_than_days must be an integer'}, status=400)
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = qs.filter(started_at__lt=cutoff).delete()
    elif keep_recent is not None:
        try:
            k = int(keep_recent)
        except ValueError:
            return JsonResponse({'error': 'keep_recent must be an integer'}, status=400)
        ids_to_keep = list(qs.values_list('id', flat=True)[:k])
        deleted, _ = qs.exclude(id__in=ids_to_keep).delete()
    else:
        return JsonResponse({'error': 'Provide older_than_days or keep_recent'}, status=400)

    return JsonResponse({'status': 'ok', 'deleted': deleted})


@csrf_exempt
def generate_quiz(request):
    """Generate a structured quiz in JSON using the LLM.

    Body JSON: { student_id: <User.id>, topic: str, difficulty?: 'easy'|'medium'|'hard', num_questions?: int }
    Returns: { quiz: { title, questions:[{id, question, choices:[...], answer_index}]} }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)
    topic = payload.get('topic') or payload.get('content') or 'Quiz'
    difficulty = payload.get('difficulty', 'easy')
    num_q = int(payload.get('num_questions', 3))
    age = int(payload.get('age', 9))
    try:
        from .quiz_manager import generate_quiz as _generate_quiz
        quiz = _generate_quiz(topic=topic, difficulty=difficulty, num_questions=num_q, age=age)
        return JsonResponse({'quiz': quiz})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def grade_quiz(request):
    """Grade a quiz locally.
    Body JSON: { quiz: {...}, answers: { <id>: index } }
    Returns: { total, correct, details:[{id, correct_index, user_index, is_correct}] }
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)
    quiz = payload.get('quiz')
    answers = payload.get('answers', {})
    if not quiz or 'questions' not in quiz:
        return JsonResponse({'error': 'quiz is required'}, status=400)
    total = len(quiz['questions'])
    correct = 0
    details = []
    for q in quiz['questions']:
        qid = q.get('id')
        ai = q.get('answer_index')
        ui = answers.get(str(qid)) if isinstance(answers, dict) else None
        try:
            ui = int(ui) if ui is not None else None
        except Exception:
            ui = None
        ok = (ui is not None and ai == ui)
        if ok:
            correct += 1
        details.append({'id': qid, 'correct_index': ai, 'user_index': ui, 'is_correct': ok})
    return JsonResponse({'total': total, 'correct': correct, 'details': details})


@csrf_exempt
def generate_image(request):
    """Generate a simple image.
    Body: { text: str, width?: int, height?: int }
    If text mentions 'pomme' or 'apple', draw a cute apple (shape) instead of plain text.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)
    text = (payload.get('text') or 'EduKids Image').strip()
    width = int(payload.get('width', 800))
    height = int(payload.get('height', 600))
    try:
        from .media_helpers import generate_image as _gen_img
        img_bytes = _gen_img(text, width=width, height=height)
        # Persist image to MediaFile and create a Message in the conversation if conversation id provided
        try:
            # Attempt to associate with a conversation if provided in payload
            conv_id = payload.get('conversation_id') or payload.get('conversation')
            if conv_id:
                conv = Conversation.objects.filter(id=conv_id).first()
            else:
                conv = None
            from django.core.files.base import ContentFile
            if conv:
                import time
                ts = int(time.time())
                fname = f"image_{conv.id}_{ts}.png"
                mf = MediaFile.objects.create(conversation=conv, uploader=None, media_type='image', caption=text)
                mf.file.save(fname, ContentFile(img_bytes), save=True)
                # create message referencing the file
                Message.objects.create(conversation=conv, sender_type='assistant', message_type='image', content=f'Image: {text}', file=mf.file.name)
        except Exception:
            # non-fatal: continue
            pass
        return HttpResponse(img_bytes, content_type='image/png')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def generate_pdf(request):
    """Generate a PDF using reportlab. Body: { title: str, paragraphs: [str,...] }"""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)
    title = (payload.get('title') or 'EduKids Document').strip()
    paragraphs = payload.get('paragraphs') or [payload.get('content') or '']
    # If the user asked for a "résumé" (summary) but provided only a short prompt,
    # try to generate a child-friendly summary using the LLM (Mistral) if available.
    try:
        content_probe = ' '.join([p for p in paragraphs if p]).strip()
    except Exception:
        content_probe = ''
    import re
    lower_probe = (content_probe or '').lower()
    # Allow explicit forcing of LLM summary via payload flags
    force_llm = bool(payload.get('use_llm') or payload.get('generate_summary'))
    wants_summary = force_llm or any(k in lower_probe for k in ['résum', 'resume', 'résume', 'résumer', 'résumé', 'summary'])
    if wants_summary:
        # Try to extract a topic after words like 'résumé de' or 'resume of'
        topic = None
        m = re.search(r"(?:résum(?:e|é)|resume|résume|résumer|summary)\s*(?:de|of)?\s*(.+)", content_probe, flags=re.IGNORECASE)
        if m:
            topic = m.group(1).strip().strip('.')
        if not topic:
            # fallback to title if it seems more specific
            if title and title.lower() not in ['edukids document', 'document']:
                topic = title
            else:
                topic = content_probe

        # Build LLM prompt for a short, child-friendly summary
        prompt = (
            f"Fais un court résumé pour des enfants de 6 à 12 ans sur le sujet: {topic}. "
            "Utilise un langage simple, 3 à 5 phrases, enthousiaste et encourageant. Pas de markdown ni listes. Réponds en français."
        )
        summary = None
        try:
            client = get_client()
            chunks = list(client.stream_generate(prompt, system='Tu es un professeur pour enfants; réponds en phrases courtes et claires.', language='fr'))
            summary = ''.join(chunks).strip()
            # basic sanitization: if the LLM echoed back the prompt, ignore
            if not summary or summary.lower().startswith('fais') or len(summary) < 10:
                summary = None
        except Exception:
            summary = None

        if not summary:
            # Simple deterministic fallback summary for offline mode
            summary = f"Voici un petit résumé sur {topic} : {topic} est un sujet intéressant. Les enfants peuvent apprendre en lisant des histoires simples et en posant des questions. Essaie de retenir les idées principales et demande si tu veux en savoir plus !"

        # Log the summary that will be embedded in the PDF (helps debugging LLM output)
        logger = logging.getLogger('assistant.pdf')
        logger.info('PDF generate_quiz summary for topic "%s": %s', topic, summary)

        paragraphs = [summary]
    try:
        from .media_helpers import generate_pdf as _gen_pdf
        pdf_bytes = _gen_pdf(title, paragraphs)
        # persist PDF if conversation id provided
        try:
            conv_id = payload.get('conversation_id') or payload.get('conversation')
            if conv_id:
                conv = Conversation.objects.filter(id=conv_id).first()
            else:
                conv = None
            from django.core.files.base import ContentFile
            if conv:
                import time
                ts = int(time.time())
                fname = f"document_{conv.id}_{ts}.pdf"
                mf = MediaFile.objects.create(conversation=conv, uploader=None, media_type='pdf', caption=title)
                mf.file.save(fname, ContentFile(pdf_bytes), save=True)
                Message.objects.create(conversation=conv, sender_type='assistant', message_type='text', content='PDF généré: '+title, file=mf.file.name)
        except Exception:
            pass
        return HttpResponse(pdf_bytes, content_type='application/pdf')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def pdf_history(request):
    """Return all PDFs generated for a student, ordered by most recent first.
    
    Query params:
      - student_id (required): User.id
      - limit (optional, default 20): max number of PDFs to return
    
    Response format:
    {
      "pdfs": [
        {
          "id": <MediaFile.id>,
          "title": <caption>,
          "file_url": <download_url>,
          "conversation_id": <Conversation.id>,
          "conversation_title": <Conversation.title>,
          "created_at": <ISO datetime>
        },
        ...
      ]
    }
    """
    user_id = request.GET.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)
    
    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'pdfs': []})
    
    try:
        limit = int(request.GET.get('limit', '20'))
    except ValueError:
        limit = 20
    
    # Fetch all PDF MediaFiles for this student's conversations
    pdf_files = MediaFile.objects.filter(
        conversation__student_id=student.id,
        media_type='pdf'
    ).select_related('conversation').order_by('-created_at')[:limit]
    
    pdfs = []
    for mf in pdf_files:
        pdfs.append({
            'id': mf.id,
            'title': mf.caption or 'Document PDF',
            'file_url': mf.file.url if mf.file and getattr(mf.file, 'name', None) else None,
            'conversation_id': mf.conversation_id,
            'conversation_title': mf.conversation.title if mf.conversation else 'Conversation',
            'created_at': mf.created_at.isoformat(),
        })
    
    return JsonResponse({'pdfs': pdfs})


@require_GET
def media_gallery(request):
    """Return all media files (images and PDFs) for a student, grouped by type.
    
    Query params:
      - student_id (required): User.id
      - media_type (optional): 'image' or 'pdf' to filter by type
      - limit (optional, default 50): max number of items to return
    
    Response format:
    {
      "media": [
        {
          "id": <MediaFile.id>,
          "media_type": "image" | "pdf",
          "title": <caption>,
          "file_url": <download_url>,
          "thumbnail_url": <thumbnail_url> (for images),
          "conversation_id": <Conversation.id>,
          "conversation_title": <Conversation.title>,
          "created_at": <ISO datetime>
        },
        ...
      ]
    }
    """
    user_id = request.GET.get('student_id')
    if not user_id:
        return JsonResponse({'error': 'student_id is required'}, status=400)
    
    try:
        from students.models import Student
        student = Student.objects.get(user_id=user_id)
    except Student.DoesNotExist:
        return JsonResponse({'media': []})
    
    try:
        limit = int(request.GET.get('limit', '50'))
    except ValueError:
        limit = 50
    
    media_type_filter = request.GET.get('media_type', '').strip().lower()
    
    # Build query
    query = MediaFile.objects.filter(conversation__student_id=student.id)
    
    if media_type_filter in ['image', 'pdf']:
        query = query.filter(media_type=media_type_filter)
    
    media_files = query.select_related('conversation').order_by('-created_at')[:limit]
    
    media = []
    for mf in media_files:
        item = {
            'id': mf.id,
            'media_type': mf.media_type,
            'title': mf.caption or ('Image' if mf.media_type == 'image' else 'Document PDF'),
            'file_url': mf.file.url if mf.file and getattr(mf.file, 'name', None) else None,
            'conversation_id': mf.conversation_id,
            'conversation_title': mf.conversation.title if mf.conversation else 'Conversation',
            'created_at': mf.created_at.isoformat(),
        }
        # Add thumbnail for images
        if mf.media_type == 'image':
            try:
                item['thumbnail_url'] = mf.thumbnail.url if mf.thumbnail and getattr(mf.thumbnail, 'name', None) else None
            except Exception:
                item['thumbnail_url'] = None
        
        media.append(item)
    
    return JsonResponse({'media': media})


