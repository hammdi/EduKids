"""
URLs pour l'application assessments
"""
from django.urls import path
from . import views
from . import story_views

app_name = 'assessments'

urlpatterns = [
    # Simple views for basic functionality
    path('', views.voice_assessment, name='voice_assessment'),
    path('student/exercises/', views.student_exercises, name='student_exercises'),
    path('teacher/exercises/', views.teacher_exercises, name='teacher_exercises'),
    path('teacher/assessments/', views.teacher_assessments, name='teacher_assessments'),
    
    # Advanced voice assessment views
    path('voice-assessment/', views.voice_assessment_view, name='voice_assessment_view'),
    path('voice-assessment/<int:student_id>/', views.voice_assessment_view, name='voice_assessment_student'),
    path('voice-assessment/results/<int:assessment_id>/', views.voice_assessment_results, name='voice_results'),
    path('voice-assessment/history/', views.voice_assessment_history, name='voice_history'),
    path('voice-assessment/history/<int:student_id>/', views.voice_assessment_history, name='voice_history_student'),
    
    # Story Generation & Reading
    path('stories/', story_views.story_list, name='story_list'),
    path('stories/generate/', story_views.generate_story, name='generate_story'),
    path('stories/<int:story_id>/', story_views.story_detail, name='story_detail'),
    path('stories/<int:story_id>/submit/', story_views.submit_answers, name='submit_answers'),
    path('stories/<int:story_id>/results/', story_views.story_results, name='story_results'),
    path('badges/', story_views.student_badges, name='student_badges'),
    
    # API
    path('api/voice-assessment/analyze/', views.voice_assessment_analyze, name='voice_analyze_api'),
]

