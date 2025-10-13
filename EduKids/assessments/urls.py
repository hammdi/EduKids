"""
URLs pour l'application assessments
"""
from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Évaluation vocale
    path('voice-assessment/', views.voice_assessment_view, name='voice_assessment'),
    path('voice-assessment/<int:student_id>/', views.voice_assessment_view, name='voice_assessment_student'),
    path('voice-assessment/results/<int:assessment_id>/', views.voice_assessment_results, name='voice_results'),
    path('voice-assessment/history/', views.voice_assessment_history, name='voice_history'),
    path('voice-assessment/history/<int:student_id>/', views.voice_assessment_history, name='voice_history_student'),
    
    # API
    path('api/voice-assessment/analyze/', views.voice_assessment_analyze, name='voice_analyze_api'),
]

