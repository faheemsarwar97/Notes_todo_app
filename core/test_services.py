from django.test import TestCase
from django.utils import timezone
from .services import NoteService, TodoService
from .models import Note, Todo
import datetime

class ServiceTestCase(TestCase):
    def setUp(self):
        self.note_service = NoteService()
        self.todo_service = TodoService()

    def test_note_crud(self):
        # Create
        data = {"title": "Test Note", "content": "Content"}
        success, note = self.note_service.create(data)
        self.assertTrue(success)
        self.assertEqual(note.title, "Test Note")

        # List
        notes = self.note_service.list_all()
        self.assertEqual(len(notes), 1)

        # Get
        fetched = self.note_service.get_by_id(note.id)
        self.assertEqual(fetched.id, note.id)

        # Update
        update_data = {"title": "Updated Title", "content": "Content"}
        success, updated = self.note_service.update(note.id, update_data)
        self.assertTrue(success)
        self.assertEqual(updated.title, "Updated Title")

        # Delete
        self.note_service.delete(note.id)
        self.assertEqual(len(self.note_service.list_all()), 0)

    def test_todo_dashboard_stats(self):
        # Setup
        Note.objects.create(title="N1", content="C1")
        Todo.objects.create(task="T1", done=False)
        Todo.objects.create(task="T2", done=True)
        
        # Test stats
        stats = self.todo_service.get_dashboard_stats()
        self.assertEqual(stats["notes_count"], 1)
        self.assertEqual(stats["todos_count"], 2)
        self.assertEqual(stats["completed_todos"], 1)

    def test_reminders_logic(self):
        now = timezone.now()
        # Overdue
        Todo.objects.create(task="Overdue", reminder=now - datetime.timedelta(hours=2), done=False)
        # Upcoming
        Todo.objects.create(task="Upcoming", reminder=now + datetime.timedelta(hours=2), done=False)
        
        reminders = self.todo_service.get_reminders(now)
        self.assertEqual(reminders["overdue_count"], 1)
        self.assertEqual(len(reminders["upcoming"]), 1)

    def test_priority_matrix(self):
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Important & Urgent (Due today)
        Todo.objects.create(task="ImpUrg", is_important=True, due_date=today, done=False)
        # Important & Not Urgent (Due in 2 days)
        Todo.objects.create(task="ImpNotUrg", is_important=True, due_date=today + datetime.timedelta(days=2), done=False)

        matrix = self.todo_service.get_priority_matrix(now)
        self.assertEqual(len(matrix["important_urgent"]), 1)
        self.assertEqual(len(matrix["important_not_urgent"]), 1)
        self.assertEqual(matrix["important_urgent"][0].task, "ImpUrg")
