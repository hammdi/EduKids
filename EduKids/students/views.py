from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Student, Teacher, Parent, User
from .forms import StudentRegistrationForm, TeacherRegistrationForm

def home(request):
    """Home page view"""
    return render(request, 'base/home.html')

def logout_view(request):
    """Custom logout view that handles GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def register(request):
    """Registration view with role selection"""
    user_type = request.GET.get('type', 'student')  # Default to student
    
    if request.method == 'POST':
        if user_type == 'teacher':
            form = TeacherRegistrationForm(request.POST)
        else:
            form = StudentRegistrationForm(request.POST)
            
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'{user_type.title()} account created successfully!')
            
            # Redirect based on user type
            if user_type == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        if user_type == 'teacher':
            form = TeacherRegistrationForm()
        else:
            form = StudentRegistrationForm()
    
    return render(request, 'registration/register.html', {
        'form': form, 
        'user_type': user_type
    })

@login_required
def student_dashboard(request):
    """Student dashboard view"""
    try:
        student = request.user.student
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
        teacher = request.user.teacher
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
