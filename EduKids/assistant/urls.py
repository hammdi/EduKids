from django.urls import path
from . import views, api_views

app_name = 'assistant'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('api/history/', api_views.history_view, name='history'),
    path('api/send_message/', api_views.send_message, name='send_message'),
    path('api/conversation/<int:conversation_id>/', api_views.conversation_detail, name='conversation_detail'),
    path('api/search/', api_views.search_conversations, name='search_conversations'),
    path('api/conversation/<int:conversation_id>/delete/', api_views.delete_conversation, name='delete_conversation'),
    path('api/message/<int:message_id>/edit/', api_views.edit_message, name='edit_message'),
    path('api/message/<int:message_id>/delete/', api_views.delete_message, name='delete_message'),
    path('api/bulk_delete/', api_views.bulk_delete_old_conversations, name='bulk_delete_old_conversations'),
    path('api/generate_quiz/', api_views.generate_quiz, name='generate_quiz'),
    path('api/grade_quiz/', api_views.grade_quiz, name='grade_quiz'),
    path('api/generate_image/', api_views.generate_image, name='generate_image'),
    path('api/generate_pdf/', api_views.generate_pdf, name='generate_pdf'),
    path('api/pdf_history/', api_views.pdf_history, name='pdf_history'),
    path('api/media_gallery/', api_views.media_gallery, name='media_gallery'),
]


