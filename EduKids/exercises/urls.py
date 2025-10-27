# filepath: c:\Users\ahmed\Desktop\django\EduKids\EduKids\exercises\urls.py
from django.urls import path
from . import views

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
    path('delete_subject/<int:pk>/', views.delete_subject, name='delete_subject'),
    # Teacher Class Management - REMOVED all assignment/classroom-related URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    # path('classes/', views.teacher_classes_list, name='teacher_classes_list'),  # REMOVED
    # path('teacher/classes/', views.teacher_classes_list, name='teacher_classes_list_alt'),  # REMOVED
    # path('classes/create/', views.create_classroom, name='create_classroom'),  # REMOVED
    # path('teacher/classes/create/', views.create_classroom, name='create_classroom_alt'),  # REMOVED
    # path('classes/<int:pk>/', views.classroom_detail, name='classroom_detail'),  # REMOVED
    # path('teacher/classes/<int:pk>/', views.classroom_detail, name='classroom_detail_alt'),  # REMOVED
    # path('classes/<int:classroom_pk>/add-student/', views.add_student_to_class, name='add_student_to_class'),  # REMOVED
    # path('teacher/classes/<int:classroom_pk>/add-student/', views.add_student_to_class, name='add_student_to_class_alt'),  # REMOVED
    # path('classes/<int:classroom_pk>/create-assignment/', views.create_assignment, name='create_assignment'),  # REMOVED
    # path('assignments/<int:assignment_pk>/add-questions/', views.assignment_add_questions, name='assignment_add_questions'),  # REMOVED
    # path('teacher/assignments/', views.teacher_assignments_list, name='teacher_assignments_list'),  # REMOVED
    path('subjects/<int:subject_pk>/invite-student/', views.invite_student_to_subject, name='invite_student_to_subject'),
    path('exercises/<int:pk>/generate-ai/', views.generate_ai_questions, name='generate_ai_questions'),
    path('exercises/<int:pk>/preview-ai/', views.preview_ai_questions, name='preview_ai_questions'),
]