from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json

from .models import Subject, Topic, Exercise, Lesson, Question, Answer, ExerciseResult, StudentAnswer
from .forms import SubjectForm, TopicForm, ExerciseForm, LessonForm, QuestionForm, AnswerForm, QuestionWithAnswersForm, AnswerFormSet

def subjects_list(request):
    subjects = Subject.objects.filter(is_active=True)
    subject_form = SubjectForm()
    if request.method == 'POST':
        if 'add_subject' in request.POST:
            subject_form = SubjectForm(request.POST, request.FILES)
            if subject_form.is_valid():
                subject_form.save()
                messages.success(request, 'Subject created successfully!')
                return redirect('subjects_list')
    return render(request, 'exercises/subjects_list.html', {
        'subjects': subjects,
        'subject_form': subject_form,
    })

def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk, is_active=True)
    topics = subject.topics.filter(is_active=True)
    topic_form = TopicForm()
    if request.method == 'POST':
        if 'add_topic' in request.POST:
            topic_form = TopicForm(request.POST)
            if topic_form.is_valid():
                topic = topic_form.save(commit=False)
                topic.subject = subject
                topic.save()
                messages.success(request, 'Topic created successfully!')
                return redirect('subject_detail', pk=subject.pk)
    return render(request, 'exercises/subject_detail.html', {
        'subject': subject,
        'topics': topics,
        'topic_form': topic_form,
    })

def topic_detail(request, pk):
    topic = get_object_or_404(Topic, pk=pk, is_active=True)
    exercises = topic.exercises.filter(is_active=True)
    lessons = topic.lessons.filter(is_active=True)
    exercise_form = ExerciseForm()
    lesson_form = LessonForm()
    if request.method == 'POST':
        if 'add_exercise' in request.POST:
            exercise_form = ExerciseForm(request.POST)
            if exercise_form.is_valid():
                exercise = exercise_form.save(commit=False)
                exercise.topic = topic
                exercise.creator = request.user
                exercise.save()
                messages.success(request, 'Exercise created successfully!')
                return redirect('topic_detail', pk=topic.pk)
        elif 'add_lesson' in request.POST:
            lesson_form = LessonForm(request.POST, request.FILES)
            if lesson_form.is_valid():
                lesson = lesson_form.save(commit=False)
                lesson.topic = topic
                lesson.save()
                messages.success(request, 'Lesson created successfully!')
                return redirect('topic_detail', pk=topic.pk)
    return render(request, 'exercises/topic_detail.html', {
        'topic': topic,
        'exercises': exercises,
        'lessons': lessons,
        'exercise_form': exercise_form,
        'lesson_form': lesson_form,
    })

def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    questions = exercise.questions.all()
    question_form = QuestionWithAnswersForm()
    answer_formset = AnswerFormSet()
    answer_form = AnswerForm()
    
    if request.method == 'POST':
        if 'add_question' in request.POST:
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
                                print("Creating answer:", form.cleaned_data['answer_text'])  # Debug
                                Answer.objects.create(
                                    question=question,
                                    answer_text=form.cleaned_data['answer_text'],
                                    is_correct=form.cleaned_data['is_correct'],
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
def student_subjects_list(request):
    """View for students to see subjects based on their grade level"""
    try:
        student = request.user.student_profile  # Assuming this relationship exists
        student_grade = student.grade_level
        
        # Get subjects that have topics for the student's grade level
        subjects_with_topics = Subject.objects.filter(
            is_active=True,
            topics__grade_level=student_grade,
            topics__is_active=True
        ).distinct()
        
        # Add topic count for each subject
        for subject in subjects_with_topics:
            subject.topic_count = subject.topics.filter(
                grade_level=student_grade, 
                is_active=True
            ).count()
            
    except AttributeError:
        # If user doesn't have a student profile, show all subjects
        subjects_with_topics = Subject.objects.filter(is_active=True)
        student_grade = None
        for subject in subjects_with_topics:
            subject.topic_count = subject.topics.filter(is_active=True).count()
    
    return render(request, 'exercises/student_subjects_list.html', {
        'subjects': subjects_with_topics,
        'student_grade': student_grade,
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
    
    return render(request, 'exercises/student_subject_detail.html', {
        'subject': subject,
        'topics': topics,
        'student_grade': student_grade,
    })

@login_required 
def student_topic_detail(request, pk):
    """Student view for a specific topic showing lessons and exercises"""
    topic = get_object_or_404(Topic, pk=pk, is_active=True)
    lessons = topic.lessons.filter(is_active=True).order_by('order', 'created_at')
    exercises = topic.exercises.filter(is_active=True).order_by('name')
    
    # Add exercise results for each exercise - IMPROVED
    for exercise in exercises:
        try:
            latest_result = ExerciseResult.objects.filter(
                student=request.user,
                exercise=exercise
            ).select_related('exercise').first()
            
            # Ensure the result has all required fields
            if latest_result:
                # Verify the result is complete
                if latest_result.score is not None and latest_result.earned_points is not None:
                    exercise.latest_result = latest_result
                else:
                    print(f"Warning: Incomplete result for exercise {exercise.pk}")
                    exercise.latest_result = None
            else:
                exercise.latest_result = None
                
        except Exception as e:
            print(f"Error loading result for exercise {exercise.pk}: {e}")
            exercise.latest_result = None
    
    return render(request, 'exercises/student_topic_detail.html', {
        'topic': topic,
        'lessons': lessons,
        'exercises': exercises,
    })

@login_required
def student_exercise_start(request, pk):
    """Student starts an exercise"""
    exercise = get_object_or_404(Exercise, pk=pk, is_active=True)
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
