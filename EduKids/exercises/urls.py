from django.urls import path
from . import views

app_name = "exercises"

urlpatterns = [
    # Teacher/Admin views
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('exercises/<int:pk>/', views.exercise_detail, name='exercise_detail'),
    path('lessons/<int:pk>/delete/', views.delete_lesson, name='delete_lesson'),
    path('exercises/<int:pk>/delete/', views.delete_exercise, name='delete_exercise'),
    path('questions/<int:pk>/delete/', views.delete_question, name='delete_question'),
    
    # Student views
    path('student/subjects/', views.student_subjects_list, name='student_subjects_list'),
    path('student/subjects/<int:pk>/', views.student_subject_detail, name='student_subject_detail'),
    path('student/topics/<int:pk>/', views.student_topic_detail, name='student_topic_detail'),
    path('student/exercises/<int:pk>/start/', views.student_exercise_start, name='student_exercise_start'),
    path('student/exercises/<int:pk>/submit/', views.submit_exercise, name='submit_exercise'),
    
    # Teacher Class Management
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('subjects/<int:subject_pk>/invite-student/', views.invite_student_to_subject, name='invite_student_to_subject'),
    path('exercises/<int:pk>/generate-ai/', views.generate_ai_questions, name='generate_ai_questions'),
    path('exercises/<int:pk>/preview-ai/', views.preview_ai_questions, name='preview_ai_questions'),
    
    # Legacy URLs (for backward compatibility)
    path("teacher/", views.teacher_exercise_list, name="teacher_exercises"),
    path("teacher/create/", views.teacher_exercise_create, name="teacher_exercise_create"),
    path("teacher/<int:exercise_id>/edit/", views.teacher_exercise_edit, name="teacher_exercise_edit"),
    path("teacher/<int:exercise_id>/delete/", views.teacher_exercise_delete, name="teacher_exercise_delete"),
    path("student/", views.student_exercise_list, name="student_exercises"),
    path("student/<int:exercise_id>/take/", views.student_exercise_take, name="student_exercise_take"),
]
