from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Student, Teacher

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    birth_date = forms.DateField(
        required=True,
        help_text="Enter your birth date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    # Student type selection
    STUDENT_TYPE_CHOICES = (
        ('self_learning', 'Auto-apprentissage (étudiant indépendant)'),
        ('classroom', 'Étudiant lié à une classe d\'enseignant'),
        ('parent_monitored', 'Étudiant surveillé par un parent'),
    )
    
    student_type = forms.ChoiceField(
        choices=STUDENT_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect,
        help_text="Choisissez votre type d'inscription"
    )
    
    # Conditional fields
    teacher_invitation_code = forms.CharField(
        max_length=50,
        required=False,
        help_text="Code d'invitation de l'enseignant (si lié à une classe)",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: 211JMT6535'})
    )
    parent_email = forms.EmailField(
        required=False,
        help_text="Email du parent (si surveillé par un parent)",
        widget=forms.EmailInput(attrs={'placeholder': 'parent@example.com'})
    )
    
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
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'birth_date', 'student_type', 'teacher_invitation_code', 'parent_email', 'grade_level', 'learning_style')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = 'student'
        
        # Generate username based on student type
        student_type = self.cleaned_data['student_type']
        invitation_code = self.cleaned_data.get('teacher_invitation_code', '').strip()
        
        if student_type == 'classroom' and invitation_code:
            # For classroom students, use invitation code as username
            user.username = User.generate_username('student', school_id=invitation_code)
            user.auto_generated_username = True
        else:
            # For self-learning and parent-monitored students, generate unique username
            user.username = User.generate_username('student')
            user.auto_generated_username = True
        
        if commit:
            user.save()
            # Create student profile with conditional fields
            student_data = {
                'user': user,
                'birth_date': self.cleaned_data['birth_date'],
                'grade_level': self.cleaned_data['grade_level'],
                'learning_style': self.cleaned_data['learning_style'],
                'auto_generated_username': user.auto_generated_username,
            }
            
            # Add conditional fields based on student type
            if student_type == 'classroom' and invitation_code:
                student_data['school_id'] = invitation_code
            elif student_type == 'parent_monitored':
                parent_email = self.cleaned_data.get('parent_email', '').strip()
                if parent_email:
                    student_data['parent_email'] = parent_email
            
            Student.objects.create(**student_data)
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
