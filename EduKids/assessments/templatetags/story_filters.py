"""
Custom template filters for story templates
"""
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary in template"""
    if dictionary and key:
        return dictionary.get(key)
    return None

@register.filter
def make_answer_key(index):
    """Convert index to answer key format (e.g., 0 -> 'q0')"""
    return f'q{index}'
