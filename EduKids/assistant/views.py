from django.shortcuts import render


def chat_view(request):
	"""Simple page de chat pour l'assistant virtuel.

	Cette vue rend une interface conversationnelle minimale qui se connecte
	au WebSocket `ws/assistant/` et permet le TTS via Web Speech API.
	"""
	return render(request, 'assistant/chat.html', {})
