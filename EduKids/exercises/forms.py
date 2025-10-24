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
        fields = ['question_text', 'question_type', 'points', 'hint']
        widgets = {
            'question_text': forms.Textarea(attrs={
                'class': 'form-control form-control-lg rounded-3 px-4 py-3',
                'rows': 5,
                'placeholder': 'Texte de dictée...',
                'style': 'border: 2px solid #e2e8f0; resize: vertical;'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg rounded-pill px-4',
                'style': 'border: 2px solid #e2e8f0;'
            }),
            'hint': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control form-control-lg rounded-3 px-4 py-3',
                'style': 'border: 2px solid #e2e8f0; resize: vertical;',
                'placeholder': 'Indice optionnel...'
            }),
        }

class QuestionWithAnswersForm(forms.Form):
    question_text = forms.CharField(
        label="Question Text",
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-lg rounded-3 px-4 py-3',
            'rows': 3,
            'placeholder': 'Énoncez votre question...',
            'style': 'border: 2px solid #e2e8f0; resize: vertical;'
        }),
        required=False,
        help_text="For dictée: Enter the text to be read aloud."
    )
    question_type = forms.ChoiceField(choices=Question.QUESTION_TYPE_CHOICES, initial='text')
    points = forms.IntegerField(
        initial=1, 
        min_value=1,
        widget=forms.NumberInput(attrs={  # ADDED: Custom attrs for styling
            'class': 'form-control form-control-lg rounded-pill px-4',
            'style': 'border: 2px solid #e2e8f0;'
        })
    )
    hint = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={  # ADDED: Custom attrs for styling (kept as Textarea for multi-line)
            'rows': 2,
            'class': 'form-control form-control-lg rounded-3 px-4 py-3',
            'style': 'border: 2px solid #e2e8f0; resize: vertical;',
            'placeholder': 'Indice optionnel...'
        })
    )

class AnswerForm(forms.Form):
    answer_text = forms.CharField(label="Answer Text", required=False)  # Not required
    is_correct = forms.BooleanField(required=False, label="Correct?")
    explanation = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))

AnswerFormSet = formset_factory(AnswerForm, extra=1, can_delete=True)