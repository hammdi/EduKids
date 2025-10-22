from django import forms
from django.forms import inlineformset_factory
from .models import Assignment, AssignmentQuestion, AssignmentAnswer


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'assignment_type', 'difficulty', 'points', 'time_limit', 'instructions', 'due_date', 'is_required']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Devoir de dictée - Les animaux'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du devoir...'}),
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Instructions pour les étudiants...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AssignmentQuestionForm(forms.ModelForm):
    class Meta:
        model = AssignmentQuestion
        fields = ['question_text', 'points', 'hint', 'image']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'hint': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AssignmentAnswerForm(forms.ModelForm):
    class Meta:
        model = AssignmentAnswer
        fields = ['answer_text', 'is_correct', 'explanation']
        widgets = {
            'answer_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Entrez la réponse...'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explication optionnelle...'}),
        }


# FIXED Formset - Removed strict validation that was causing issues
AssignmentAnswerFormSet = inlineformset_factory(
    AssignmentQuestion, 
    AssignmentAnswer, 
    form=AssignmentAnswerForm,
    extra=4,  # Number of empty forms
    can_delete=True,
    min_num=0,  # Changed from 1 to 0 - allow no answers initially
    validate_min=False,  # Changed to False - don't enforce minimum
    max_num=10,  # Add maximum limit
)