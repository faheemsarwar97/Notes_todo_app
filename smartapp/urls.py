from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    
    # Auth
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Notes
    path("notes/", views.notes_list, name="notes_list"),
    path("notes/add/", views.notes_add, name="notes_add"),
    path("notes/<int:id>/", views.notes_detail, name="notes_detail"),
    path("notes/edit/<int:id>/", views.notes_edit, name="notes_edit"),
    path("notes/delete/<int:id>/", views.notes_delete, name="notes_delete"),

    # Todos
    path("todos/", views.todos_list, name="todos_list"),
    path("todos/add/", views.todos_add, name="todos_add"),
    path("todos/<int:id>/", views.todos_detail, name="todos_detail"),
    path("todos/edit/<int:id>/", views.todos_edit, name="todos_edit"),
    path("todos/delete/<int:id>/", views.todos_delete, name="todos_delete"),
    path("todos/check-done/<int:id>/", views.todos_check_done, name="todos_check_done"),
    # Todos calendar
    path("todos/calendar/", views.todos_calendar, name="todos_calendar"),
    # Todos Kanban Status API
    path("todos/update-status/<int:id>/", views.update_todo_status, name="update_todo_status"),

    # Reminders JSON endpoint for live polling
    path("reminders/status/", views.reminders_status, name="reminders_status"),

    # Admin
    path("admin/", admin.site.urls),
]
