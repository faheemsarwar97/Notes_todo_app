import os
import sys
from datetime import timedelta

# Ensure project root is on path
BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartapp.settings')

import django
django.setup()

from django.utils import timezone
from core.models import Todo

# Create a todo with a preset activity
t1 = Todo.objects.create(task='Buy milk', done=False, activity=Todo.ACTIVITY_SHOPPING)
# Create a todo with a custom activity
t2 = Todo.objects.create(task='Plan picnic', done=False, activity=Todo.ACTIVITY_OTHER, activity_custom='Picnic at the lake')
# Create a todo with a reminder (1 day from now)
reminder_time = timezone.now() + timedelta(days=1)
t3 = Todo.objects.create(task='Doctor appointment', done=False, activity=Todo.ACTIVITY_MEETING, reminder=reminder_time)

print('Total todos:', Todo.objects.count())
for t in Todo.objects.all().order_by('created_at'):
    activity_display = (t.activity_custom if (t.activity == Todo.ACTIVITY_OTHER and t.activity_custom) else t.get_activity_display())
    reminder_display = t.reminder.strftime('%Y-%m-%d %H:%M') if t.reminder else 'No reminder'
    print('-', repr(t), '| activity:', activity_display, '| reminder:', reminder_display)

# Cleanup created test todos to avoid leaving test data (optional)
# Uncomment below if you want to remove the created test records after inspection
# t1.delete(); t2.delete(); t3.delete()
