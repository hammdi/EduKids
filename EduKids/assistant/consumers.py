import asyncio
import json
import threading
import base64
import io
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async

from .models import Conversation, Message, VirtualAssistant
from .models import MediaFile, Quiz as QuizModel, QuizQuestion as QuizQuestionModel, QuizOption as QuizOptionModel
from .mistral_client import get_client, MistralClient
from . import context_manager
from . import reference_resolver


class AssistantConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer pour la conversation en temps réel avec l'assistant.

    Protocole JSON attendu depuis le client:
    {
      "action": "start" | "message",
      "conversation_id": <optional>,
      "student_id": <optional>,
      "assistant_id": <optional>,
      "language": "fr"|"en"|...,
      "content": "..."
    }

    Le consumer enverra des messages JSON:
    {"type":"partial","text":"..."}
    {"type":"done","text":"..."}
    {"type":"error","text":"..."}
    """

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        # Nothing special for now
        pass

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except Exception:
            await self.send(text_data=json.dumps({"type": "error", "text": "Payload non-JSON"}))
            return

        action = data.get('action')

        if action == 'start_quiz':
            # Client requests to start a quiz on a topic via WebSocket
            # Ensure we have a student_id and create/lookup a conversation
            student_id = data.get('student_id')
            assistant_id = data.get('assistant_id')
            conversation_id = data.get('conversation_id')
            if not student_id:
                await self.send(text_data=json.dumps({"type": "error", "text": "student_id is required to start a quiz."}))
                return
            # Create or get conversation
            conv = await self._get_or_create_conversation(conversation_id, student_id, assistant_id)
            topic = data.get('topic') or data.get('content') or 'Quiz'
            difficulty = data.get('difficulty', 'easy')
            num_q = int(data.get('num_questions', 3))
            age = int(data.get('age', 9))
            try:
                from .quiz_manager import generate_quiz
                quiz = generate_quiz(topic=topic, difficulty=difficulty, num_questions=num_q, age=age)
                # store in lightweight session
                context_manager.set_quiz(conv.id, quiz)
                # persist quiz to DB (async wrapper) and save a structured message in history
                try:
                    saved_quiz = await self._save_quiz(conv, quiz)
                    # record the DB id in the in-memory quiz state so we can persist attempts later
                    qs = context_manager.get_quiz_state(conv.id)
                    if qs is not None and saved_quiz is not None:
                        qs['quiz_db_id'] = saved_quiz.id
                    import json as _json
                    try:
                        # Save the structured quiz JSON as a system message so it appears in history.
                        # Save raw JSON system message for programmatic access but mark as internal so it
                        # does not appear in the user-facing history.
                        await self._save_message(conv, 'assistant', 'system', _json.dumps(quiz), metadata={'is_quiz': True, 'quiz_id': saved_quiz.id, 'internal': True})
                        # Also save a human-readable quiz summary for clearer history
                        try:
                            import re
                            def _build_readable(qdict):
                                lines = []
                                # compute readable title
                                raw_title = qdict.get('title') or qdict.get('topic') or 'Quiz'
                                display = re.sub(r"(?i)^(?:génère|genere|fais[- ]?moi|donne[- ]?moi|crée|cree)\s+(?:un\s+)?quiz(?:\s+(?:sur|de|about)\s*)?", "", raw_title)
                                lines.append(display or 'Quiz')
                                for i, qq in enumerate(qdict.get('questions', []), start=1):
                                    lines.append(f"{i}. {qq.get('question','')}")
                                    for ci, ch in enumerate(qq.get('choices', []) or []):
                                        lines.append(f"   {chr(65+ci)}) {ch}")
                                return "\n".join(lines)
                            readable = _build_readable(quiz)
                            readable = self._sanitize_text(readable)
                            await self._save_message(conv, 'assistant', 'text', readable, metadata={'is_quiz': True, 'quiz_id': saved_quiz.id, 'human_readable': True})
                        except Exception:
                            pass
                    except Exception:
                        # non-fatal
                        pass
                except Exception:
                    # non-fatal if persistence fails
                    saved_quiz = None
                # send first question
                q0 = quiz['questions'][0]
                # mark awaiting answer
                qs = context_manager.get_quiz_state(conv.id)
                if qs is not None:
                    qs['awaiting_answer'] = True
                # compute display title (clean prompting phrases)
                try:
                    import re
                    raw_title = quiz.get('title') or topic
                    display_title = re.sub(r"(?i)^(?:génère|genere|fais[- ]?moi|donne[- ]?moi|crée|cree)\s+(?:un\s+)?quiz(?:\s+(?:sur|de|about)\s*)?", "", raw_title).strip() or 'Quiz'
                except Exception:
                    display_title = quiz.get('title') or 'Quiz'
                # Save assistant starting quiz message (sanitized)
                await self._save_message(conv, 'assistant', 'text', self._sanitize_text(f"D'accord ! Voici un petit quiz : {display_title}"))
                await self.send(text_data=json.dumps({
                    'type': 'quiz_start',
                    'title': display_title,
                    'question': {'id': q0['id'], 'question': q0['question'], 'choices': q0.get('choices', [])}
                }))
            except Exception as e:
                await self.send(text_data=json.dumps({"type": "error", "text": f"Impossible de démarrer le quiz: {str(e)}"}))
            return

        if action == 'message':
            content = data.get('content', '')
            language = data.get('language', 'fr')
            assistant_id = data.get('assistant_id')
            conversation_id = data.get('conversation_id')
            student_id = data.get('student_id')

            # student_id is required to persist conversations (model requires Student FK)
            if not student_id:
                await self.send(text_data=json.dumps({"type": "error", "text": "student_id is required to start a conversation."}))
                return

            # Find the Student by user_id (since student_id is actually User.id from frontend)
            try:
                from students.models import Student
                student = await sync_to_async(Student.objects.get)(user_id=student_id)
                student_id = student.id  # Use actual Student.id
            except Student.DoesNotExist:
                await self.send(text_data=json.dumps({"type": "error", "text": "Student profile not found."}))
                return

            # Ensure conversation exists (sync DB ops via sync_to_async)
            conv = await self._get_or_create_conversation(conversation_id, student_id, assistant_id)

            # Inform client of the conversation id so the frontend can reuse it
            # (prevents creating a new Conversation for every message while the modal is open).
            try:
                await self.send(text_data=json.dumps({"type": "conversation", "id": conv.id, "title": conv.title}))
            except Exception:
                # don't break the flow if client can't receive this
                pass

            # Save incoming message and keep reference so we can replace numeric/letter answers
            # with the chosen option text in the conversation history.
            student_msg = await self._save_message(conv, 'student', 'text', content, metadata={'language': language})

            # Update lightweight in-memory session and try to resolve implicit references
            context_manager.update_history(conv.id, 'student', content)
            session = context_manager.get_session(conv.id)

            # --- Intelligent short-turn analysis (child-friendly correction/response) ---
            # If the last assistant message was a question and the child replied (not asking a new question),
            # give a short, non-judgmental correction or praise and propose a simple follow-up.
            try:
                import re

                def _is_question(text: str) -> bool:
                    if not text:
                        return False
                    t = text.strip()
                    # Basic heuristics: ends with '?', or starts with common interrogative words (FR)
                    if t.endswith('?'):
                        return True
                    if re.match(r"^(?:pourquoi|comment|quoi|quand|où|ou|qui|combien|est-ce que|peux-tu|peux tu|veux-tu|veux tu)", t.lower()):
                        return True
                    return False

                def _normalize_words(text: str):
                    return re.findall(r"[\wàâäéèêëïîôöùûüç'-]+", (text or '').lower(), flags=re.UNICODE)

                # fetch last assistant message (sync DB access wrapped)
                def _last_assistant_message(conv):
                    try:
                        return conv.messages.filter(sender_type='assistant').order_by('-created_at').first()
                    except Exception:
                        return None

                last_assistant = await sync_to_async(_last_assistant_message)(conv)
                student_is_question = _is_question(content)

                if last_assistant and _is_question(last_assistant.content) and not student_is_question:
                    # The child likely answered the assistant's question.
                    # Very light heuristic to judge correctness: measure overlap of content words.
                    q_words = [w for w in _normalize_words(last_assistant.content) if len(w) > 2]
                    s_words = [w for w in _normalize_words(content) if len(w) > 0]
                    if q_words:
                        overlap = len(set(q_words) & set(s_words)) / max(1, len(set(q_words)))
                    else:
                        overlap = 0.0

                    if overlap >= 0.35 or (any(ch.isdigit() for ch in content) and any(ch.isdigit() for ch in last_assistant.content)):
                        # Considered a correct short answer
                        reply = "Bravo ! C'est exact ! 🎉"
                    else:
                        # Encourage and invite retry
                        reply = "Pas tout à fait, mais tu vas y arriver ! Essaie encore 😊"

                    # Propose a small related follow-up (keeps things simple and progressive)
                    follow_up = "On continue ? Voici une petite question facile : Combien font 2 + 2 ?"
                    assistant_reply = f"{reply} {follow_up}"

                    # Save assistant reply and send to client
                    try:
                        await self._save_message(conv, 'assistant', 'text', assistant_reply)
                        await self.send(text_data=json.dumps({'type': 'assistant_reply', 'text': assistant_reply}))
                    except Exception:
                        # Non-fatal: continue to LLM flow if saving fails
                        await self.send(text_data=json.dumps({'type': 'assistant_reply', 'text': assistant_reply}))

                    # We've handled this turn locally; do not continue into full LLM flow for this short-turn reply.
                    return
                # If the student asked a new question, allow the normal LLM flow below to answer it.
            except Exception:
                # If our lightweight analysis fails, fall back to existing flow.
                pass

            # If a quiz is active and awaiting an answer, try to grade this message as an answer
            try:
                quiz = context_manager.get_quiz(conv.id)
                qs = context_manager.get_quiz_state(conv.id)
            except Exception:
                quiz = None
                qs = None

            if quiz and qs and qs.get('awaiting_answer'):
                # grade this answer against current question
                try:
                    current_idx = qs.get('current', 0)
                    q = quiz['questions'][current_idx]
                    from .quiz_manager import grade_answer
                    res = grade_answer(quiz, q['id'], content)
                    # Persist attempt and per-question answer if we have a persisted quiz id
                    try:
                        if qs and qs.get('quiz_db_id'):
                            # Ensure there is a QuizAttempt for this student
                            attempt_id = qs.get('attempt_id')
                            if not attempt_id:
                                try:
                                    attempt = await self._save_quiz_attempt(conv, qs.get('quiz_db_id'), student_id)
                                    qs['attempt_id'] = attempt.id
                                    attempt_id = attempt.id
                                except Exception:
                                    attempt_id = None
                            # Map the local question id to persisted question DB id
                            try:
                                question_db_id = await self._get_question_db_id(qs.get('quiz_db_id'), q.get('id'))
                            except Exception:
                                question_db_id = None
                            selected_index = res.get('user_index')
                            is_correct = bool(res.get('is_correct'))
                            feedback_text = res.get('explanation') or ''
                            # Determine selected_text robustly: prefer mapped choice text, else try to match the user's text to a choice, else use raw user content
                            selected_text = None
                            try:
                                choices = q.get('choices') or []
                                # helper normalizer (similar to grade_answer)
                                import re
                                def _norm(x):
                                    return re.sub(r"[^a-z0-9]+", "", (x or '').lower())

                                # If grade_answer returned an index, prefer that mapping
                                if selected_index is not None and isinstance(selected_index, int) and 0 <= selected_index < len(choices):
                                    selected_text = choices[selected_index]
                                else:
                                    s = str(content).strip()
                                    # If user sent a single letter like 'A'.. map to index
                                    if len(s) == 1 and 'A' <= s.upper() <= chr(65 + max(0, len(choices)-1)):
                                        idx = ord(s.upper()) - 65
                                        if 0 <= idx < len(choices):
                                            selected_text = choices[idx]
                                            selected_index = idx
                                    # If user sent a digit (1-based preferred), map to index
                                    if selected_text is None and s.isdigit():
                                        try:
                                            v = int(s)
                                            if 1 <= v <= len(choices):
                                                selected_text = choices[v-1]
                                                selected_index = v-1
                                            elif 0 <= v < len(choices):
                                                selected_text = choices[v]
                                                selected_index = v
                                        except Exception:
                                            pass
                                    # Try textual match against choices (normalize removing punctuation and accents)
                                    if selected_text is None and choices:
                                        ns = _norm(s)
                                        for ci, ch in enumerate(choices):
                                            if _norm(ch) == ns:
                                                selected_text = ch
                                                selected_index = ci
                                                break
                                    # fallback to raw content
                                    if selected_text is None:
                                        selected_text = content
                            except Exception:
                                selected_text = content
                            if attempt_id and question_db_id is not None:
                                try:
                                    # Update the saved student message to contain the human-readable selected_text
                                    try:
                                        if student_msg and selected_text is not None:
                                            # sanitize before saving into message content
                                            safe = self._sanitize_text(str(selected_text))
                                            await self._update_message_content(student_msg.id, safe)
                                    except Exception:
                                        # non-fatal - do not block saving the attempt
                                        pass

                                    await self._save_quiz_answer(attempt_id, question_db_id, selected_index, is_correct, feedback_text, selected_text=selected_text)
                                except Exception:
                                    # non-fatal
                                    pass
                    except Exception:
                        # don't block grading on persistence errors
                        pass
                    # update state
                    if res.get('is_correct'):
                        qs['correct'] = qs.get('correct', 0) + 1
                    qs['awaiting_answer'] = False
                    qs['current'] = current_idx + 1
                    # save assistant feedback message
                    feedback = res.get('explanation')
                    try:
                        feedback_s = self._sanitize_text(feedback)
                    except Exception:
                        feedback_s = feedback or ''
                    await self._save_message(conv, 'assistant', 'text', feedback_s)
                    # send feedback to client
                    await self.send(text_data=json.dumps({'type': 'quiz_feedback', 'result': res, 'score': {'correct': qs.get('correct',0), 'current': qs.get('current',0), 'total': len(quiz.get('questions',[]))}}))
                    # if more questions, send next
                    if qs['current'] < len(quiz.get('questions', [])):
                        next_q = quiz['questions'][qs['current']]
                        qs['awaiting_answer'] = True
                        await self.send(text_data=json.dumps({'type': 'quiz_question', 'question': {'id': next_q['id'], 'question': next_q['question'], 'choices': next_q.get('choices', [])}}))
                    else:
                        # quiz finished
                        total = len(quiz.get('questions', []))
                        correct = qs.get('correct', 0)
                        summary = f"Tu as eu {correct} bonne(s) réponse(s) sur {total}. Super effort ! 🎉"
                        try:
                            summary_s = self._sanitize_text(summary)
                        except Exception:
                            summary_s = summary
                        await self._save_message(conv, 'assistant', 'text', summary_s)
                        await self.send(text_data=json.dumps({'type': 'quiz_done', 'summary': summary, 'score': {'correct': correct, 'total': total}}))
                        context_manager.clear_quiz(conv.id)
                    return
                except Exception as e:
                    # Fall back to normal LLM flow if grading failed
                    await self.send(text_data=json.dumps({"type": "error", "text": f"Erreur correction quiz: {str(e)}"}))
                    # continue to LLM handling below


            # Build prompt (system_prompt + history + user message). Use assistant-specific base prompt if present.
            assistant = await sync_to_async(VirtualAssistant.objects.get)(id=assistant_id) if assistant_id else None
            base_system = assistant.system_prompt if assistant else ''
            # Child-friendly instructions: simple language, short sentences, positive tone
            child_guard = (
                "Tu es un assistant bienveillant pour les enfants de 6 à 12 ans. "
                "Utilise un langage simple et joyeux, phrases courtes, vocabulaire clair, et rends les réponses encourageantes et ludiques. "
                "Si la question est une erreur, donne une courte explication et encourage l'enfant. "
                "Réponds en français sauf indication contraire. Pas de Markdown ni de listes complexes."
            )
            system_prompt = (base_system + "\n" + child_guard).strip()

            # Attempt to resolve implicit references (e.g. "C'est quoi ses livres ?") using session context
            resolved_content = reference_resolver.resolve_reference(content, session)
            # Simple natural-language triggers: if the user asks the assistant to generate a quiz/image/pdf
            trigger = resolved_content.lower()
            # Detect quiz requests
            if any(kw in trigger for kw in ["quiz", "fais-moi un quiz", "génère un quiz", "donne-moi un quiz", "donne moi un quiz"]):
                try:
                    from .quiz_manager import generate_quiz
                    quiz = generate_quiz(topic=resolved_content, difficulty='easy', num_questions=3, age=9)
                    context_manager.set_quiz(conv.id, quiz)
                    try:
                        saved_quiz = await self._save_quiz(conv, quiz)
                        # record DB id into in-memory quiz state for later attempt persistence
                        qs_tmp = context_manager.get_quiz_state(conv.id)
                        if qs_tmp is not None and saved_quiz is not None:
                            qs_tmp['quiz_db_id'] = saved_quiz.id
                        import json as _json
                        try:
                                # Save raw JSON system message for programmatic access but mark internal
                                await self._save_message(conv, 'assistant', 'system', _json.dumps(quiz), metadata={'is_quiz': True, 'quiz_id': saved_quiz.id, 'internal': True})
                                # Also save a human-readable quiz summary so history is clear for humans
                                try:
                                    # Build readable quiz text
                                    def _build_readable(qdict):
                                        lines = []
                                        title = qdict.get('title') or ''
                                        # Clean title to remove prompting phrases if present
                                        import re
                                        t = re.sub(r"(?i)^(?:génère|genere|fais[- ]?moi|donne[- ]?moi|crée|cree)\s+(?:un\s+)?quiz(?:\s+(?:sur|de|about)\s*)?", "", title or qdict.get('topic',''))
                                        title = title or t or 'Quiz'
                                        lines.append(f"{title}")
                                        for i, qq in enumerate(qdict.get('questions', []), start=1):
                                            qtext = qq.get('question') or ''
                                            lines.append(f"{i}. {qtext}")
                                            choices = qq.get('choices') or []
                                            for ci, ch in enumerate(choices):
                                                lines.append(f"   {chr(65+ci)}) {ch}")
                                        return "\n".join(lines)

                                    readable = _build_readable(quiz)
                                    # sanitize readable text before saving
                                    readable = self._sanitize_text(readable)
                                    await self._save_message(conv, 'assistant', 'text', readable, metadata={'is_quiz': True, 'quiz_id': saved_quiz.id, 'human_readable': True})
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    except Exception:
                        pass
                    q0 = quiz['questions'][0]
                    qs = context_manager.get_quiz_state(conv.id)
                    if qs is not None:
                        qs['awaiting_answer'] = True
                    # Save assistant starting quiz message (sanitize title)
                    try:
                        import re
                        raw_title = quiz.get('title') or resolved_content
                        display_title = re.sub(r"(?i)^(?:génère|genere|fais[- ]?moi|donne[- ]?moi|crée|cree)\s+(?:un\s+)?quiz(?:\s+(?:sur|de|about)\s*)?", "", raw_title).strip() or 'Quiz'
                    except Exception:
                        display_title = quiz.get('title') or 'Quiz'
                    await self._save_message(conv, 'assistant', 'text', self._sanitize_text(f"D'accord ! Voici un petit quiz : {display_title}"))
                    await self.send(text_data=json.dumps({
                        'type': 'quiz_start',
                        'title': display_title,
                        'question': {'id': q0['id'], 'question': q0['question'], 'choices': q0.get('choices', [])}
                    }))
                    return
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "text": f"Erreur génération quiz: {str(e)}"}))
                    return

            # Detect image requests
            if any(kw in trigger for kw in ["image", "dessine", "montre une image", "génère une image", "crée une image", "faire une image"]):
                try:
                    from .media_helpers import generate_image
                    # Use the resolved_content as prompt for the image
                    img_bytes = generate_image(resolved_content, width=800, height=600)
                    b64 = base64.b64encode(img_bytes).decode('ascii')
                    # create thumbnail
                    try:
                        from .media_helpers import create_thumbnail
                        thumb = create_thumbnail(img_bytes)
                    except Exception:
                        thumb = None
                    # persist media file and create Message with file
                    try:
                        media = await self._save_media_file(conv, student_id, img_bytes, filename_prefix='image', media_type='image', thumbnail_bytes=thumb, caption=f"Image générée: {resolved_content}")
                        # also create a message record referencing the file
                        await self._save_message_with_file(conv, 'assistant', 'image', f"Image pour: {resolved_content}", media.file.name, metadata={'caption': resolved_content})
                    except Exception:
                        # fallback: save just a text message
                        await self._save_message(conv, 'assistant', 'text', f"J'ai créé une image pour: {resolved_content}")
                    await self.send(text_data=json.dumps({'type': 'image', 'image_b64': b64, 'content_type': 'image/png', 'caption': resolved_content}))
                    return
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "text": f"Erreur génération image: {str(e)}"}))
                    return

            # Detect PDF/document requests
            if any(kw in trigger for kw in ["pdf", "document", "imprime", "génère un pdf", "crée un pdf"]):
                try:
                    # Decide whether the user wants a summary or exercises in the PDF
                    wants_summary = any(k in trigger for k in ['résum', 'resume', 'résume', 'résumer', 'summary'])
                    wants_exercises = any(k in trigger for k in ['exerc', 'exercice', 'quiz', 'question'])
                    
                    # Helper to clean PDF title from prompting phrases
                    def _clean_pdf_title(raw_text):
                        import re
                        t = (raw_text or '').strip()
                        # Remove leading phrases like "génère moi un pdf sur..."
                        t = re.sub(r"(?i)^(?:génère|genere|fais[- ]?moi|donne[- ]?moi|crée|cree)\s+(?:moi\s+)?(?:un\s+)?(?:pdf|document)\s+(?:sur|de|about)\s*", "", t)
                        t = re.sub(r"(?i)^(?:résum(?:e|é)|resume|résume|résumer|summary)\s*(?:de|of|sur)?\s*", "", t)
                        # Remove extra punctuation and whitespace
                        t = t.strip(' :,-.')
                        # Capitalize first letter
                        if t:
                            t = t[0].upper() + t[1:]
                        return t[:60].strip() or 'Document'
                    
                    title = _clean_pdf_title(resolved_content)
                    paragraphs = []

                    if wants_summary:
                        # Try to generate a child-friendly summary via LLM; fallback otherwise
                        try:
                            client = get_client()
                            prompt = (f"Fais un court résumé pour des enfants de 6 à 12 ans sur le sujet: {resolved_content}. "
                                      "Utilise un langage simple, 3 à 5 phrases, enthousiaste et encourageant. Réponds en français.")
                            chunks = list(client.stream_generate(prompt, system='Tu es un professeur pour enfants; réponds en phrases courtes et claires.', language='fr'))
                            summary = ''.join(chunks).strip()
                            if not summary or len(summary) < 10:
                                summary = None
                        except Exception:
                            summary = None
                        if not summary:
                            summary = f"Voici un petit résumé sur {resolved_content} : {resolved_content} est un sujet intéressant pour les enfants. Lis des histoires simples et pose des questions si tu veux en savoir plus."


                        # Clean and sanitize summary: remove markdown markers and small promo prefixes
                        import re
                        cleaned = self._sanitize_text(summary)
                        # Remove stray emphasis markers left by model (already handled but double-check)
                        cleaned = re.sub(r"^[\*\_\s]+|[\*\_]$", "", cleaned)
                        # Remove short leading phrases like "Super !", "Voici un petit résumé" but keep the rest
                        cleaned = re.sub(r"^\s*(?:super\s*[!:\-\.]?\s*|voici\s*(?:un\s+petit\s+résum\w*)?\s*[!:\-\.]?\s*|voilà\s*[!:\-\.]?\s*)", "", cleaned, flags=re.I)
                        # Remove any explicit instructions added by the model such as sections 'Pour ton PDF' or 'Pour ton PDF:'
                        cleaned = re.split(r"Pour ton PDF[:\-]?", cleaned, flags=re.I)[0].strip()
                        # Remove trailing interactive prompts or meta-questions that invite response
                        cleaned = re.sub(r"\s*(?:Et toi[,\s].*|Tu veux.*|Veux-tu.*|Voulez-vous.*)$", "", cleaned, flags=re.I)
                        # Collapse whitespace and sanitize again
                        cleaned = self._sanitize_text(cleaned)
                        # If cleaning removed too much, fall back to the raw sanitized summary
                        if len(cleaned) < 20:
                            cleaned = self._sanitize_text(summary)

                        # Determine a nicer title (not the user's full question)
                        topic = None
                        m = re.search(r"(?:résum(?:e|é)|resume|résume|résumer|summary)\s*(?:de|of)?\s*(.+)", resolved_content, flags=re.IGNORECASE)
                        if m:
                            topic = m.group(1).strip().strip('.')
                        if not topic:
                            # Try to extract topic from prompt
                            topic = _clean_pdf_title(resolved_content)
                        title = f"Résumé : {topic}"

                        paragraphs = [cleaned]
                        # Log the cleaned summary that will be embedded in the PDF
                        try:
                            import logging
                            logger = logging.getLogger('assistant.pdf')
                            logger.info('WS PDF summary for request "%s": %s', resolved_content, cleaned)
                        except Exception:
                            pass

                    elif wants_exercises:
                        # Generate a small quiz and convert it to paragraph text to include in PDF
                        try:
                            from .quiz_manager import generate_quiz
                            # attempt to extract a topic from cleaned title
                            topic = _clean_pdf_title(resolved_content)
                            quiz = generate_quiz(topic=topic, difficulty='easy', num_questions=3, age=9)
                            # Build human-readable paragraphs: one per question with options
                            # Title for exercises PDF
                            title = f"Exercices : {topic}"
                            paragraphs = [quiz.get('title', 'Quiz')]
                            for q in quiz.get('questions', []):
                                qtext = f"Question: {q.get('question')}"
                                choices = q.get('choices', [])
                                opt_lines = ' ; '.join([f"{chr(65+i)}) {c}" for i, c in enumerate(choices)])
                                paragraphs.append(qtext)
                                paragraphs.append(f"Options: {opt_lines}")
                        except Exception:
                            paragraphs = [f"Exercices sur: {_clean_pdf_title(resolved_content)}"]

                    else:
                        # Default: generate a summary via LLM for generic PDF requests
                        try:
                            client = get_client()
                            prompt = (f"Écris un court texte pour enfants de 6 à 12 ans sur le sujet: {title}. "
                                      "Utilise 3 à 5 phrases simples et encourageantes. Réponds en français.")
                            chunks = list(client.stream_generate(prompt, system='Tu es un professeur pour enfants; sois clair et positif.', language='fr'))
                            content = ''.join(chunks).strip()
                            if content and len(content) >= 20:
                                paragraphs = [self._sanitize_text(content)]
                            else:
                                paragraphs = [f"Voici des informations sur {title}."]
                        except Exception:
                            paragraphs = [f"Voici des informations sur {title}."]

                    from .media_helpers import generate_pdf
                    # Prepare message text to persist (ensure assistant response is saved)
                    message_text = '\n'.join(paragraphs) if paragraphs else resolved_content
                    pdf_bytes = generate_pdf(title, paragraphs)
                    b64 = base64.b64encode(pdf_bytes).decode('ascii')
                    # persist PDF to storage and create MediaFile + Message
                    try:
                        media = await self._save_media_file(conv, student_id, pdf_bytes, filename_prefix='document', media_type='pdf', thumbnail_bytes=None, caption=title)
                        # save assistant message with file reference and include the generated content
                        await self._save_message_with_file(conv, 'assistant', 'text', message_text, media.file.name, metadata={'title': title})
                    except Exception:
                        await self._save_message(conv, 'assistant', 'text', f"J'ai préparé un PDF pour: {resolved_content}")
                    await self.send(text_data=json.dumps({'type': 'pdf', 'pdf_b64': b64, 'content_type': 'application/pdf', 'filename': f"{title}.pdf", 'title': title}))
                    return
                except Exception as e:
                    await self.send(text_data=json.dumps({"type": "error", "text": f"Erreur génération PDF: {str(e)}"}))
                    return

            prompt = f"{system_prompt}\nUser ({language}): {resolved_content}"

            # Call Mistral in a thread to avoid blocking event loop
            try:
                client = get_client()
            except Exception as e:
                await self.send(text_data=json.dumps({"type": "error", "text": f"Assistant unavailable: {str(e)}"}))
                return

            loop = asyncio.get_running_loop()
            q: asyncio.Queue = asyncio.Queue()

            def _stream_worker():
                """Run the blocking generator in a thread and forward chunks to asyncio queue."""
                try:
                    for chunk in client.stream_generate(prompt, system=system_prompt, language=language):
                        # push chunk to async queue
                        loop.call_soon_threadsafe(q.put_nowait, chunk)
                except Exception as e:
                    loop.call_soon_threadsafe(q.put_nowait, {'__error__': str(e)})
                finally:
                    # sentinel to indicate end
                    loop.call_soon_threadsafe(q.put_nowait, None)

            # start worker thread
            worker = threading.Thread(target=_stream_worker, daemon=True)
            worker.start()

            # consume queue and forward to websocket as they arrive
            try:
                collected_chunks = []
                while True:
                    item = await q.get()
                    if item is None:
                        break
                    if isinstance(item, dict) and '__error__' in item:
                        await self.send(text_data=json.dumps({"type": "error", "text": item['__error__']}))
                        break
                    chunk = item
                    collected_chunks.append(chunk)
                    # Optionally throttle partials - still send for perceived responsiveness
                    await self.send(text_data=json.dumps({"type": "partial", "text": chunk}))
                    # save partial
                    await self._save_message(conv, 'assistant', 'text', chunk, metadata={'partial': True})

                # finalize: merge partials
                final_msg = await self._finalize_assistant_message(conv)
                await self.send(text_data=json.dumps({"type": "done", "text": final_msg.content}))
            except Exception as e:
                await self.send(text_data=json.dumps({"type": "error", "text": str(e)}))

        else:
            await self.send(text_data=json.dumps({"type": "error", "text": "Action inconnue"}))

    @sync_to_async
    def _get_or_create_conversation(self, conversation_id, student_id, assistant_id):
        if conversation_id:
            try:
                return Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                pass

        # create minimal conversation if not exists; student/assistant can be null-checked by FK constraints
        assistant = VirtualAssistant.objects.get(id=assistant_id) if assistant_id else VirtualAssistant.objects.filter(is_active=True).first()
        # Student linking left as optional: the Student must be provided in payload for proper linking
        conv = Conversation.objects.create(student_id=student_id if student_id else None, assistant=assistant, title='Conversation')
        return conv

    @sync_to_async
    def _save_message(self, conversation, sender_type, message_type, content, metadata=None):
        metadata = metadata or {}
        msg = Message.objects.create(
            conversation=conversation,
            sender_type=sender_type,
            message_type=message_type,
            content=content,
            metadata=metadata,
            created_at=timezone.now()
        )
        # If this is the first student message and conversation has generic title, set a title
        if sender_type == 'student' and (not conversation.title or conversation.title.lower().startswith('conversation')):
            preview = (content or '').strip().split('\n')[0][:80]
            conversation.title = preview or 'Conversation'
            # Do NOT set conversation.topic here — topic will be computed from the whole conversation
            conversation.save(update_fields=['title'])
        return msg

    @sync_to_async
    def _save_message_with_file(self, conversation, sender_type, message_type, content, filename, metadata=None):
        """Create a Message and attach an existing file path (filename is a storage path)."""
        metadata = metadata or {}
        # Create the message and set the file field to the provided filename path
        msg = Message.objects.create(
            conversation=conversation,
            sender_type=sender_type,
            message_type=message_type,
            content=content,
            metadata=metadata,
            created_at=timezone.now()
        )
        # attach file path to message.file if provided
        if filename:
            # Use the underlying storage save path. We assign file name assuming it exists in default storage.
            msg.file.name = filename
            msg.save(update_fields=['file'])
        return msg

    @sync_to_async
    def _save_media_file(self, conversation, student_user_id, file_bytes, filename_prefix='file', media_type='image', thumbnail_bytes=None, caption=''):
        """Save bytes to default storage via MediaFile and return the created MediaFile instance."""
        from django.core.files.base import ContentFile
        # Build a filename
        import time
        ts = int(time.time())
        ext = 'png' if media_type == 'image' else 'pdf' if media_type == 'pdf' else 'bin'
        filename = f"{filename_prefix}_{conversation.id}_{ts}.{ext}"
        mf = MediaFile.objects.create(
            conversation=conversation,
            uploader_id=conversation.student_id if conversation and conversation.student_id else None,
            media_type=media_type,
            caption=caption,
            metadata={},
        )
        # Save the main file
        mf.file.save(filename, ContentFile(file_bytes), save=False)
        # Save thumbnail if available
        if thumbnail_bytes:
            thumb_name = f"thumb_{filename_prefix}_{conversation.id}_{ts}.jpg"
            mf.thumbnail.save(thumb_name, ContentFile(thumbnail_bytes), save=False)
        mf.save()
        return mf

    @sync_to_async
    def _save_quiz(self, conversation, quiz_dict):
        """Persist a generated quiz dict to DB as Quiz, QuizQuestion and QuizOption records."""
        q = QuizModel.objects.create(
            conversation=conversation,
            title=quiz_dict.get('title') or '',
            topic=quiz_dict.get('topic') or '',
            metadata={k: v for k, v in quiz_dict.items() if k not in ('questions',)}
        )
        question_map = {}
        for i, ques in enumerate(quiz_dict.get('questions', [])):
            qq = QuizQuestionModel.objects.create(quiz=q, text=ques.get('question', ''), order=i, correct_choice_index=ques.get('answer_index'))
            # record mapping from provided question id (if present) to DB id
            try:
                local_qid = str(ques.get('id', i+1))
            except Exception:
                local_qid = str(i+1)
            question_map[local_qid] = qq.id
            choices = ques.get('choices') or []
            for ci, choice in enumerate(choices):
                QuizOptionModel.objects.create(question=qq, text=choice, index=ci)
        # persist mapping in metadata for later lookup
        meta = q.metadata or {}
        meta['question_map'] = question_map
        q.metadata = meta
        q.save(update_fields=['metadata'])
        return q

    @sync_to_async
    def _get_question_db_id(self, quiz_db_id, local_question_id):
        """Return the DB id of a question given the persisted quiz id and the local question id used in the quiz dict."""
        try:
            q = QuizModel.objects.get(id=quiz_db_id)
        except QuizModel.DoesNotExist:
            return None
        meta = q.metadata or {}
        qm = meta.get('question_map', {}) or {}
        return qm.get(str(local_question_id))

    @sync_to_async
    def _save_quiz_attempt(self, conversation, quiz_id, student_id):
        from .models import QuizAttempt
        quiz = QuizModel.objects.get(id=quiz_id)
        from students.models import Student
        student = Student.objects.get(id=student_id)
        attempt = QuizAttempt.objects.create(quiz=quiz, conversation=conversation, student=student, total=0, correct=0, score=0.0)
        return attempt

    @sync_to_async
    def _save_quiz_answer(self, attempt_id, question_db_id, selected_index, is_correct, feedback='', selected_text=None):
        from .models import QuizAttemptAnswer, QuizAttempt
        question = QuizQuestionModel.objects.get(id=question_db_id)
        attempt = QuizAttempt.objects.get(id=attempt_id)
        ans = QuizAttemptAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_index=selected_index,
            selected_text=selected_text,
            is_correct=is_correct,
            feedback=feedback
        )
        # update attempt counters
        attempt.total = attempt.answers.count()
        attempt.correct = attempt.answers.filter(is_correct=True).count()
        attempt.score = (attempt.correct / attempt.total) * 100 if attempt.total > 0 else 0.0
        attempt.save(update_fields=['total', 'correct', 'score'])
        return ans

    @sync_to_async
    def _finalize_quiz_attempt(self, attempt_id):
        from .models import QuizAttempt
        attempt = QuizAttempt.objects.get(id=attempt_id)
        attempt.total = attempt.answers.count()
        attempt.correct = attempt.answers.filter(is_correct=True).count()
        attempt.score = (attempt.correct / attempt.total) * 100 if attempt.total > 0 else 0.0
        attempt.save(update_fields=['total', 'correct', 'score'])
        return attempt

    @sync_to_async
    def _update_message_content(self, msg_id, new_content):
        """Update the content of an existing Message by id.

        This is used to replace short student answers like '1' or 'A' with the
        human-readable option text that the backend resolved, so the conversation
        history is clearer for teachers/parents and for later review.
        """
        try:
            m = Message.objects.get(id=msg_id)
        except Message.DoesNotExist:
            return None
        m.content = new_content
        m.save(update_fields=['content'])
        return m

    def _classify_topic(self, text: str) -> str:
        """Extract a two-word topic from the provided text.

        Algorithm (simple and deterministic):
        - normalize text, remove punctuation
        - tokenize and remove stopwords (FR + EN small list)
        - count word frequencies and pick the top two distinct words
        - if not enough words, fall back to 'sujet general'

        Returns a two-word lowercase string (words separated by a single space).
        """
        if not text:
            return 'sujet general'
        import re
        t = text.lower()
        # remove punctuation (keep unicode letters and numbers)
        t = re.sub(r"[^\w\sàâäéèêëïîôöùûüç'-]", ' ', t, flags=re.UNICODE)
        # simple tokenization
        words = re.findall(r"[\w'-]+", t, flags=re.UNICODE)
        if not words:
            return 'sujet general'

        # small stopword list (French + English common words)
        stopwords = {
            'le','la','les','de','des','du','un','une','et','à','a','en','dans','pour','avec','sur','par',
            'au','aux','ce','ces','qui','que','quoi','il','elle','je','tu','nous','vous','est','sont','etre','être',
            'avoir','faire','pas','ne','se','mon','ma','mes','son','sa','ses','bien','très','plus','moins','comme',
            'the','is','are','of','and','to','in','on','for','with','by','this','that','it','be','was','were','i','you',
        }

        # count frequencies ignoring stopwords and very short tokens
        freq = {}
        for w in words:
            w = w.strip("'\"")
            if len(w) <= 2:
                continue
            if w in stopwords:
                continue
            freq[w] = freq.get(w, 0) + 1

        if not freq:
            # try again with fewer restrictions
            for w in words:
                if len(w) <= 1:
                    continue
                if w in stopwords:
                    continue
                freq[w] = freq.get(w, 0) + 1

        # sort by frequency then by alphabetical order to be deterministic
        items = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
        if not items:
            return 'sujet general'

        # Prefer a 3-word summary; allow 4 words if the 4th has notable frequency
        max_words = 3
        top_count = min(len(items), 4)
        # Determine candidate words
        candidates = [w for w, _ in items[:top_count]]

        if len(candidates) >= 3:
            # normally use top 3
            selected = candidates[:3]
            # include 4th if it has frequency >= 2 and exists
            if len(candidates) >= 4 and items[3][1] >= 2:
                selected = candidates[:4]
        else:
            # fewer than 3 unique words: pad with 'general'
            selected = candidates[:]
            while len(selected) < 3:
                selected.append('general')

        # Build a short human-readable phrase summarizing the topic
        def cap_word(w):
            return w.capitalize() if w else w

        if not selected:
            return 'Sujet général'

        # Join using commas and 'et' for the last element (French-friendly)
        if len(selected) == 1:
            phrase = cap_word(selected[0])
        elif len(selected) == 2:
            phrase = f"{cap_word(selected[0])} et {cap_word(selected[1])}"
        else:
            phrase = ', '.join([cap_word(w) for w in selected[:-1]]) + f" et {cap_word(selected[-1])}"

        # Display topic label in English for history display
        topic = f"Topic: {phrase}"
        # final cleanup and limit length
        topic = topic.strip()
        if len(topic) > 80:
            topic = topic[:80].rsplit(' ', 1)[0].strip()
        return topic

    @sync_to_async
    def _finalize_assistant_message(self, conversation):
        # Merge recent assistant partials into a single assistant message record (simple approach)
        parts = conversation.messages.filter(sender_type='assistant', metadata__has_key='partial').order_by('created_at')
        # join without introducing newlines between token fragments to avoid mid-word spacing
        full_text = ''.join([p.content for p in parts])
        # delete partials
        for p in parts:
            p.delete()
        # create final message (sanitized)
        sanitized = self._sanitize_text(full_text)
        final_msg = Message.objects.create(
            conversation=conversation,
            sender_type='assistant',
            message_type='text',
            content=sanitized,
            metadata={'final': True},
            created_at=timezone.now()
        )
        # Recompute conversation topic based on the full conversation content (all messages)
        try:
            all_msgs = conversation.messages.order_by('created_at')
            aggregate = '\n'.join([m.content or '' for m in all_msgs])
            # classify into a two-word topic
            new_topic = self._classify_topic(aggregate)
            if new_topic and new_topic != conversation.topic:
                conversation.topic = new_topic
                conversation.save(update_fields=['topic'])
                # Also update lightweight session current_topic so follow-ups can resolve references
                try:
                    context_manager.set_current_topic(conversation.id, new_topic)
                except Exception:
                    pass
        except Exception:
            # Don't let topic computation break message finalization
            pass
        return final_msg

    def _sanitize_text(self, text: str) -> str:
        """Normalize LLM output: remove markdown headings/bullets/separators, collapse extra whitespace."""
        if not text:
            return ''
        import re
        t = text
        # Remove horizontal rules and separators
        t = re.sub(r"^-{3,}\s*$", "", t, flags=re.MULTILINE)
        # Remove markdown headings ###, ##, #
        t = re.sub(r"^\s*#{1,6}\s*", "", t, flags=re.MULTILINE)
        # Remove leading list markers ("- ", "* ", numbers like "1. ")
        t = re.sub(r"^\s*[-*]\s+", "", t, flags=re.MULTILINE)
        t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.MULTILINE)
        # Strip bold/italic markers **text**, *text*, __text__, _text_
        t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
        t = re.sub(r"\*(.*?)\*", r"\1", t)
        t = re.sub(r"__(.*?)__", r"\1", t)
        t = re.sub(r"_(.*?)_", r"\1", t)
        # Collapse excessive blank lines
        t = re.sub(r"\n{3,}", "\n\n", t)
        # Collapse any whitespace sequences into single spaces (helps when stream split words)
        t = re.sub(r"[ \t\r\n]+", " ", t)
        # Remove space before punctuation (e.g. "bonjour ," -> "bonjour,")
        t = re.sub(r"\s+([,.;:!?])", r"\1", t)
        return t.strip()
