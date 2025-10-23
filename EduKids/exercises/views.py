from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json
import requests
from students.models import User, Student
from .models import (
    Subject, Topic, Exercise, Lesson, Question, Answer, ExerciseResult, StudentAnswer, 
    SubjectMembership, StudentSubjectView, StudentTopicView,  # Add this
)
from .forms import SubjectForm, TopicForm, ExerciseForm, LessonForm, QuestionForm, AnswerForm, QuestionWithAnswersForm, AnswerFormSet

@login_required
def subjects_list(request):
    """List subjects as classes (teachers see their own)"""
    if request.user.user_type == 'teacher':
        subjects = Subject.objects.filter(created_by=request.user)
    else:
        subjects = Subject.objects.all()
    return render(request, 'exercises/subjects_list.html', {'subjects': subjects})

@login_required
def subject_detail(request, pk):
    """Subject as class: show exercises (assignments), enrolled students, and topics"""
    subject = get_object_or_404(Subject, pk=pk)
    if request.user.user_type == 'teacher' and subject.created_by != request.user:
        return redirect('subjects_list')
    
    memberships = subject.memberships.filter(is_active=True).select_related('student')
    students = [m.student for m in memberships]
    topics = subject.topics.filter(is_active=True)
    topic_form = TopicForm()
    
    # NEW: Subject edit form
    subject_form = SubjectForm(instance=subject) if request.GET.get('edit') == 'subject' else None
    
    if request.method == 'POST':
        if 'update_subject' in request.POST:  # NEW: Handle subject update
            subject_form = SubjectForm(request.POST, request.FILES, instance=subject)
            if subject_form.is_valid():
                subject_form.save()
                messages.success(request, 'Subject updated successfully!')
                return redirect('subject_detail', pk=subject.pk)
        elif 'add_topic' in request.POST:
            topic_form = TopicForm(request.POST)
            if topic_form.is_valid():
                topic = topic_form.save(commit=False)
                topic.subject = subject
                topic.save()
                messages.success(request, 'Topic created successfully!')
                
                # Update subject's updated_at timestamp
                subject.updated_at = timezone.now()
                subject.save()
                
                return redirect('subject_detail', pk=subject.pk)
    
    return render(request, 'exercises/subject_detail.html', {
        'subject': subject,
        'students': students,
        'topics': topics,
        'topic_form': topic_form,
        'subject_form': subject_form,  # NEW
    })

@login_required
def invite_student_to_subject(request, subject_pk):
    """Invite student to subject (grade-matched)"""
    subject = get_object_or_404(Subject, pk=subject_pk, created_by=request.user)
    
    # Filter Student objects by grade_level, then select related User
    available_students = Student.objects.filter(
        grade_level=subject.grade_level
    ).select_related('user').exclude(
        user__id__in=subject.memberships.values('student_id')
    )
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        try:
            # Get the Student object, not User
            student = Student.objects.get(user__id=student_id, grade_level=subject.grade_level)
            SubjectMembership.objects.create(subject=subject, student=student.user)  # FIXED: Use student.user
            messages.success(request, f'{student.user.username} invité!')
        except Student.DoesNotExist:
            messages.error(request, 'Étudiant introuvable.')
        return redirect('subject_detail', pk=subject_pk)
    
    return render(request, 'exercises/invite_student.html', {
        'subject': subject,
        'available_students': available_students,
    })

@login_required
def subjects_list(request):
    if request.user.user_type != 'teacher':
        return redirect('home')  # Only teachers can create subjects
    
    subjects = Subject.objects.filter(is_active=True)
    subject_form = SubjectForm()
    if request.method == 'POST':
        if 'add_subject' in request.POST:
            subject_form = SubjectForm(request.POST, request.FILES)
            if subject_form.is_valid():
                subject_form.instance.created_by = request.user  # Set the creator
                subject_form.save()
                messages.success(request, 'Subject created successfully!')
                return redirect('subjects_list')
    return render(request, 'exercises/subjects_list.html', {
        'subjects': subjects,
        'subject_form': subject_form,
    })



