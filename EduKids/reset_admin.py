#!/usr/bin/env python
"""Reset admin password for EduKids"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from students.models import User

# Check existing superusers
print("=== Existing Superusers ===")
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    print(f"Username: {user.username}, Email: {user.email}")

# Reset admin password
try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("\n✅ Password reset successfully for 'admin'")
    print("Username: admin")
    print("Password: admin123")
except User.DoesNotExist:
    print("\n❌ User 'admin' does not exist. Creating new superuser...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@edukids.com',
        password='admin123',
        first_name='Admin',
        last_name='User',
        user_type='admin'
    )
    print("✅ Superuser 'admin' created successfully!")
    print("Username: admin")
    print("Password: admin123")
