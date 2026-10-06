from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .services import NoteService, TodoService

# ---------------------------
# Auth Views
# ---------------------------

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Login automatically after registration
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

# ---------------------------
# Dashboard
# ---------------------------
@login_required
def dashboard(request):
    todo_service = TodoService(request.user)
    query = request.GET.get("q", "")
    now = timezone.now()

    # Get base stats and search results
    stats = todo_service.get_dashboard_stats(query)

    # Get reminders
    reminders = todo_service.get_reminders(now)

    # Get new features data
    # 1. TODAY'S FOCUS
    today_todos = todo_service.get_daily_focus(now)
    
    # 2. PRIORITY MATRIX
    matrix = todo_service.get_priority_matrix(now)

    # 3. MONTHLY STATS
    monthly_stats = todo_service.get_monthly_stats(now)

    context = {
        "notes_count": stats["notes_count"],
        "todos_count": stats["todos_count"],
        "completed_todos": stats["completed_todos"],
        "query": query,
        "notes_results": stats["notes_results"],
        "todos_results": stats["todos_results"],
        
        "upcoming_reminders": reminders["upcoming"],
        "overdue_reminders": reminders["overdue"],
        "soon_reminders": reminders["soon"],
        "overdue_count": reminders["overdue_count"],
        "soon_count": reminders["soon_count"],
        "show_reminder_alert": (reminders["overdue_count"] > 0) or (reminders["soon_count"] > 0),

        # New features
        "today_todos": today_todos,
        "important_urgent": matrix["important_urgent"],
        "important_not_urgent": matrix["important_not_urgent"],
        "all_important": matrix["all_important"],
        
        "monthly_stats": monthly_stats,
    }
    return render(request, "dashboard.html", context)


@login_required
def reminders_status(request):
    """AJAX endpoint returning JSON with overdue and soon reminders for client polling."""
    todo_service = TodoService(request.user)
    now = timezone.now()
    data = todo_service.get_reminders_status_data(now)
    return JsonResponse(data)


# ---------------------------
# Notes CRUD
# ---------------------------
@login_required
def notes_list(request):
    note_service = NoteService(request.user)
    notes = note_service.list_all()
    return render(request, "notes_list.html", {"notes": notes})

@login_required
def notes_add(request):
    note_service = NoteService(request.user)
    if request.method == "POST":
        success, result = note_service.create(request.POST)
        if success:
            return redirect("notes_list")
        form = result
    else:
        form = note_service.form_class()
    return render(request, "notes_form.html", {"form": form})

@login_required
def notes_detail(request, id):
    note_service = NoteService(request.user)
    note = note_service.get_by_id(id)
    return render(request, "notes_detail.html", {"note": note})

@login_required
def notes_edit(request, id):
    note_service = NoteService(request.user)
    # Retrieve object first to ensure 404 if not found (handled by get_by_id)
    note = note_service.get_by_id(id)
    
    if request.method == "POST":
        success, result = note_service.update(id, request.POST)
        if success:
            return redirect("notes_list")
        form = result
    else:
        form = note_service.form_class(instance=note)
    return render(request, "notes_form.html", {"form": form})

@login_required
def notes_delete(request, id):
    note_service = NoteService(request.user)
    note_service.delete(id)
    return redirect("notes_list")


# ---------------------------
# Todos CRUD
# ---------------------------
@login_required
def todos_list(request):
    todo_service = TodoService(request.user)
    board = todo_service.get_kanban_board()
    return render(request, "todos_list.html", {"board": board})

@login_required
def update_todo_status(request, id):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        new_status = data.get("status")
        
        todo_service = TodoService(request.user)
        success, message = todo_service.update_status(id, new_status)
        
        if success:
            return JsonResponse({"status": "success"})
        return JsonResponse({"status": "error", "message": message}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)

@login_required
def todos_add(request):
    todo_service = TodoService(request.user)
    if request.method == "POST":
        success, result = todo_service.create(request.POST)
        if success:
            return redirect("todos_list")
        form = result
    else:
        form = todo_service.form_class()
    return render(request, "todos_form.html", {"form": form})

@login_required
def todos_detail(request, id):
    todo_service = TodoService(request.user)
    todo = todo_service.get_by_id(id)
    return render(request, "todos_detail.html", {"t": todo})

@login_required
def todos_edit(request, id):
    todo_service = TodoService(request.user)
    todo = todo_service.get_by_id(id)
    if request.method == "POST":
        success, result = todo_service.update(id, request.POST)
        if success:
            return redirect("todos_list")
        form = result
    else:
        form = todo_service.form_class(instance=todo)
    return render(request, "todos_form.html", {"form": form})

@login_required
def todos_delete(request, id):
    todo_service = TodoService(request.user)
    todo_service.delete(id)
    return redirect("todos_list")


# ---------------------------
# Todos Calendar
# ---------------------------
@login_required
def todos_calendar(request):
    todo_service = TodoService(request.user)
    context = todo_service.get_calendar_data()
    return render(request, "todos_calendar.html", context)


@login_required
def todos_check_done(request, id):
    """
    Quickly mark a task as done (and COMPLETED) from the dashboard or list,
    then redirect back to the previous page (dashboard).
    """
    if request.method == "POST":
        todo_service = TodoService(request.user)
        # Using update_status to ensure synchronization logic in service/model is respected
        # although update_status returns (success, msg)
        
        # Simpler approach: fetch and update directly or use service update_status
        # Service update_status requires a string status.
        success, msg = todo_service.update_status(id, "COMPLETED")
        
        # Redirect back to where the user came from, or dashboard default
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
    return redirect('dashboard')