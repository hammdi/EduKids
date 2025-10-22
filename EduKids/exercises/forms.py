from django import forms
from django.forms import formset_factory
from .models import Subject, Topic, Exercise, Lesson, Question, Answer

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description', 'icon', 'color', 'order', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description', 'grade_level', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['name', 'description', 'exercise_type', 'points', 'available_from', 'due_date']
        widgets = {
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'media', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'points', 'hint']  # Changed 'hints' to 'hint'

class QuestionWithAnswersForm(forms.Form):
    question_text = forms.CharField(
        label="Question Text",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="For dictée: Enter the text to be read aloud."
    )
    question_type = forms.ChoiceField(choices=Question.QUESTION_TYPE_CHOICES, initial='text')
    points = forms.IntegerField(initial=1, min_value=1)
    hint = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

class AnswerForm(forms.Form):
    answer_text = forms.CharField(label="Answer Text", required=False)  # Not required
    is_correct = forms.BooleanField(required=False, label="Correct?")
    explanation = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

AnswerFormSet = formset_factory(AnswerForm, extra=1, can_delete=True)