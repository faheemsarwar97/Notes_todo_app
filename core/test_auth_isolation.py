from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Note, Todo

class AuthIsolationTest(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        
        # Client 1
        self.client1 = Client()
        self.client1.login(username='user1', password='password123')
        
        # Client 2
        self.client2 = Client()
        self.client2.login(username='user2', password='password123')

    def test_note_isolation(self):
        # User 1 creates a note
        note = Note.objects.create(user=self.user1, title="User 1 Note", content="Secret")
        
        # User 1 should see it
        response = self.client1.get('/notes/')
        self.assertContains(response, "User 1 Note")
        
        # User 2 should NOT see it
        response = self.client2.get('/notes/')
        self.assertNotContains(response, "User 1 Note")

    def test_todo_isolation(self):
        # User 2 creates a todo
        todo = Todo.objects.create(user=self.user2, task="User 2 Task")
        
        # User 2 should see it
        response = self.client2.get('/todos/')
        self.assertContains(response, "User 2 Task")
        
        # User 1 should NOT see it
        response = self.client1.get('/todos/')
        self.assertNotContains(response, "User 2 Task")

    def test_login_required(self):
        # Unauthenticated client
        client = Client()
        response = client.get('/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
