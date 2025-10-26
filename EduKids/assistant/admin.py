from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizOption, MediaFile


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'topic', 'conversation', 'created_at')
	search_fields = ('title', 'topic')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
	list_display = ('id', 'quiz', 'order', 'text')
	search_fields = ('text',)


@admin.register(QuizOption)
class QuizOptionAdmin(admin.ModelAdmin):
	list_display = ('id', 'question', 'index', 'text')
	search_fields = ('text',)


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
	list_display = ('id', 'media_type', 'conversation', 'caption', 'created_at')
	list_filter = ('media_type',)
	search_fields = ('caption',)
