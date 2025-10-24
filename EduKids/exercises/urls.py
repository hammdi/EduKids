from django.urls import path
from . import views

app_name = "exercises"

urlpatterns = [
    # Teacher
    path("teacher/", views.teacher_exercise_list, name="teacher_exercises"),
    path("teacher/create/", views.teacher_exercise_create, name="teacher_exercise_create"),
    path("teacher/<int:exercise_id>/edit/", views.teacher_exercise_edit, name="teacher_exercise_edit"),
    path("teacher/<int:exercise_id>/delete/", views.teacher_exercise_delete, name="teacher_exercise_delete"),

    # Student
    path("student/", views.student_exercise_list, name="student_exercises"),
    path("student/<int:exercise_id>/take/", views.student_exercise_take, name="student_exercise_take"),
]



