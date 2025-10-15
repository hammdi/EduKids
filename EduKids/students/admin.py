from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Teacher, Parent, Classroom

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade_level', 'learning_style', 'progress_score')
    list_filter = ('grade_level', 'learning_style')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject_specialties_display', 'teaching_experience', 'certification_level')
    list_filter = ('certification_level', 'teaching_experience')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def subject_specialties_display(self, obj):
        return ', '.join(obj.subject_specialties)
    subject_specialties_display.short_description = 'Subject Specialties'

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'children_count')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    
    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = 'Number of Children'

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'student_count')
    list_filter = ('grade_level',)
    search_fields = ('name',)
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Number of Students'
