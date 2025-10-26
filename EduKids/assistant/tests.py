from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from datetime import date

from students.models import User, Student
from .models import Conversation, Message, VirtualAssistant


class AssistantApiTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='stu', password='x', user_type='student')
		self.student = Student.objects.create(
			user=self.user,
			grade_level='CM1',
			birth_date=date(2015, 1, 1),
			preferred_language='fr'
		)
		self.assistant = VirtualAssistant.objects.create(
			name='TestBot',
			personality='friendly',
			language='fr',
			system_prompt='You are a helpful assistant.'
		)
		self.conv = Conversation.objects.create(student=self.student, assistant=self.assistant, title='Test conv')
		self.msg_student = Message.objects.create(conversation=self.conv, sender_type='student', message_type='text', content='Bonjour')
		self.msg_assistant = Message.objects.create(conversation=self.conv, sender_type='assistant', message_type='text', content='Salut!')

	def test_history_view(self):
		url = reverse('assistant:history') + f'?student_id={self.user.id}&limit=3'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIn('conversations', data)
		self.assertGreaterEqual(len(data['conversations']), 1)

	def test_conversation_detail(self):
		url = reverse('assistant:conversation_detail', args=[self.conv.id]) + f'?student_id={self.user.id}'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIn('conversation', data)
		self.assertEqual(data['conversation']['id'], self.conv.id)

	def test_search_conversations(self):
		# search by title
		url = reverse('assistant:search_conversations') + f'?student_id={self.user.id}&q=Test'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertGreaterEqual(len(resp.json().get('results', [])), 1)

		# search by message content
		url = reverse('assistant:search_conversations') + f'?student_id={self.user.id}&q=Bonjour'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertGreaterEqual(len(resp.json().get('results', [])), 1)

	def test_edit_message_student_only(self):
		url = reverse('assistant:edit_message', args=[self.msg_student.id])
		resp = self.client.post(url, data={'student_id': self.user.id, 'content': 'Bonjour modifié'}, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		self.msg_student.refresh_from_db()
		self.assertEqual(self.msg_student.content, 'Bonjour modifié')

		# attempt editing assistant message should be forbidden
		url = reverse('assistant:edit_message', args=[self.msg_assistant.id])
		resp = self.client.post(url, data={'student_id': self.user.id, 'content': 'Hack'}, content_type='application/json')
		self.assertEqual(resp.status_code, 403)

	def test_delete_message_student_only(self):
		url = reverse('assistant:delete_message', args=[self.msg_student.id])
		resp = self.client.post(url, data={'student_id': self.user.id}, content_type='application/json')
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(Message.objects.filter(id=self.msg_student.id).exists())

		# attempt delete assistant message should be forbidden
		url = reverse('assistant:delete_message', args=[self.msg_assistant.id])
		resp = self.client.post(url, data={'student_id': self.user.id}, content_type='application/json')
		self.assertEqual(resp.status_code, 403)

	def test_delete_conversation(self):
		url = reverse('assistant:delete_conversation', args=[self.conv.id]) + f'?student_id={self.user.id}'
		resp = self.client.post(url)
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(Conversation.objects.filter(id=self.conv.id).exists())
