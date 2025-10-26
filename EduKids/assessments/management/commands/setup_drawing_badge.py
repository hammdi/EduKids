"""
Management command to set up the drawing badge with custom image
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from assessments.models import Badge
import os


class Command(BaseCommand):
    help = 'Creates the Little Artist badge for drawing feature'

    def handle(self, *args, **options):
        # Create or update the drawing badge
        badge, created = Badge.objects.get_or_create(
            badge_type='drawing',
            defaults={
                'name': 'Little Artist',
                'description': 'Created your first character drawing! 🎨',
                'icon': '🎨',
                'color': '#FFB6C1',
                'requirement': {'drawings': 1}
            }
        )
        
        # Try multiple possible locations for the image
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'draw.png'),
            os.path.join(settings.BASE_DIR, 'EduKids', 'static', 'images', 'draw.png'),
            os.path.join('static', 'images', 'draw.png'),
        ]
        
        image_found = False
        for image_path in possible_paths:
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    badge.image.save('draw.png', File(f), save=True)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully {"created" if created else "updated"} Little Artist badge with custom image!')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'📁 Image loaded from: {image_path}')
                )
                image_found = True
                break
        
        if not image_found:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Badge created but image not found')
            )
            self.stdout.write(
                self.style.WARNING(f'Searched in:')
            )
            for path in possible_paths:
                self.stdout.write(self.style.WARNING(f'  - {path}'))
            self.stdout.write(
                self.style.WARNING('Please add the badge image manually in Django admin')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Badge ID: {badge.id}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Badge Type: {badge.badge_type}')
        )