def topic_detail(request, pk):
    topic = get_object_or_404(Topic, pk=pk, is_active=True)
    exercises = topic.exercises.filter(is_active=True)
    lessons = topic.lessons.filter(is_active=True)
    exercise_form = ExerciseForm()
    lesson_form = LessonForm()
    
    # NEW: Topic edit form
    topic_form = TopicForm(instance=topic) if request.GET.get('edit') == 'topic' else None
    
    if request.method == 'POST':
        if 'update_topic' in request.POST:  # NEW
            topic_form = TopicForm(request.POST, instance=topic)
            if topic_form.is_valid():
                topic_form.save()
                messages.success(request, 'Topic updated successfully!')
                return redirect('topic_detail', pk=topic.pk)
        elif 'add_exercise' in request.POST:
            exercise_form = ExerciseForm(request.POST)
            if exercise_form.is_valid():
                exercise = exercise_form.save(commit=False)
                exercise.topic = topic
                exercise.creator = request.user
                exercise.save()
                topic.updated_at = timezone.now()
                topic.save()
                topic.subject.updated_at = timezone.now()
                topic.subject.save()
                messages.success(request, 'Exercise created successfully!')
                return redirect('topic_detail', pk=topic.pk)
        elif 'add_lesson' in request.POST:
            lesson_form = LessonForm(request.POST, request.FILES)
            if lesson_form.is_valid():
                lesson = lesson_form.save(commit=False)
                lesson.topic = topic
                lesson.save()
                # Update timestamps for new content indicator
                topic.updated_at = timezone.now()
                topic.save()
                topic.subject.updated_at = timezone.now()
                topic.subject.save()
                messages.success(request, 'Lesson created successfully!')
                return redirect('topic_detail', pk=topic.pk)
    return render(request, 'exercises/topic_detail.html', {
        'topic': topic,
        'exercises': exercises,
        'lessons': lessons,
        'exercise_form': exercise_form,
        'lesson_form': lesson_form,
        'topic_form': topic_form,  # NEW
    })

@login_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    questions = exercise.questions.all()
    question_form = QuestionWithAnswersForm()
    answer_formset = AnswerFormSet()
    answer_form = AnswerForm()
    
    # NEW: Exercise edit form
    exercise_form = ExerciseForm(instance=exercise) if request.GET.get('edit') == 'exercise' else None
    
    if request.method == 'POST':
        if 'update_exercise' in request.POST:  # NEW: Handle exercise update
            exercise_form = ExerciseForm(request.POST, instance=exercise)
            if exercise_form.is_valid():
                exercise_form.save()
                messages.success(request, 'Exercise updated successfully!')
                return redirect('exercise_detail', pk=exercise.pk)
        # EXISTING: Add question logic (unchanged)
        elif 'add_question' in request.POST:
            print("add_question in POST")  # Debug
            question_form = QuestionWithAnswersForm(request.POST, request.FILES)
            print("question_form valid:", question_form.is_valid())  # Debug
            
            if not question_form.is_valid():
                print("question_form errors:", question_form.errors)  # Debug
            
            # For dictée, we don't need answer formset
            if exercise.exercise_type == 'dictée':
                if question_form.is_valid():
                    question_text = question_form.cleaned_data['question_text']
                    
                    question = Question.objects.create(
                        exercise=exercise,
                        question_text=question_text,
                        question_type=question_form.cleaned_data['question_type'],
                        points=question_form.cleaned_data['points'],
                        hint=question_form.cleaned_data.get('hint', ''),
                        image=question_form.cleaned_data.get('image'),
                        creator=request.user
                    )
                    
                    # For dictée, create one answer that matches the question text
                    Answer.objects.create(
                        question=question,
                        answer_text=question_text,  # Expected answer is the same as question text
                        is_correct=True,
                        explanation="Réponse attendue pour la dictée"
                    )
                    
                    messages.success(request, 'Question de dictée ajoutée avec succès!')
                    return redirect('exercise_detail', pk=exercise.pk)
                else:
                    messages.error(request, 'Erreur dans le formulaire de question.')
            
            else:
                # For other exercise types (QCM, texte_à_trous)
                answer_formset = AnswerFormSet(request.POST)
                print("answer_formset valid:", answer_formset.is_valid())  # Debug
                
                if not answer_formset.is_valid():
                    print("answer_formset errors:", answer_formset.errors)  # Debug
                
                if question_form.is_valid() and answer_formset.is_valid():
                    if question_form.cleaned_data['question_text']:
                        print("Creating question")  # Debug
                        question = Question.objects.create(
                            exercise=exercise,
                            question_text=question_form.cleaned_data['question_text'],
                            question_type=question_form.cleaned_data['question_type'],
                            points=question_form.cleaned_data['points'],
                            hint=question_form.cleaned_data.get('hint', ''),
                            image=question_form.cleaned_data.get('image'),
                            creator=request.user
                        )
                        
                        # Create answers for QCM and texte_à_trous
                        for form in answer_formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data.get('answer_text'):
                                is_correct = form.cleaned_data.get('is_correct', False)
                                
                                # FIX: For texte_à_trous, always set is_correct=True (since the hidden word is the expected answer)
                                if exercise.exercise_type == 'texte_à_trous':
                                    is_correct = True
                                
                                Answer.objects.create(
                                    question=question,
                                    answer_text=form.cleaned_data['answer_text'],
                                    is_correct=is_correct,
                                    explanation=form.cleaned_data.get('explanation', '')
                                )
                        
                        messages.success(request, 'Question ajoutée avec succès!')
                        return redirect('exercise_detail', pk=exercise.pk)
                    else:
                        messages.error(request, 'Le texte de la question est requis.')
        
        elif 'add_answer' in request.POST:
            answer_form = AnswerForm(request.POST)
            if answer_form.is_valid():
                Answer.objects.create(
                    question=get_object_or_404(Question, pk=request.POST.get('question_id')),
                    answer_text=answer_form.cleaned_data['answer_text'],
                    is_correct=answer_form.cleaned_data['is_correct'],
                    explanation=answer_form.cleaned_data.get('explanation', '')
                )
                messages.success(request, 'Réponse ajoutée avec succès!')
                return redirect('exercise_detail', pk=exercise.pk)
    
    return render(request, 'exercises/exercise_detail.html', {
        'exercise': exercise,
        'questions': questions,
        'question_form': question_form,
        'answer_formset': answer_formset,
        'answer_form': answer_form,
        'exercise_form': exercise_form,  # NEW
    })

