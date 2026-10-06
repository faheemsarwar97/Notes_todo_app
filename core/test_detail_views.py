from django.test import TestCase, Client
from django.urls import reverse
from .models import Note, Todo

class DetailViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.note = Note.objects.create(title="Test Note", content="Content")
        self.todo = Todo.objects.create(task="Test Todo")

    def test_note_detail(self):
        response = self.client.get(reverse('notes_detail', args=[self.note.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Note")
        self.assertContains(response, "Content")

    def test_todo_detail(self):
        response = self.client.get(reverse('todos_detail', args=[self.todo.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Todo")
