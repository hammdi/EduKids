"""
Test script to verify Gemini API integration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EduKids.settings')
django.setup()

from assessments.story_service import StoryGeneratorService

print("=" * 60)
print("🧪 Testing Gemini API Integration")
print("=" * 60)

# Create service
service = StoryGeneratorService()
print("✅ Service initialized successfully")

# Test story generation
print("\n🎨 Generating a story about 'teamwork'...")
print("-" * 60)

story = service.generate_story(
    theme="teamwork",
    age_group="6-7",
    difficulty=1
)

print("\n📖 Generated Story:")
print("-" * 60)
print(f"Title: {story['title']}")
print(f"\nStory:")
for i, paragraph in enumerate(story['story'], 1):
    print(f"  {i}. {paragraph}")

print(f"\nCharacters: {', '.join(story['characters'])}")

print(f"\n❓ Questions:")
for i, q in enumerate(story['questions'], 1):
    print(f"  {i}. {q['question']}")
    print(f"     Answer: {q['answer']}")

print("\n" + "=" * 60)
print("✅ Test completed!")
print("=" * 60)