@login_required
def delete_lesson(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lesson deleted successfully!')
        return redirect('topic_detail', pk=lesson.topic.pk)
    return redirect('topic_detail', pk=lesson.topic.pk)  # Fallback

@login_required
def delete_exercise(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    if request.method == 'POST':
        exercise.delete()
        messages.success(request, 'Exercise deleted successfully!')
        return redirect('topic_detail', pk=exercise.topic.pk)
    return redirect('topic_detail', pk=exercise.topic.pk)  # Fallback

@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('exercise_detail', pk=question.exercise.pk)
    return redirect('exercise_detail', pk=question.exercise.pk)  # Fallback

@login_required
def student_subjects_list(request):
    if request.user.user_type != 'student':
        return redirect('home')
    
    # Get search query from GET parameters
    search_query = request.GET.get('search', '').strip()
    
    # Only show subjects where the student has an active membership
    subjects = Subject.objects.filter(
        memberships__student=request.user,
        memberships__is_active=True,
        is_active=True
    ).distinct()
    
    # Apply search filter if query provided
    if search_query:
        subjects = subjects.filter(name__icontains=search_query)
    
    # New code: add indicators for new content
    subjects_with_indicators = []
    for subject in subjects:
        view_record = StudentSubjectView.objects.filter(student=request.user, subject=subject).first()
        has_new = view_record is None or subject.updated_at > view_record.last_viewed
        subjects_with_indicators.append({'subject': subject, 'has_new': has_new})
    
    return render(request, 'exercises/student_subjects_list.html', {
        'subjects_with_indicators': subjects_with_indicators,
        'search_query': search_query,  # Pass query back to template
    })

@login_required
def student_subject_detail(request, pk):
    """Student view for a specific subject showing topics"""
    subject = get_object_or_404(Subject, pk=pk, is_active=True)
    
    try:
        student = request.user.student_profile
        student_grade = student.grade_level
        # Filter topics by student's grade level
        topics = subject.topics.filter(
            grade_level=student_grade,
            is_active=True
        ).order_by('order', 'name')
    except AttributeError:
        # If no student profile, show all topics
        topics = subject.topics.filter(is_active=True).order_by('order', 'name')
        student_grade = None
    
    # Add counts for each topic
    for topic in topics:
        topic.lessons_count = topic.lessons.filter(is_active=True).count()
        topic.exercises_count = topic.exercises.filter(is_active=True).count()
    
    # New code: indicate if there's new content in topics
    topics_with_indicators = []
    for topic in topics:
        view_record = StudentTopicView.objects.filter(student=request.user, topic=topic).first()
        has_new = view_record is None or topic.updated_at > view_record.last_viewed
        topics_with_indicators.append({'topic': topic, 'has_new': has_new})
    
    # Update subject view
    StudentSubjectView.objects.update_or_create(
        student=request.user, subject=subject,
        defaults={'last_viewed': timezone.now()}
    )
    
    return render(request, 'exercises/student_subject_detail.html', {
        'subject': subject,
        'topics_with_indicators': topics_with_indicators,
        'student_grade': student_grade,
    })

@login_required 
def student_topic_detail(request, pk):
    """Student view for a specific topic showing lessons and exercises"""
    topic = get_object_or_404(Topic, pk=pk, is_active=True)
    lessons = topic.lessons.filter(is_active=True).order_by('order', 'created_at')
    
    # Get all active exercises
    all_exercises = topic.exercises.filter(is_active=True).order_by('name')
    
    # Categorize exercises
    now = timezone.now()
    upcoming_exercises = []
    available_exercises = []
    expired_exercises = []
    
    for exercise in all_exercises:
        if exercise.available_from and exercise.available_from > now:
            upcoming_exercises.append(exercise)
        elif exercise.due_date and exercise.due_date <= now:
            expired_exercises.append(exercise)
        else:
            available_exercises.append(exercise)
    
    # Add latest result to each exercise
    for exercise in upcoming_exercises + available_exercises + expired_exercises:
        exercise.latest_result = ExerciseResult.objects.filter(
            student=request.user,
            exercise=exercise
        ).order_by('-completed_at').first()
    
    # Update topic view for indicator reset
    StudentTopicView.objects.update_or_create(
        student=request.user, topic=topic,
        defaults={'last_viewed': now}
    )
    
    return render(request, 'exercises/student_topic_detail.html', {
        'topic': topic,
        'lessons': lessons,
        'upcoming_exercises': upcoming_exercises,
        'available_exercises': available_exercises,
        'expired_exercises': expired_exercises,
    })

@login_required
def student_exercise_start(request, pk):
    """Student starts an exercise"""
    exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
    
    # Check availability window
    if exercise.available_from and exercise.available_from > timezone.now():
        messages.error(request, 'This assignment is not yet available.')
        return redirect('student_topic_detail', pk=exercise.topic.pk)
    if exercise.due_date and exercise.due_date <= timezone.now():
        messages.error(request, 'This assignment has expired.')
        return redirect('student_topic_detail', pk=exercise.topic.pk)
    
    questions = exercise.questions.all().order_by('order')
    
    # Debug output
    print(f"Exercise: {exercise.name}")
    print(f"Questions count: {questions.count()}")
    print(f"Questions: {list(questions)}")
    
    # Add answers to each question for QCM
    for question in questions:
        question.answer_choices = question.answers.all().order_by('order')
        print(f"Question {question.pk}: {question.answer_choices.count()} answers")
    
    return render(request, 'exercises/student_exercise_start.html', {
        'exercise': exercise,
        'questions': questions,
    })

@login_required
def submit_exercise(request, pk):
    """Handle exercise submission and return results"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
    
    try:
        # Get submitted answers
        submitted_answers = json.loads(request.body)
        
        # Calculate score
        total_questions = exercise.questions.count()
        correct_answers = 0
        results = []
        
        # Create exercise result record
        exercise_result = ExerciseResult.objects.create(
            student=request.user,
            exercise=exercise,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            score=0,  # Will update after calculation
            total_points=exercise.points,
            earned_points=0  # Will update after calculation
        )
        
        earned_points = 0
        
        for question in exercise.questions.all():
            question_id = str(question.pk)
            submitted_answer = submitted_answers.get(question_id, '')
            
            if exercise.exercise_type == 'QCM':
                # For QCM, check if selected answer is correct
                print(f"\n=== QCM SCORING ===")
                print(f"Question ID: {question.pk}")
                print(f"Submitted answer ID: '{submitted_answer}'")
                
                try:
                    if submitted_answer:
                        selected_answer = question.answers.get(pk=int(submitted_answer))
                        is_correct = selected_answer.is_correct
                        correct_answer = question.answers.filter(is_correct=True).first()
                        
                        print(f"Selected answer: '{selected_answer.answer_text}'")
                        print(f"Is correct: {is_correct}")
                        
                        if is_correct:
                            points_earned_for_question = question.points
                            correct_answers += 1
                        else:
                            points_earned_for_question = 0
                            
                    else:
                        # No answer selected
                        is_correct = False
                        selected_answer = None
                        correct_answer = question.answers.filter(is_correct=True).first()
                        points_earned_for_question = 0
                        print("No answer selected")
                        
                except (ValueError, Answer.DoesNotExist) as e:
                    print(f"Error processing QCM answer: {e}")
                    is_correct = False
                    selected_answer = None
                    correct_answer = question.answers.filter(is_correct=True).first()
                    points_earned_for_question = 0
                
                # Save student answer
                StudentAnswer.objects.create(
                    exercise_result=exercise_result,
                    question=question,
                    student_answer=selected_answer.answer_text if selected_answer else '',
                    is_correct=is_correct,
                    points_earned=points_earned_for_question
                )
                
                results.append({
                    'question_id': question.pk,
                    'question_text': question.question_text[:60] + '...' if len(question.question_text) > 60 else question.question_text,
                    'submitted_answer': selected_answer.answer_text if selected_answer else 'Aucune réponse',
                    'correct_answer': correct_answer.answer_text if correct_answer else 'Aucune réponse correcte trouvée',
                    'is_correct': is_correct,
                    'explanation': correct_answer.explanation if correct_answer and correct_answer.explanation else None,
                })
                
                earned_points += points_earned_for_question
                print(f"Points earned: {points_earned_for_question}/{question.points}")
                print(f"=== END QCM SCORING ===\n")
            
            elif exercise.exercise_type == 'texte_à_trous':
                # For fill-in-the-blanks, compare each blank answer
                print(f"\n=== TEXTE À TROUS SCORING ===")
                print(f"Question ID: {question.pk}")
                print(f"Submitted answers: {submitted_answer}")
                
                # Get correct answers for this question (ordered)
                correct_answers_db = question.answers.filter(is_correct=True).order_by('order')
                correct_answer_texts = [answer.answer_text.strip().lower() for answer in correct_answers_db]
                
                print(f"Expected answers: {correct_answer_texts}")
                
                # Process submitted answers
                if isinstance(submitted_answer, list):
                    submitted_answer_texts = [ans.strip().lower() for ans in submitted_answer]
                else:
                    # Handle single answer or empty submission
                    submitted_answer_texts = [submitted_answer.strip().lower()] if submitted_answer else []
                
                print(f"Submitted answers (normalized): {submitted_answer_texts}")
                
                # Word-by-word comparison for texte_à_trous (similar to dictée)
                total_blanks = len(correct_answer_texts)
                correct_blank_count = 0
                
                if total_blanks == 0:
                    print("❌ No blanks to compare")
                    is_correct = False
                    points_earned_for_question = 0
                else:
                    print(f"\n--- BLANK BY BLANK COMPARISON ---")
                    max_length = max(len(correct_answer_texts), len(submitted_answer_texts))
                    
                    for i in range(max_length):
                        if i < len(correct_answer_texts) and i < len(submitted_answer_texts):
                            correct_blank = correct_answer_texts[i]
                            submitted_blank = submitted_answer_texts[i]
                            
                            # Exact match (case-insensitive)
                            if submitted_blank == correct_blank:
                                correct_blank_count += 1
                                print(f"Blank {i+1}: '{submitted_blank}' = '{correct_blank}' ✅")
                            else:
                                # Check for similar words (typo tolerance)
                                if len(correct_blank) >= 3 and len(submitted_blank) >= 3:
                                    # Calculate similarity
                                    min_len = min(len(correct_blank), len(submitted_blank))
                                    max_len = max(len(correct_blank), len(submitted_blank))
                                    
                                    matching_chars = sum(1 for j in range(min_len) 
                                                       if correct_blank[j] == submitted_blank[j])
                                    
                                    char_similarity = matching_chars / max_len
                                    length_penalty = abs(len(correct_blank) - len(submitted_blank)) / max_len
                                    
                                    # Accept if similarity is high enough
                                    if char_similarity >= 0.85 and length_penalty <= 0.2:
                                        correct_blank_count += 0.8  # Partial credit for typos
                                        print(f"Blank {i+1}: '{submitted_blank}' ≈ '{correct_blank}' ⚠️ (typo, 80% credit)")
                                    else:
                                        print(f"Blank {i+1}: '{submitted_blank}' ≠ '{correct_blank}' ❌")
                                else:
                                    print(f"Blank {i+1}: '{submitted_blank}' ≠ '{correct_blank}' ❌")
                        
                        elif i < len(correct_answer_texts):
                            # Missing blank
                            print(f"Blank {i+1}: MISSING ≠ '{correct_answer_texts[i]}' ❌")
                        
                        elif i < len(submitted_answer_texts):
                            # Extra blank (student provided more answers than expected)
                            print(f"Blank {i+1}: '{submitted_answer_texts[i]}' = EXTRA ❌")
                    
                    # Calculate score based on correct blanks
                    blank_accuracy = correct_blank_count / total_blanks
                    print(f"\n--- SCORING ---")
                    print(f"Correct blanks: {correct_blank_count:.1f}/{total_blanks}")
                    print(f"Blank accuracy: {blank_accuracy:.1%}")
                    
                    # Calculate points based on accuracy
                    points_earned_for_question = round(question.points * blank_accuracy, 2)
                    
                    # For "correct/incorrect" classification, use 80% threshold
                    if blank_accuracy >= 0.8:
                        is_correct = True
                        print(f"Result: ✅ CORRECT (≥80% accuracy)")
                    else:
                        is_correct = False
                        print(f"Result: ❌ INCORRECT (<80% accuracy, but partial credit given)")
                    
                    print(f"Points earned: {points_earned_for_question}/{question.points}")
                
                # Save student answer
                StudentAnswer.objects.create(
                    exercise_result=exercise_result,
                    question=question,
                    student_answer=json.dumps(submitted_answer_texts) if submitted_answer_texts else '',
                    is_correct=is_correct,
                    points_earned=points_earned_for_question
                )
                
                # Prepare feedback
                if submitted_answer_texts and correct_answer_texts:
                    feedback = f"Précision des blancs: {blank_accuracy:.1%} ({correct_blank_count:.1f}/{total_blanks} blancs corrects)"
                else:
                    feedback = "Aucune réponse fournie"
                
                results.append({
                    'question_id': question.pk,
                    'question_text': question.question_text[:60] + '...' if len(question.question_text) > 60 else question.question_text,
                    'submitted_answer': ', '.join(submitted_answer_texts) if submitted_answer_texts else 'Aucune réponse',
                    'correct_answer': ', '.join(correct_answer_texts),
                    'is_correct': is_correct,
                    'explanation': feedback,
                })
                
                if is_correct:
                    correct_answers += 1
                
                earned_points += points_earned_for_question
                print(f"=== END TEXTE À TROUS SCORING ===\n")
            
            elif exercise.exercise_type == 'dictée':
                # EXISTING DICTÉE CODE (unchanged)
                correct_answer = question.answers.first()
                if correct_answer:
                    submitted_text = submitted_answer.strip() if submitted_answer else ""
                    correct_text = correct_answer.answer_text.strip()
                    
                    print(f"\n=== DICTÉE SCORING SYSTEM ===")
                    print(f"Question ID: {question.pk}")
                    print(f"Correct text: '{correct_text}'")
                    print(f"Submitted text: '{submitted_text}'")
                    
                    # Check if input is empty
                    if not submitted_text:
                        print("❌ Empty submission detected")
                        is_correct = False
                        points_earned_for_question = 0
                    else:
                        # Clean and normalize function
                        import re
                        
                        def clean_word(word):
                            # Remove punctuation and convert to lowercase
                            cleaned = re.sub(r'[.,!?;:"\'-]', '', word.lower().strip())
                            return cleaned
                        
                        def normalize_text(text):
                            # Split into words and clean each word
                            words = text.split()
                            cleaned_words = [clean_word(word) for word in words if clean_word(word)]
                            return cleaned_words
                        
                        # Get normalized word lists
                        correct_words = normalize_text(correct_text)
                        submitted_words = normalize_text(submitted_text)
                        
                        print(f"Correct words: {correct_words}")
                        print(f"Submitted words: {submitted_words}")
                        print(f"Expected word count: {len(correct_words)}")
                        print(f"Submitted word count: {len(submitted_words)}")
                        
                        # Word-by-word comparison
                        total_words = len(correct_words)
                        correct_word_count = 0
                        
                        if total_words == 0:
                            print("❌ No words to compare")
                            is_correct = False
                            points_earned_for_question = 0
                        else:
                            # Compare each position
                            max_length = max(len(correct_words), len(submitted_words))
                            
                            print(f"\n--- WORD BY WORD COMPARISON ---")
                            for i in range(max_length):
                                if i < len(correct_words) and i < len(submitted_words):
                                    correct_word = correct_words[i]
                                    submitted_word = submitted_words[i]
                                    
                                    # Exact match
                                    if correct_word == submitted_word:
                                        correct_word_count += 1
                                        print(f"Position {i+1}: '{submitted_word}' = '{correct_word}' ✅")
                                    else:
                                        # Check for similar words (allow 1-2 character differences for longer words)
                                        if len(correct_word) >= 3 and len(submitted_word) >= 3:
                                            # Calculate character differences
                                            min_len = min(len(correct_word), len(submitted_word))
                                            max_len = max(len(correct_word), len(submitted_word))
                                            
                                            # Count matching characters in same positions
                                            matching_chars = sum(1 for j in range(min_len) 
                                                               if correct_word[j] == submitted_word[j])
                                            
                                            # Calculate similarity (allow some typos)
                                            char_similarity = matching_chars / max_len
                                            length_penalty = abs(len(correct_word) - len(submitted_word)) / max_len
                                            
                                            # Accept if similarity is high enough (85% similar with small length difference)
                                            if char_similarity >= 0.85 and length_penalty <= 0.2:
                                                correct_word_count += 0.8  # Partial credit for typos
                                                print(f"Position {i+1}: '{submitted_word}' ≈ '{correct_word}' ⚠️ (typo, 80% credit)")
                                            else:
                                                print(f"Position {i+1}: '{submitted_word}' ≠ '{correct_word}' ❌")
                                        else:
                                            print(f"Position {i+1}: '{submitted_word}' ≠ '{correct_word}' ❌")
                                
                                elif i < len(correct_words):
                                    # Missing word
                                    print(f"Position {i+1}: MISSING ≠ '{correct_words[i]}' ❌")
                                
                                elif i < len(submitted_words):
                                    # Extra word
                                    print(f"Position {i+1}: '{submitted_words[i]}' = EXTRA ❌")
                            
                            # Calculate score based on correct words
                            word_accuracy = correct_word_count / total_words
                            print(f"\n--- SCORING ---")
                            print(f"Correct words: {correct_word_count:.1f}/{total_words}")
                            print(f"Word accuracy: {word_accuracy:.1%}")
                            

                            # NEW SCORING SYSTEM - Use actual percentage with proper rounding
                            # Convert word accuracy to points (proportional scoring)
                            points_earned_for_question = round(question.points * word_accuracy, 2)

                            # For "correct/incorrect" classification, still use 80% threshold
                            # But actual score reflects real percentage
                            if word_accuracy >= 0.8:  # 80% or better = considered "correct"
                                is_correct = True
                                print(f"Result: ✅ CORRECT (≥80% accuracy)")
                            else:
                                is_correct = False
                                print(f"Result: ❌ INCORRECT (<80% accuracy, but partial credit given)")

                            print(f"Word accuracy score: {word_accuracy:.1%}")
                            print(f"Points earned: {points_earned_for_question}/{question.points}")
                    
                    print(f"=== END DICTÉE SCORING ===\n")
                    
                    # Save student answer
                    StudentAnswer.objects.create(
                        exercise_result=exercise_result,
                        question=question,
                        student_answer=submitted_text,
                        is_correct=is_correct,
                        points_earned=points_earned_for_question
                    )
                    
                    # Prepare detailed feedback for results
                    if submitted_text and correct_text:
                        correct_words = normalize_text(correct_text)
                        submitted_words = normalize_text(submitted_text)
                        word_accuracy = correct_word_count / len(correct_words) if correct_words else 0
                        
                        feedback = f"Précision des mots: {word_accuracy:.1%} ({correct_word_count:.1f}/{len(correct_words)} mots corrects)"
                    else:
                        feedback = "Aucune réponse fournie"
                    
                    results.append({
                        'question_id': question.pk,
                        'question_text': 'Dictée (texte lu à voix haute)',
                        'submitted_answer': submitted_text or 'Aucune réponse',
                        'correct_answer': correct_text,
                        'is_correct': is_correct,
                        'explanation': feedback,
                    })
                    
                    if is_correct:
                        correct_answers += 1
                    
                    earned_points += points_earned_for_question
                    
                else:
                    print(f"❌ No correct answer found for question {question.pk}")
        
        # Calculate ACTUAL percentage score based on points earned, not just correct/incorrect
        if total_questions > 0:
            # Calculate based on actual points earned vs total possible points
            total_possible_points = sum(q.points for q in exercise.questions.all())
            score_percentage = (earned_points / total_possible_points * 100) if total_possible_points > 0 else 0
        else:
            score_percentage = 0

        exercise_result.score = score_percentage
        exercise_result.earned_points = earned_points
        exercise_result.save()

        print(f"Final score: {score_percentage:.1f}%, earned points: {earned_points}/{total_possible_points}")
        
        return JsonResponse({
            'success': True,
            'score_percentage': round(score_percentage, 1),
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'results': results,
        })
        
    except Exception as e:
        import traceback
        print(f"Error in submit_exercise: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def teacher_dashboard(request):
    """Dashboard for teachers to overview their subjects/classes"""
    if request.user.user_type != 'teacher':
        return redirect('subjects_list')  # Redirect non-teachers
    
    # Get teacher's subjects (classes)
    subjects = Subject.objects.filter(created_by=request.user, is_active=True)
    
    # Calculate stats
    total_subjects = subjects.count()
    total_students = sum(subject.memberships.filter(is_active=True).count() for subject in subjects)
    
    # Recent exercise results from teacher's subjects
    recent_results = ExerciseResult.objects.filter(
        exercise__topic__subject__created_by=request.user
    ).select_related('student', 'exercise').order_by('-completed_at')[:10]
    
    # Add student count to each subject for display
    for subject in subjects:
        subject.student_count = subject.memberships.filter(is_active=True).count()
    
    return render(request, 'exercises/teacher_dashboard.html', {
        'subjects': subjects,
        'total_subjects': total_subjects,
        'total_students': total_students,
        'recent_results': recent_results,
    })

@login_required
def set_exercise_assignment(request, pk):
    """Set or update exercise assignment details"""
    exercise = get_object_or_404(Exercise, pk=pk)
    
    if request.method == 'POST':
        available_from = request.POST.get('available_from')
        due_date = request.POST.get('due_date')
        
        exercise.available_from = available_from or None
        exercise.due_date = due_date or None
        exercise.save()
        
        messages.success(request, f'Assignment dates updated for {exercise.name}!')
        return redirect('exercise_detail', pk=pk)
    
    return render(request, 'exercises/set_exercise_assignment.html', {
        'exercise': exercise,
    })

@login_required
def generate_ai_questions(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    if request.user != exercise.creator:
        return redirect('exercise_detail', pk=pk)
    
    # Restrict to QCM only
    if exercise.exercise_type != 'QCM':
        messages.error(request, 'AI generation is currently only available for QCM exercises.')
        return redirect('exercise_detail', pk=pk)
    
    if request.method == 'POST':
        num_questions = int(request.POST.get('num_questions', 5))
        difficulty = request.POST.get('difficulty', 'medium')
        custom_prompt = request.POST.get('custom_prompt', '').strip()
        
        # Build AI prompt (QCM only)
        base_prompt = (
            f"Generate {num_questions} QCM questions for the topic "
            f"'{exercise.topic.name}' in the subject '{exercise.topic.subject.name}' "
            f"at {difficulty} difficulty level for grade {exercise.topic.grade_level}."
        )
        if custom_prompt:
            base_prompt += f" Additional instructions: {custom_prompt}."
        base_prompt += (
            " Format each question as: Question: [question text], then provide 4 distinct numerical options:"
            " A) [option1] B) [option2] C) [option3] D) [option4]."
            " Ensure the correct option letter you indicate actually equals the true result of the calculation."
            " Finally, specify Answer: [correct option letter]."
        )
        
        # Groq API call
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer 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",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": base_prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            ai_output = response_data['choices'][0]['message']['content']
            print("=== AI RESPONSE DEBUG ===")
            print(f"AI Output: '{ai_output}'")
            print(f"AI Output Length: {len(ai_output)}")
            print("=== END DEBUG ===")
            
            # Parse AI output into QCM questions only
            generated_questions = []
            lines = ai_output.split('\n')
            current_q = None
            options = []

            for line in lines:
                line = line.strip()
                if 'Question:' in line:
                    # Save previous question
                    if current_q:
                        current_q['answers'] = options
                        generated_questions.append(current_q)
                    
                    question_text = line.split('Question:', 1)[1].strip()
                    current_q = {'text': question_text, 'answers': []}
                    options = []
                
                elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                    # Collect options
                    option_text = line[3:].strip()
                    options.append({'text': option_text, 'correct': False})
                
                elif line.startswith('Answer:'):
                    raw = line.replace('Answer:', '').strip()
                    # extract the letter before ')' if present (e.g. "C) 10" → "C")
                    letter = raw.split(')')[0].strip()
                    # fallback if no ')' (e.g. "C")
                    if len(letter) > 1 and letter[1] != '':
                        letter = letter[0]
                    if letter in ['A', 'B', 'C', 'D']:
                        idx = ord(letter) - ord('A')
                        if 0 <= idx < len(options):
                            options[idx]['correct'] = True

            # Don't forget the last question
            if current_q:
                current_q['answers'] = options
                generated_questions.append(current_q)

            print(f"=== PARSING DEBUG ===")
            print(f"Parsed {len(generated_questions)} questions")
            for i, q in enumerate(generated_questions):
                print(f"Q{i+1}: {q['text'][:50]}...")
                print(f"  Options: {len(q['answers'])}")
                for j, a in enumerate(q['answers']):
                    print(f"    {chr(65+j)}) {a['text']} {'✅' if a['correct'] else ''}")
            print(f"=== END PARSING DEBUG ===")
            
            # Store in session for preview
            request.session['generated_questions'] = generated_questions[:num_questions]
            return redirect('preview_ai_questions', pk=pk)
        
        except Exception as e:
            messages.error(request, f'AI generation failed: {str(e)}')
            return redirect('exercise_detail', pk=pk)
    
    return redirect('exercise_detail', pk=pk)


@login_required
def preview_ai_questions(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    generated_questions = request.session.get('generated_questions', [])
    if not generated_questions:
        return redirect('exercise_detail', pk=pk)
    
    if request.method == 'POST':
        # Save questions
        for q_data in generated_questions:
            question = Question.objects.create(
                exercise=exercise,
                question_text=q_data['text'],
                question_type=exercise.exercise_type,
                points=10,
                creator=request.user
            )
            for a_data in q_data['answers']:
                # For dictée, use question_text as answer_text (like manual creation)
                if exercise.exercise_type == 'dictée':
                    answer_text = q_data['text']  # Full question text (instruction)
                else:
                    answer_text = a_data['text']
                
                Answer.objects.create(
                    question=question,
                    answer_text=answer_text,
                    is_correct=a_data['correct']
                )
        del request.session['generated_questions']
        messages.success(request, f'Added {len(generated_questions)} questions!')
        return redirect('exercise_detail', pk=pk)
    
    return render(request, 'exercises/preview_ai_questions.html', {
        'exercise': exercise,
        'generated_questions': generated_questions,
    })