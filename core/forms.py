from django import forms
from .models import Note, Todo
from datetime import date
from django.core.exceptions import ValidationError

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content"]

class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ["task", "done", "due_date", "activity", "activity_custom", "reminder", "is_important"]
        widgets = {
            # ensure the HTML date input receives a YYYY-MM-DD formatted value
            "due_date": forms.DateInput(format='%Y-%m-%d', attrs={"type": "date"}),
            "activity": forms.Select(),
            "activity_custom": forms.TextInput(attrs={"placeholder": "Enter custom activity (visible when 'Other' selected)"}),
            # Use datetime-local so browsers show a combined date+time picker
            "reminder": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "is_important": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set a sensible minimum date for the date picker (today)
        try:
            today_iso = date.today().isoformat()
            self.fields['due_date'].widget.attrs.setdefault('min', today_iso)
        except Exception:
            pass

        # If an instance value exists, format it for the date widget (YYYY-MM-DD)
        if self.instance and getattr(self.instance, 'due_date', None):
            try:
                self.initial.setdefault('due_date', self.instance.due_date.strftime('%Y-%m-%d'))
            except Exception:
                # leave as-is if formatting fails
                pass

        # If bound data isn't present, ensure the datetime-local widget displays existing value correctly
        if self.instance and self.instance.reminder:
            # Convert to string matching the widget format (no timezone)
            self.initial.setdefault('reminder', self.instance.reminder.strftime('%Y-%m-%dT%H:%M'))

    def clean_due_date(self):
        """Validate the due_date field: not in the past and reasonable year."""
        due = self.cleaned_data.get('due_date')
        if due:
            # Prevent obviously wrong years (e.g. year 0343 shown in the screenshot)
            if due.year < 1900:
                raise ValidationError('Please provide a valid due date (year must be >= 1900).')
            # Prevent dates in the past
            if due < date.today():
                raise ValidationError('Due date cannot be in the past.')
        return due

    def clean(self):
        cleaned = super().clean()
        activity = cleaned.get('activity')
        activity_custom = cleaned.get('activity_custom') or ''
        # If activity is not custom, clear custom field to avoid stray text
        if activity != Todo.ACTIVITY_OTHER:
            cleaned['activity_custom'] = ''
        else:
            cleaned['activity_custom'] = activity_custom.strip()
        # reminder will be parsed by Django; no extra cleaning needed here
        return cleaned
