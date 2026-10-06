from django.shortcuts import get_object_or_404
from .models import Note, Todo
from .forms import NoteForm, TodoForm
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

class BaseCRUDService:
    def __init__(self, model_class, form_class, user):
        self.model = model_class
        self.form_class = form_class
        self.user = user

    def list_all(self):
        """Return all objects for the user ordered by creation date descending."""
        return self.model.objects.filter(user=self.user).order_by("-created_at")

    def get_by_id(self, pk):
        """Get object or 404, ensuring it belongs to the user."""
        return get_object_or_404(self.model, pk=pk, user=self.user)

    def create(self, request_post_data):
        """
        Process form data to create a new object.
        Returns (success, object_or_form)
        """
        form = self.form_class(request_post_data)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = self.user
            obj.save()
            return True, obj
        return False, form

    def update(self, pk, request_post_data):
        """
        Process form data to update an existing object.
        Returns (success, object_or_form)
        """
        obj = self.get_by_id(pk)
        form = self.form_class(request_post_data, instance=obj)
        if form.is_valid():
            obj = form.save()
            return True, obj
        return False, form

    def delete(self, pk):
        """Delete object by ID."""
        obj = self.get_by_id(pk)
        obj.delete()
        return True

class NoteService(BaseCRUDService):
    def __init__(self, user):
        super().__init__(Note, NoteForm, user)

