"""
URLs pour l'application assessments
"""
from django.urls import path
from . import views
from . import story_views
from . import story_crud_views
from . import drawing_views

app_name = 'assessments'

urlpatterns = [
    # Simple views for basic functionality
    path('', views.voice_assessment, name='voice_assessment'),
    path('voice/', views.voice_assessment_view, name='voice'),
    path('voice-direct/', views.voice_assessment_direct_view, name='voice_direct'),
    path('voice-audio-only/', views.voice_assessment_audio_only_view, name='voice_audio_only'),
    path('student/exercises/', views.student_exercises, name='student_exercises'),
    path('teacher/exercises/', views.teacher_exercises, name='teacher_exercises'),
    path('teacher/assessments/', views.teacher_assessments, name='teacher_assessments'),
    
    # Advanced voice assessment views
    path('voice-assessment/', views.voice_assessment_view, name='voice_assessment_view'),
    path('voice-assessment/<int:student_id>/', views.voice_assessment_view, name='voice_assessment_student'),
    path('voice-assessment-real/', views.voice_assessment_real_view, name='voice_assessment_real'),
    path('voice-assessment-real/<int:student_id>/', views.voice_assessment_real_view, name='voice_assessment_real_student'),
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
    
    # AI Story Correction
    path('story-correction/', story_views.story_correction, name='story_correction'),
    path('story-correction/submit/', story_views.submit_story_correction, name='submit_story_correction'),
    path('story-correction/view/<int:assessment_id>/', story_views.view_story_assessment, name='view_story_assessment'),
    
    # Story CRUD Management (Teacher/Admin only)
    path('stories/manage/', story_crud_views.story_manage_list, name='story_manage_list'),
    path('stories/manage/create/', story_crud_views.story_create, name='story_create'),
    path('stories/manage/<int:pk>/', story_crud_views.story_manage_detail, name='story_manage_detail'),
    path('stories/manage/<int:pk>/edit/', story_crud_views.story_update, name='story_update'),
    path('stories/manage/<int:pk>/delete/', story_crud_views.story_delete, name='story_delete'),
    path('stories/manage/<int:pk>/duplicate/', story_crud_views.story_duplicate, name='story_duplicate'),
    path('stories/manage/bulk-delete/', story_crud_views.story_bulk_delete, name='story_bulk_delete'),
    
    # Character Drawing
    path('drawing/', drawing_views.drawing_page, name='drawing_page'),
    path('drawing/save/', drawing_views.save_drawing, name='save_drawing'),
    path('drawing/gallery/', drawing_views.gallery_page, name='gallery_page'),
    path('drawing/cartoonify/<int:drawing_id>/', drawing_views.cartoonify_drawing, name='cartoonify_drawing'),
    path('drawing/delete/<int:drawing_id>/', drawing_views.delete_drawing, name='delete_drawing'),
    
    # API
    path('api/voice-assessment/analyze/', views.voice_assessment_analyze, name='voice_analyze_api'),
    path('api/voice-assessment-audio-analyze/', views.voice_assessment_audio_analyze, name='voice_audio_analyze_api'),
    path('api/voice-transcription/', views.voice_transcription_api, name='voice_transcription_api'),
]

