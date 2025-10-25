"""
List available Gemini models
"""
import google.generativeai as genai

# Configure API
genai.configure(api_key='AIzaSyD19fEQdWAy8LMILMWvtKtWylTz7diTE6E')

print("=" * 60)
print("📋 Available Gemini Models")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
