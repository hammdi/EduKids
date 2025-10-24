from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from students.decorators import teacher_required, student_required
from .models import Exercise, Question, Answer, Topic


@teacher_required
def teacher_exercise_list(request):
    exercises = Exercise.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "exercises/teacher_list.html", {"exercises": exercises})


@teacher_required
def teacher_exercise_create(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "")
        topic_id = request.POST.get("topic")
        exercise_type = request.POST.get("exercise_type")
        difficulty_level = int(request.POST.get("difficulty_level", 3))
        estimated_time = int(request.POST.get("estimated_time", 10))
        points = int(request.POST.get("points", 10))
        instructions = request.POST.get("instructions", "")

        if not title or not topic_id or not exercise_type:
            messages.error(request, "Title, Topic and Type are required.")
        else:
            topic = get_object_or_404(Topic, id=topic_id)
            Exercise.objects.create(
                title=title,
                description=description,
                topic=topic,
                exercise_type=exercise_type,
                difficulty_level=difficulty_level,
                estimated_time=estimated_time,
                points=points,
                instructions=instructions,
                created_by=request.user,
                is_published=True,
            )
            messages.success(request, "Exercise created successfully.")
            return redirect("teacher_exercises")

    topics = Topic.objects.all().order_by("subject__name", "name")
    return render(request, "exercises/teacher_create.html", {"topics": topics})


@teacher_required
def teacher_exercise_edit(request, exercise_id: int):
    exercise = get_object_or_404(Exercise, id=exercise_id, created_by=request.user)

    if request.method == "POST":
        exercise.title = request.POST.get("title", exercise.title)
        exercise.description = request.POST.get("description", exercise.description)
        topic_id = request.POST.get("topic")
        if topic_id:
            exercise.topic = get_object_or_404(Topic, id=topic_id)
        exercise.exercise_type = request.POST.get("exercise_type", exercise.exercise_type)
        exercise.difficulty_level = int(request.POST.get("difficulty_level", exercise.difficulty_level))
        exercise.estimated_time = int(request.POST.get("estimated_time", exercise.estimated_time))
        exercise.points = int(request.POST.get("points", exercise.points))
        exercise.instructions = request.POST.get("instructions", exercise.instructions)
        exercise.save()
        messages.success(request, "Exercise updated.")
        return redirect("teacher_exercises")

    topics = Topic.objects.all().order_by("subject__name", "name")
    return render(request, "exercises/teacher_edit.html", {"exercise": exercise, "topics": topics})


@teacher_required
@require_http_methods(["POST"])
def teacher_exercise_delete(request, exercise_id: int):
    exercise = get_object_or_404(Exercise, id=exercise_id, created_by=request.user)
    exercise.delete()
    messages.success(request, "Exercise deleted.")
    return redirect("teacher_exercises")


@student_required
def student_exercise_list(request):
    exercises = Exercise.objects.filter(is_published=True).order_by("-created_at")[:100]
    return render(request, "exercises/student_list.html", {"exercises": exercises})


@student_required
def student_exercise_take(request, exercise_id: int):
    exercise = get_object_or_404(Exercise, id=exercise_id, is_published=True)

    if request.method == "POST":
        # For now, just acknowledge submission
        messages.success(request, "Your responses were submitted. Feedback coming soon!")
        return redirect("student_exercises")

    return render(request, "exercises/student_take.html", {"exercise": exercise})
