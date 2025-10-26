"""
Story CRUD Views - EduKids
Complete Create, Read, Update, Delete operations for Story management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .story_models import Story, StoryProgress
from .story_forms import StoryForm, StorySearchForm


def is_teacher_or_admin(user):
    """Check if user is teacher or admin"""
    return user.is_authenticated and (user.user_type in ['teacher', 'admin'] or user.is_superuser)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_manage_list(request):
    """
    List all stories with search and filter options (Teacher/Admin only)
    """
    # Get all stories
    stories = Story.objects.all().order_by('-created_at')
    
    # Initialize search form
    search_form = StorySearchForm(request.GET)
    
    # Apply filters
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        theme = search_form.cleaned_data.get('theme')
        age_group = search_form.cleaned_data.get('age_group')
        difficulty = search_form.cleaned_data.get('difficulty')
        
        if search_query:
            stories = stories.filter(
                Q(title__icontains=search_query) |
                Q(characters__icontains=search_query)
            )
        
        if theme:
            stories = stories.filter(theme=theme)
        
        if age_group:
            stories = stories.filter(age_group=age_group)
        
        if difficulty:
            stories = stories.filter(difficulty_level=int(difficulty))
    
    # Pagination
    paginator = Paginator(stories, 10)  # 10 stories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_stories = Story.objects.count()
    ai_generated = Story.objects.filter(generated_by_ai=True).count()
    manual_stories = total_stories - ai_generated
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_stories': total_stories,
        'ai_generated': ai_generated,
        'manual_stories': manual_stories,
    }
    
    return render(request, 'assessments/story_manage_list.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_create(request):
    """
    Create a new story (Teacher/Admin only)
    """
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            try:
                story = form.save()
                messages.success(
                    request,
                    f'✅ Story "{story.title}" created successfully!'
                )
                return redirect('assessments:story_manage_detail', pk=story.pk)
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error creating story: {str(e)}'
                )
        else:
            messages.error(
                request,
                '❌ Please correct the errors below.'
            )
    else:
        form = StoryForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'button_text': 'Create Story',
    }
    
    return render(request, 'assessments/story_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_manage_detail(request, pk):
    """
    View story details with statistics (Teacher/Admin only)
    """
    story = get_object_or_404(Story, pk=pk)
    
    # Get statistics
    total_reads = StoryProgress.objects.filter(story=story).count()
    completed_reads = StoryProgress.objects.filter(story=story, is_completed=True).count()
    average_score = 0
    
    if completed_reads > 0:
        scores = StoryProgress.objects.filter(
            story=story,
            is_completed=True,
            score__isnull=False
        ).values_list('score', flat=True)
        if scores:
            average_score = sum(scores) / len(scores)
    
    context = {
        'story': story,
        'total_reads': total_reads,
        'completed_reads': completed_reads,
        'average_score': round(average_score, 1),
    }
    
    return render(request, 'assessments/story_manage_detail.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_update(request, pk):
    """
    Update an existing story (Teacher/Admin only)
    """
    story = get_object_or_404(Story, pk=pk)
    
    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            try:
                story = form.save()
                messages.success(
                    request,
                    f'✅ Story "{story.title}" updated successfully!'
                )
                return redirect('assessments:story_manage_detail', pk=story.pk)
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error updating story: {str(e)}'
                )
        else:
            messages.error(
                request,
                '❌ Please correct the errors below.'
            )
    else:
        form = StoryForm(instance=story)
    
    context = {
        'form': form,
        'story': story,
        'action': 'Update',
        'button_text': 'Update Story',
    }
    
    return render(request, 'assessments/story_form.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_delete(request, pk):
    """
    Delete a story (Teacher/Admin only)
    """
    story = get_object_or_404(Story, pk=pk)
    
    if request.method == 'POST':
        story_title = story.title
        try:
            story.delete()
            messages.success(
                request,
                f'✅ Story "{story_title}" deleted successfully!'
            )
            return redirect('assessments:story_manage_list')
        except Exception as e:
            messages.error(
                request,
                f'❌ Error deleting story: {str(e)}'
            )
            return redirect('assessments:story_manage_detail', pk=pk)
    
    # Check if story has any progress records
    progress_count = StoryProgress.objects.filter(story=story).count()
    
    context = {
        'story': story,
        'progress_count': progress_count,
    }
    
    return render(request, 'assessments/story_confirm_delete.html', context)


@login_required
@user_passes_test(is_teacher_or_admin)
def story_bulk_delete(request):
    """
    Bulk delete stories (Teacher/Admin only)
    """
    if request.method == 'POST':
        story_ids = request.POST.getlist('story_ids')
        
        if not story_ids:
            messages.warning(request, '⚠️ No stories selected.')
            return redirect('assessments:story_manage_list')
        
        try:
            stories = Story.objects.filter(id__in=story_ids)
            count = stories.count()
            stories.delete()
            messages.success(
                request,
                f'✅ Successfully deleted {count} story(ies)!'
            )
        except Exception as e:
            messages.error(
                request,
                f'❌ Error deleting stories: {str(e)}'
            )
        
        return redirect('assessments:story_manage_list')
    
    return redirect('assessments:story_manage_list')


@login_required
@user_passes_test(is_teacher_or_admin)
def story_duplicate(request, pk):
    """
    Duplicate an existing story (Teacher/Admin only)
    """
    original_story = get_object_or_404(Story, pk=pk)
    
    try:
        # Create a copy
        new_story = Story.objects.create(
            title=f"{original_story.title} (Copy)",
            theme=original_story.theme,
            age_group=original_story.age_group,
            story_content=original_story.story_content,
            characters=original_story.characters,
            questions=original_story.questions,
            difficulty_level=original_story.difficulty_level,
            reading_time_minutes=original_story.reading_time_minutes,
            generated_by_ai=original_story.generated_by_ai
        )
        
        messages.success(
            request,
            f'✅ Story duplicated successfully! You can now edit "{new_story.title}".'
        )
        return redirect('assessments:story_update', pk=new_story.pk)
        
    except Exception as e:
        messages.error(
            request,
            f'❌ Error duplicating story: {str(e)}'
        )
        return redirect('assessments:story_manage_detail', pk=pk)
