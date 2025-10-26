"""
Story Generation Views - EduKids
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .story_models import Story, StoryProgress, Badge, StudentBadge, StoryAssessment
from .story_service import StoryGeneratorService
import json


@login_required
def story_list(request):
    """Display list of available stories"""
    stories = Story.objects.all().order_by('-created_at')
    
    # Get student's progress if student
    progress_data = {}
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        progress = StoryProgress.objects.filter(student=student)
        progress_data = {p.story_id: p for p in progress}
        
        # Get earned badges
        earned_badges = StudentBadge.objects.filter(student=student).select_related('badge')
    else:
        earned_badges = []
    
    context = {
        'stories': stories,
        'progress_data': progress_data,
        'earned_badges': earned_badges,
    }
    
    return render(request, 'assessments/story_list.html', context)


@login_required
def generate_story(request):
    """Generate a new story using AI"""
    if request.method == 'POST':
        theme = request.POST.get('theme', 'kindness')
        age_group = request.POST.get('age_group', '6-7')
        difficulty = int(request.POST.get('difficulty', 1))
        
        # Generate story using Gemini
        generator = StoryGeneratorService()
        story_data = generator.generate_story(theme, age_group, difficulty)
        
        # Save to database
        story = Story.objects.create(
            title=story_data['title'],
            theme=theme,
            age_group=age_group,
            story_content=story_data['story'],
            characters=story_data.get('characters', []),
            questions=story_data['questions'],
            difficulty_level=difficulty,
            generated_by_ai=True
        )
        
        messages.success(request, f"✨ New story '{story.title}' generated!")
        return redirect('assessments:story_detail', story_id=story.id)
    
    # GET request - show generation form
    themes = Story.THEME_CHOICES
    age_groups = Story.AGE_GROUP_CHOICES
    
    context = {
        'themes': themes,
        'age_groups': age_groups,
    }
    
    return render(request, 'assessments/generate_story.html', context)


@login_required
def story_detail(request, story_id):
    """Display story and comprehension questions"""
    story = get_object_or_404(Story, id=story_id)
    
    # Get or create progress for student
    progress = None
    if hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        progress, created = StoryProgress.objects.get_or_create(
            student=student,
            story=story
        )
    
    context = {
        'story': story,
        'progress': progress,
    }
    
    return render(request, 'assessments/story_detail.html', context)


@login_required
def submit_answers(request, story_id):
    """Submit and evaluate comprehension answers"""
    if request.method != 'POST':
        return redirect('assessments:story_detail', story_id=story_id)
    
    story = get_object_or_404(Story, id=story_id)
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can submit answers.")
        return redirect('assessments:story_detail', story_id=story_id)
    
    student = request.user.student_profile
    progress = get_object_or_404(StoryProgress, student=student, story=story)
    
    # Collect answers
    answers = {}
    for i, question_data in enumerate(story.questions):
        answer_key = f'answer_{i}'
        answers[f'q{i}'] = request.POST.get(answer_key, '')
    
    # Evaluate answers using AI
    generator = StoryGeneratorService()
    correct_count = 0
    
    for i, question_data in enumerate(story.questions):
        student_answer = answers.get(f'q{i}', '')
        correct_answer = question_data.get('answer', '')
        
        if student_answer.strip():
            evaluation = generator.evaluate_answer(student_answer, correct_answer)
            if evaluation.get('is_correct', False):
                correct_count += 1
    
    # Calculate score (0-5)
    total_questions = len(story.questions)
    score = round((correct_count / total_questions) * 5) if total_questions > 0 else 0
    
    # Get emotion from form (placeholder for future integration)
    emotion = request.POST.get('emotion', '')
    
    # Generate feedback
    feedback = generator.generate_feedback(score, emotion)
    
    # Update progress
    progress.answers = answers
    progress.score = score
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.emotion_detected = emotion
    progress.feedback_given = feedback
    progress.save()
    
    # Check for badge achievements
    check_and_award_badges(student)
    
    messages.success(request, f"🎉 {feedback}")
    return redirect('assessments:story_results', story_id=story_id)


@login_required
def story_results(request, story_id):
    """Display story results and feedback"""
    story = get_object_or_404(Story, id=story_id)
    
    if not hasattr(request.user, 'student_profile'):
        return redirect('assessments:story_detail', story_id=story_id)
    
    student = request.user.student_profile
    progress = get_object_or_404(StoryProgress, student=student, story=story)
    
    # Get newly earned badges (last 5 minutes)
    from datetime import timedelta
    recent_time = timezone.now() - timedelta(minutes=5)
    new_badges = StudentBadge.objects.filter(
        student=student,
        earned_at__gte=recent_time
    ).select_related('badge')
    
    context = {
        'story': story,
        'progress': progress,
        'new_badges': new_badges,
    }
    
    return render(request, 'assessments/story_results.html', context)


def check_and_award_badges(student):
    """Check achievements and award badges"""
    
    # Get all completed stories
    completed_count = StoryProgress.objects.filter(
        student=student,
        is_completed=True
    ).count()
    
    # Get perfect scores
    perfect_scores = StoryProgress.objects.filter(
        student=student,
        score=5
    ).count()
    
    # Get stories with good scores (4 or 5)
    good_scores = StoryProgress.objects.filter(
        student=student,
        score__gte=4
    ).count()
    
    # 📖 Enchanted Storybook: Complete your first story!
    if completed_count >= 1:
        badge, created = Badge.objects.get_or_create(
            badge_type='enchanted_storybook',
            defaults={
                'name': 'Enchanted Storybook',
                'description': 'Completed your first magical story! 📖',
                'icon': '📖',
                'color': '#FFE5E5',
                'requirement': {'stories_completed': 1}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # 📜 Adventure Scroll: Complete 3 stories
    if completed_count >= 3:
        badge, created = Badge.objects.get_or_create(
            badge_type='adventure_scroll',
            defaults={
                'name': 'Adventure Scroll',
                'description': 'Completed 3 exciting adventures! 📜',
                'icon': '📜',
                'color': '#FFF4E0',
                'requirement': {'stories_completed': 3}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # 🎭 Fantasy Narrator: Complete 5 stories with good scores
    if completed_count >= 5 and good_scores >= 5:
        badge, created = Badge.objects.get_or_create(
            badge_type='fantasy_narrator',
            defaults={
                'name': 'Fantasy Narrator',
                'description': 'Completed 5 stories with great understanding! 🎭',
                'icon': '🎭',
                'color': '#E5F3FF',
                'requirement': {'stories_completed': 5, 'good_scores': 5}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # 🌟 Imagination Explorer: Complete 10 stories
    if completed_count >= 10:
        badge, created = Badge.objects.get_or_create(
            badge_type='imagination_explorer',
            defaults={
                'name': 'Imagination Explorer',
                'description': 'Explored 10 amazing worlds of imagination! 🌟',
                'icon': '🌟',
                'color': '#F0E5FF',
                'requirement': {'stories_completed': 10}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # Story Explorer: Complete 5 stories (legacy badge)
    if completed_count >= 5:
        badge, created = Badge.objects.get_or_create(
            badge_type='story_explorer',
            defaults={
                'name': 'Story Explorer',
                'description': 'Completed 5 amazing stories!',
                'icon': '📚',
                'color': '#B4E7CE',
                'requirement': {'stories_completed': 5}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # Super Reader: Get 3 perfect scores
    if perfect_scores >= 3:
        badge, created = Badge.objects.get_or_create(
            badge_type='super_reader',
            defaults={
                'name': 'Super Reader',
                'description': 'Got 3 perfect scores!',
                'icon': '⭐',
                'color': '#FFD4E5',
                'requirement': {'perfect_scores': 3}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)
    
    # Perfect Score: Get a perfect score
    if perfect_scores >= 1:
        badge, created = Badge.objects.get_or_create(
            badge_type='perfect_score',
            defaults={
                'name': 'Perfect Score',
                'description': 'Answered all questions correctly!',
                'icon': '🏆',
                'color': '#FFEAA7',
                'requirement': {'perfect_scores': 1}
            }
        )
        StudentBadge.objects.get_or_create(student=student, badge=badge)


@login_required
def student_badges(request):
    """Display all student badges"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can view badges.")
        return redirect('home')
    
    student = request.user.student_profile
    earned_badges = StudentBadge.objects.filter(student=student).select_related('badge')
    all_badges = Badge.objects.all()
    
    # Separate earned and unearned
    earned_badge_ids = [sb.badge_id for sb in earned_badges]
    unearned_badges = all_badges.exclude(id__in=earned_badge_ids)
    
    context = {
        'earned_badges': earned_badges,
        'unearned_badges': unearned_badges,
    }
    
    return render(request, 'assessments/student_badges.html', context)


