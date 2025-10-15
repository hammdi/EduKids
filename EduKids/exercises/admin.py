from django.contrib import admin
from .models import Subject, Topic, Exercise, Question, Answer

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    list_filter = ('subject',)
    search_fields = ('name', 'description')

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty_level', 'exercise_type', 'created_by')
    list_filter = ('difficulty_level', 'exercise_type', 'created_by')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'exercise', 'question_type', 'points')
    list_filter = ('question_type', 'exercise', 'points')
    search_fields = ('question_text',)

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__exercise')
    search_fields = ('answer_text',)
