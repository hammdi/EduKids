"""
Drawing views for character creation - EduKids
"""
import base64
import io
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.conf import settings
from django.contrib import messages
from .models import CharacterDrawing, Story, Badge, StudentBadge
from students.models import Student
import google.generativeai as genai


@login_required
def drawing_page(request):
    """
    Render the drawing canvas page
    """
    # Get all available stories for linking (stories are shared, not per-student)
    stories = Story.objects.all().order_by('-created_at')[:20]  # Limit to recent 20
    
    context = {
        'stories': stories,
    }
    return render(request, 'drawing/draw_character.html', context)


@login_required
def save_drawing(request):
    """
    Save a drawing from canvas as PNG
    """
    if request.method == 'POST':
        try:
            # Get student
            student = Student.objects.get(user=request.user)
            
            # Get form data
            title = request.POST.get('title', 'My Character')
            image_data = request.POST.get('image_data')
            story_id = request.POST.get('story_id')
            
            if not image_data:
                return JsonResponse({'success': False, 'error': 'No image data provided'})
            
            # Decode base64 image
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_file = ContentFile(base64.b64decode(imgstr), name=f'{title}.{ext}')
            
            # Get linked story if provided (stories are shared, not per-student)
            story = None
            if story_id and story_id != '':
                try:
                    story = Story.objects.get(id=story_id)
                except (Story.DoesNotExist, ValueError):
                    # Invalid story ID or story doesn't exist - just skip linking
                    pass
            
            # Create drawing
            drawing = CharacterDrawing.objects.create(
                student=student,
                story=story,
                title=title,
                image=image_file
            )
            
            # Award "First Drawing" badge if this is their first drawing
            badge_awarded = False
            if CharacterDrawing.objects.filter(student=student).count() == 1:
                # This is their first drawing!
                try:
                    # Get or create the "Little Artist" badge
                    artist_badge, created = Badge.objects.get_or_create(
                        badge_type='drawing',
                        defaults={
                            'name': 'Little Artist',
                            'description': 'Created your first character drawing!',
                            'icon': '🎨',
                            'color': '#FFB6C1',
                            'requirement': {'drawings': 1}
                        }
                    )
                    
                    # Award badge to student (if not already earned)
                    StudentBadge.objects.get_or_create(
                        student=student,
                        badge=artist_badge
                    )
                    badge_awarded = True
                except Exception as e:
                    print(f"Error awarding badge: {e}")
            
            response_message = 'Drawing saved successfully! 🎨'
            if badge_awarded:
                response_message += ' You earned the Little Artist badge! 🏆'
            
            return JsonResponse({
                'success': True,
                'drawing_id': drawing.id,
                'message': response_message,
                'badge_awarded': badge_awarded
            })
            
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
        except Exception as e:
            import traceback
            print(f"Error in save_drawing: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def gallery_page(request):
    """
    Display all user's saved drawings
    """
    try:
        student = Student.objects.get(user=request.user)
        drawings = CharacterDrawing.objects.filter(student=student).order_by('-created_at')
        
        # Calculate badges
        total_drawings = drawings.count()
        has_ai_enhanced = drawings.filter(ai_version__isnull=False).exists()
        has_linked_story = drawings.filter(story__isnull=False).exists()
        
        badges = []
        if total_drawings >= 1:
            badges.append({'name': 'First Drawing!', 'icon': '🎖️', 'color': 'success'})
        if total_drawings >= 5:
            badges.append({'name': 'Creative Genius', 'icon': '🌈', 'color': 'primary'})
        if total_drawings >= 10:
            badges.append({'name': 'Color Explorer', 'icon': '🧑‍🎨', 'color': 'warning'})
        if has_ai_enhanced:
            badges.append({'name': 'AI Artist', 'icon': '✨', 'color': 'info'})
        if has_linked_story:
            badges.append({'name': 'Story Illustrator', 'icon': '📖', 'color': 'danger'})
        
        context = {
            'drawings': drawings,
            'total_drawings': total_drawings,
            'badges': badges,
        }
        return render(request, 'drawing/gallery.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found')
        return redirect('home')


@login_required
def cartoonify_drawing(request, drawing_id):
    """
    Use Gemini AI to enhance/cartoonify a drawing
    """
    if request.method == 'POST':
        try:
            # Get student and drawing
            student = Student.objects.get(user=request.user)
            drawing = get_object_or_404(CharacterDrawing, id=drawing_id, student=student)
            
            # Check if Gemini API key is configured
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                return JsonResponse({
                    'success': False,
                    'error': 'AI feature not configured. Please add GEMINI_API_KEY to settings.'
                })
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Read the original image
            with drawing.image.open('rb') as img_file:
                image_data = img_file.read()
            
            # Create the model
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Prepare the prompt
            prompt = """You are an art assistant for children (ages 6–12). 
Transform this drawing into a colorful cartoon character suitable for a kids' storybook.
Keep the shapes and colors similar, but make it soft, pastel, and joyful.
Make it look professional but maintain the child's creative vision.
The character should be friendly, cute, and appropriate for children."""
            
            # Generate AI version
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
            
            # Note: Gemini doesn't directly return images, so we'll need to use a different approach
            # For now, we'll return a success message
            # In production, you might want to use DALL-E or Stable Diffusion for image generation
            
            return JsonResponse({
                'success': True,
                'message': 'AI enhancement requested! This feature requires image generation API.',
                'note': 'Consider using DALL-E or Stable Diffusion for actual image generation'
            })
            
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def delete_drawing(request, drawing_id):
    """
    Delete a character drawing
    """
    if request.method == 'POST':
        try:
            student = Student.objects.get(user=request.user)
            drawing = get_object_or_404(CharacterDrawing, id=drawing_id, student=student)
            
            # Delete the image files
            if drawing.image:
                drawing.image.delete()
            if drawing.ai_version:
                drawing.ai_version.delete()
            
            # Delete the drawing
            drawing.delete()
            
            messages.success(request, f'"{drawing.title}" has been deleted! 🗑️')
            return redirect('assessments:gallery_page')
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found')
            return redirect('home')
    
    return redirect('assessments:gallery_page')
