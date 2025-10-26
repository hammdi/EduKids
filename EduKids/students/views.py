from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
import uuid
from .models import Student, Teacher, Parent, User
from .forms import StudentRegistrationForm, TeacherRegistrationForm

def send_verification_email(user):
    """Send email verification to user"""
    # Always generate and save token first
    token = uuid.uuid4()
    user.email_verification_token = token
    user.save()
    
    print(f"🎫 Token generated and saved: {token}")
    
    try:
        # Create verification URL
        verification_url = f"{settings.SITE_URL}/verify-email/{token}/"
        
        subject = "🎓 Verify Your EduKids Account"
        message = f"""
        Hi {user.first_name}!
        
        Welcome to EduKids! 🎉
        
        Please click the link below to verify your email address and activate your account:
        
        {verification_url}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        The EduKids Team
        """
        
        # Send email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        print(f"✅ Verification email sent to {user.email}")
        print(f"🔗 Verification URL: {verification_url}")
        
    except Exception as e:
        print(f"❌ Error sending verification email: {e}")
        print(f"🎫 But token is saved: {token}")

def verify_email(request, token):
    """Verify user email with token"""
    try:
        user = User.objects.get(email_verification_token=token)
        user.email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.save()
        
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('login')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('login')

def home(request):
    """Home page view"""
    return render(request, 'base/home.html')

def custom_login(request):
    """Custom login view that accepts both username and email"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)
        
        # If that fails, try to find user by email and authenticate with username
        if user is None:
            try:
                user_by_email = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            if user.is_active and user.email_verified:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect based on user type
                if user.user_type == 'student':
                    return redirect('student_dashboard')
                elif user.user_type == 'teacher':
                    return redirect('teacher_dashboard')
                elif user.user_type == 'admin':
                    return redirect('/admin/')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Your account is not active or email not verified. Please check your email.')
        else:
            messages.error(request, 'Invalid username/email or password.')
    
    # Create form for GET request
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def register(request):
    """Simplified registration view"""
    user_type = request.GET.get('type', 'student')  # Default to student
    
    if request.method == 'POST':
        # Create a simple form for basic registration
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Basic validation
        if not all([username, first_name, last_name, email, password1, password2]):
            messages.error(request, 'All fields are required.')
            return render(request, 'registration/register.html', {
                'user_type': user_type,
                'form': None
            })
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html', {
                'user_type': user_type,
                'form': None
            })
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'registration/register.html', {
                'user_type': user_type,
                'form': None
            })
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'registration/register.html', {
                'user_type': user_type,
                'form': None
            })
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                email_verified=False,  # Enable email verification
                is_active=False  # User must verify email first
            )
            
            # Create profile based on user type
            if user_type == 'student':
                Student.objects.create(
                    user=user,
                    birth_date='2000-01-01',  # Default birth date
                    grade_level='middle_school',
                    learning_style='visual'
                )
            elif user_type == 'teacher':
                Teacher.objects.create(
                    user=user,
                    subject_specialties=['General'],
                    teaching_experience=0,
                    certification_level='bachelor'
                )
            
            # Send verification email
            send_verification_email(user)
            
            messages.success(request, f'{user_type.title()} account created successfully! Please check your email to verify your account.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'registration/register.html', {
                'user_type': user_type,
                'form': None
            })
    
    return render(request, 'registration/register.html', {
        'user_type': user_type,
        'form': None
    })

@login_required
def student_dashboard(request):
    """Student dashboard view"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('home')
    
    context = {
        'student': student,
    }
    return render(request, 'students/dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    try:
        teacher = request.user.teacher_profile
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found.')
        return redirect('home')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'teachers/dashboard.html', context)

@login_required
def profile(request):
    """User profile view and edit"""
    user = request.user
    
    # Try to get user's profile
    student_profile = None
    teacher_profile = None
    
    try:
        student_profile = user.student_profile
    except Student.DoesNotExist:
        pass
    
    try:
        teacher_profile = user.teacher_profile
    except Teacher.DoesNotExist:
        pass
    
    context = {
        'user': user,
        'student_profile': student_profile,
        'teacher_profile': teacher_profile,
    }
    return render(request, 'base/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return redirect('profile')

@staff_member_required
def user_management(request):
    """Admin user management view"""
    users = User.objects.all().order_by('-date_joined')
    students = Student.objects.all()
    teachers = Teacher.objects.all()
    
    context = {
        'users': users,
        'students': students,
        'teachers': teachers,
    }
    return render(request, 'admin/user_management.html', context)

@staff_member_required
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(User, id=user_id)
    
    context = {
        'user_obj': user,  # Using user_obj to avoid conflict with request.user
    }
    return render(request, 'admin/user_detail.html', context)

@staff_member_required
def user_edit(request, user_id):
    """Edit user details"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('user_detail', user_id=user.id)
    
    context = {
        'user_obj': user,
    }
    return render(request, 'admin/user_edit.html', context)

@staff_member_required
def user_delete(request, user_id):
    """Delete user"""
    user = get_object_or_404(User, id=user_id)
    username = user.username
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('user_management')
    
    context = {
        'user_obj': user,
    }
    return render(request, 'admin/user_delete.html', context)


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.email_verified:
                # Generate new token
                user.email_verification_token = uuid.uuid4()
                user.save()
                
                # Send email
                send_verification_email(user)
                messages.success(request, 'Verification email sent! Please check your inbox.')
            else:
                messages.info(request, 'This email is already verified.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'registration/resend_verification.html')
