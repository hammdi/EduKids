from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Subject, Topic, Exercise, Lesson, Question, Answer
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
            question_form = QuestionWithAnswersForm(request.POST)
            print("question_form valid:", question_form.is_valid())  # Debug
            if not question_form.is_valid():
                print("question_form errors:", question_form.errors)  # Debug
            answer_formset = AnswerFormSet(request.POST)
            print("answer_formset valid:", answer_formset.is_valid())  # Debug
            if not answer_formset.is_valid():
                print("answer_formset errors:", answer_formset.errors)  # Debug
            print("POST data:", request.POST)  # Debug
            if question_form.is_valid() and answer_formset.is_valid():
                if question_form.cleaned_data['question_text']:  # Check if question_text exists
                    print("Creating question")  # Debug
                    question = Question.objects.create(
                        exercise=exercise,
                        question_text=question_form.cleaned_data['question_text'],
                        question_type=question_form.cleaned_data['question_type'],
                        points=question_form.cleaned_data['points'],
                        hint=question_form.cleaned_data.get('hint')
                    )
                    for form in answer_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data.get('answer_text'):  # Check if answer_text exists
                            print("Creating answer:", form.cleaned_data['answer_text'])  # Debug
                            Answer.objects.create(
                                question=question,
                                answer_text=form.cleaned_data['answer_text'],
                                is_correct=form.cleaned_data['is_correct'],
                                explanation=form.cleaned_data.get('explanation')
                            )
                    messages.success(request, 'Question and answers added!')
                    return redirect('exercise_detail', pk=exercise.pk)
                else:
                    messages.error(request, 'Question text is required.')
        elif 'add_answer' in request.POST:
            answer_form = AnswerForm(request.POST)
            if answer_form.is_valid():
                Answer.objects.create(
                    question=get_object_or_404(Question, pk=request.POST.get('question_id')),
                    answer_text=answer_form.cleaned_data['answer_text'],
                    is_correct=answer_form.cleaned_data['is_correct'],
                    explanation=answer_form.cleaned_data.get('explanation')
                )
                messages.success(request, 'Answer added successfully!')
                return redirect('exercise_detail', pk=exercise.pk)
    return render(request, 'exercises/exercise_detail.html', {
        'exercise': exercise,
        'questions': questions,
        'question_form': question_form,
        'answer_formset': answer_formset,
        'answer_form': answer_form,
    })