@login_required
def story_correction(request):
    """
    AI Story Correction - Display form and previous submissions
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Only students can access story correction.")
        return redirect('home')
    
    student = request.user.student_profile
    
    # Get previous submissions
    previous_assessments = StoryAssessment.objects.filter(
        student=student
    ).order_by('-created_at')[:5]  # Last 5 submissions
    
    context = {
        'previous_assessments': previous_assessments,
    }
    
    return render(request, 'assessments/story_correction.html', context)


@login_required
@require_http_methods(["POST"])
def submit_story_correction(request):
    """
    Submit story for AI correction and feedback
    """
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({
            'success': False,
            'error': 'Only students can submit stories.'
        }, status=403)
    
    student = request.user.student_profile
    
    # Get story text from POST
    story_text = request.POST.get('story_text', '').strip()
    
    # Validate input
    if not story_text:
        return JsonResponse({
            'success': False,
            'error': 'Please write a story before submitting!'
        }, status=400)
    
    if len(story_text) < 20:
        return JsonResponse({
            'success': False,
            'error': 'Your story is too short! Please write at least 20 characters.'
        }, status=400)
    
    if len(story_text) > 5000:
        return JsonResponse({
            'success': False,
            'error': 'Your story is too long! Please keep it under 5000 characters.'
        }, status=400)
    
    try:
        # Call Gemini API for correction
        generator = StoryGeneratorService()
        result = generator.correct_story(story_text)
        
        # Save to database
        assessment = StoryAssessment.objects.create(
            student=student,
            original_story=story_text,
            corrected_story=result['corrected_story'],
            feedback=result['feedback'],
            questions=result['questions'],
            badge=result['badge'],
            creativity_score=result.get('creativity_score', 5)
        )
        
        # Award badge to student (if they don't already have it)
        badge_type = result['badge']
        try:
            # Get or create the badge in the Badge model
            badge_obj, created = Badge.objects.get_or_create(
                badge_type=badge_type,
                defaults={
                    'name': badge_type.replace('_', ' ').title(),
                    'description': f'Earned by writing creative stories',
                    'icon': '✍️',
                    'color': '#8B5CF6',
                    'requirement': {'type': 'story_writing', 'count': 1}
                }
            )
            
            # Award badge to student (only if they don't have it)
            StudentBadge.objects.get_or_create(
                student=student,
                badge=badge_obj
            )
        except Exception as badge_error:
            print(f"Error awarding badge: {str(badge_error)}")
            # Continue even if badge awarding fails
        
        # Return success response with data
        return JsonResponse({
            'success': True,
            'data': {
                'corrected_story': result['corrected_story'],
                'feedback': result['feedback'],
                'questions': result['questions'],
                'badge': result['badge'],
                'creativity_score': result.get('creativity_score', 5),
                'assessment_id': assessment.id
            }
        })
        
    except Exception as e:
        print(f"Error in story correction: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Sorry, something went wrong. Please try again!'
        }, status=500)


@login_required
def view_story_assessment(request, assessment_id):
    """
    View a specific story assessment
    """
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access denied.")
        return redirect('home')
    
    student = request.user.student_profile
    assessment = get_object_or_404(
        StoryAssessment,
        id=assessment_id,
        student=student
    )
    
    context = {
        'assessment': assessment,
    }
    
    return render(request, 'assessments/view_assessment.html', context)