class TodoService(BaseCRUDService):
    def __init__(self, user):
        super().__init__(Todo, TodoForm, user)

    # ---------------------------
    # Dashboard / Reporting Logic
    # ---------------------------

    def get_dashboard_stats(self, query=None):
        """
        Aggregate stats for the dashboard.
        """
        # User-specific queries
        user_notes = Note.objects.filter(user=self.user)
        user_todos = self.model.objects.filter(user=self.user)

        # Global counts
        notes_count = user_notes.count()
        # Count only pending tasks (done=False) for the dashboard stat
        todos_count = user_todos.filter(done=False).count()
        completed_todos = user_todos.filter(done=True).count()

        # Search results
        notes_results = []
        todos_results = []
        if query:
            notes_results = user_notes.filter(title__icontains=query)
            todos_results = user_todos.filter(task__icontains=query)

        return {
            "notes_count": notes_count,
            "todos_count": todos_count,
            "completed_todos": completed_todos,
            "notes_results": notes_results,
            "todos_results": todos_results,
        }

    def get_reminders(self, now):
        """
        Return upcoming, overdue, and soon reminders.
        """
        # Get ALL reminders that have a reminder set and aren't done, for THIS user
        all_reminders_qs = self.model.objects.filter(user=self.user, reminder__isnull=False, done=False).order_by('reminder')
        
        overdue_qs = all_reminders_qs.filter(reminder__lt=now)
        upcoming_qs = all_reminders_qs.filter(reminder__gte=now)
        
        soon_threshold = now + timedelta(hours=1)
        soon_qs = upcoming_qs.filter(reminder__lte=soon_threshold)

        return {
            "upcoming": list(upcoming_qs[:5]),
            "overdue": list(overdue_qs[:5]),
            "soon": list(soon_qs[:5]),
            "overdue_count": overdue_qs.count(),
            "soon_count": soon_qs.count()
        }

    def get_daily_focus(self, now):
        """Return tasks due today."""
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return self.model.objects.filter(user=self.user, due_date__gte=today_start, due_date__lt=today_end, done=False).order_by('due_date')[:10]

    def get_priority_matrix(self, now):
        """Categorize tasks into Urgent/Important quadrants."""
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today_start + timedelta(days=1)
        
        base_qs = self.model.objects.filter(user=self.user, done=False, is_important=True)

        # Important AND urgent (marked important + due today/tomorrow)
        important_urgent = base_qs.filter(due_date__lte=tomorrow).order_by('due_date')[:5]

        # Important but NOT urgent (marked important + due later)
        important_not_urgent = base_qs.filter(
            due_date__gt=tomorrow,
            due_date__isnull=False
        ).order_by('due_date')[:5]

        # All important tasks (for dashboard display)
        all_important = base_qs.order_by('due_date')[:8]

        return {
            "important_urgent": important_urgent,
            "important_not_urgent": important_not_urgent,
            "all_important": all_important
        }

    # ---------------------------
    # Endpoint Helpers
    # ---------------------------

    def get_reminders_status_data(self, now):
        """
        Data for the JSON polling endpoint.
        """
        base_qs = self.model.objects.filter(user=self.user, reminder__isnull=False, done=False).order_by('reminder')
        
        upcoming_qs = base_qs.filter(reminder__gte=now)
        overdue_qs = base_qs.filter(reminder__lt=now)
        
        soon_threshold = now + timedelta(hours=1)
        soon_qs = upcoming_qs.filter(reminder__lte=soon_threshold)

        def serialize(qs, limit=10):
            items = []
            for r in qs[:limit]:
                items.append({
                    'id': r.id,
                    'task': r.task,
                    'reminder': r.reminder.strftime('%Y-%m-%d %H:%M'),
                    'due_date': r.due_date.strftime('%Y-%m-%d') if r.due_date else None,
                    'activity': r.get_activity_display(),
                    'is_important': r.is_important,
                    'done': r.done,
                    'created_at': r.created_at.strftime('%Y-%m-%d') if r.created_at else None,
                    'edit_url': f"/todos/edit/{r.id}/",
                })
            return items

        return {
            'overdue': serialize(overdue_qs, limit=20),
            'soon': serialize(soon_qs, limit=20),
            'now': now.strftime('%Y-%m-%d %H:%M:%S'),
            'overdue_count': overdue_qs.count(),
            'soon_count': soon_qs.count(),
        }

    def get_calendar_data(self):
        """
        Group todos by month for the calendar view.
        """
        pending_todos = self.model.objects.filter(user=self.user, due_date__isnull=False, done=False).order_by("due_date")
        completed_todos = self.model.objects.filter(user=self.user, due_date__isnull=False, done=True).order_by("due_date")

        def group_by_month(todos):
            grouped = {}
            for todo in todos:
                month = todo.due_date.strftime("%B %Y")
                grouped.setdefault(month, []).append(todo)
            return grouped

        return {
            "grouped_pending": group_by_month(pending_todos),
            "grouped_completed": group_by_month(completed_todos),
        }

    def get_monthly_stats(self, now):
        """
        Return stats for the current month (pending vs completed).
        """
        import calendar
        # Get range for current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # simplistic end date: start of next month
        if start_date.month == 12:
            next_month = start_date.replace(year=start_date.year + 1, month=1)
        else:
            next_month = start_date.replace(month=start_date.month + 1)
        
        # Filter todos due in this month (or reminders in this month could be another metric, but due_date is standard)
        month_tasks = self.model.objects.filter(
            user=self.user, 
            due_date__gte=start_date, 
            due_date__lt=next_month
        )
        
        return {
            "total": month_tasks.count(),
            "pending": month_tasks.filter(done=False).count(),
            "completed": month_tasks.filter(done=True).count()
        }

    # ---------------------------
    # Kanban Board
    # ---------------------------

    def get_kanban_board(self):
        """
        Group todos by status for Kanban Board.
        """
        todos = self.model.objects.filter(user=self.user)
        
        return {
            "pending": todos.filter(status=self.model.STATUS_PENDING).order_by("-is_important", "created_at"),
            "in_progress": todos.filter(status=self.model.STATUS_IN_PROGRESS).order_by("-is_important", "created_at"),
            "completed": todos.filter(status=self.model.STATUS_COMPLETED).order_by("-created_at")[:20],  # Limit completed items
        }

    def update_status(self, pk, new_status):
        """
        Update status for Kanban drag-and-drop.
        """
        todo = self.get_by_id(pk)
        
        # Validate status
        valid_statuses = [choice[0] for choice in self.model.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return False, "Invalid status"

        todo.status = new_status
        
        # Sync legacy 'done' field
        todo.done = (new_status == self.model.STATUS_COMPLETED)
        
        todo.save()
        return True, "Status updated"
