from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Student, Teacher

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    grade_level = forms.ChoiceField(
        choices=Student.GRADE_LEVEL_CHOICES,
        required=True,
        help_text="Select your current grade level"
    )
    learning_style = forms.ChoiceField(
        choices=Student.LEARNING_STYLE_CHOICES,
        required=True,
        help_text="How do you learn best?"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'grade_level', 'learning_style')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create student profile
            Student.objects.create(
                user=user,
                grade_level=self.cleaned_data['grade_level'],
                learning_style=self.cleaned_data['learning_style']
            )
        return user

class TeacherRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    subject_specialties = forms.CharField(
        max_length=500,
        required=True,
        help_text="List your subject specialties (comma-separated)"
    )
    teaching_experience = forms.IntegerField(
        min_value=0,
        required=True,
        help_text="Years of teaching experience"
    )
    certification_level = forms.ChoiceField(
        choices=Teacher.CERTIFICATION_LEVEL_CHOICES,
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'subject_specialties', 'teaching_experience', 'certification_level')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Create teacher profile
            Teacher.objects.create(
                user=user,
                subject_specialties=self.cleaned_data['subject_specialties'].split(','),
                teaching_experience=self.cleaned_data['teaching_experience'],
                certification_level=self.cleaned_data['certification_level']
            )
        return user
