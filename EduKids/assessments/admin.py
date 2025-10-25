from django.contrib import admin
from .models import (
    Assessment, StudentResponse, Progress, 
    Report, Recommendation,
    VoiceAssessment, VoiceAssessmentCriteria,
    Story, StoryProgress, Badge, StudentBadge
)
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'exercise', 'score', 'time_taken', 'completed_at')
    list_filter = ('exercise', 'completed_at', 'score')
    search_fields = ('student__user__username', 'exercise__title')
    date_hierarchy = 'completed_at'

@admin.register(StudentResponse)
class StudentResponseAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'question', 'answer_text', 'is_correct', 'time_taken')
    list_filter = ('is_correct', 'question__question_type')
    search_fields = ('answer_text',)

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'skill_level', 'improvement_rate')
    list_filter = ('subject', 'skill_level')
    search_fields = ('student__user__username',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'generated_by')
    list_filter = ('report_type', 'generated_by')
    search_fields = ('title', 'description')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'recommendation_type', 'priority', 'created_at')
    list_filter = ('recommendation_type', 'priority', 'created_at')
    search_fields = ('title', 'description')

@admin.register(VoiceAssessment)
class VoiceAssessmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'overall_score', 'created_at')
    list_filter = ('created_at', 'overall_score')
    search_fields = ('student__user__username', 'transcription')
    date_hierarchy = 'created_at'

@admin.register(VoiceAssessmentCriteria)
class VoiceAssessmentCriteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weight')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'age_group', 'difficulty_level', 'created_at')
    list_filter = ('theme', 'age_group', 'difficulty_level', 'generated_by_ai')
    search_fields = ('title',)
    date_hierarchy = 'created_at'

@admin.register(StoryProgress)
class StoryProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'story', 'score', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'score')
    search_fields = ('student__user__username', 'story__title')
    date_hierarchy = 'started_at'

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_type', 'icon', 'color')
    list_filter = ('badge_type',)
    search_fields = ('name', 'description')

@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_at')
    list_filter = ('badge', 'earned_at')
    search_fields = ('student__user__username', 'badge__name')
    date_hierarchy = 'earned_at'
