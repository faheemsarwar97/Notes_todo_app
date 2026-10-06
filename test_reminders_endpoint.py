import os
import sys
import json

BASE_DIR = os.path.dirname(__file__)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartapp.settings')
import django
django.setup()

from django.test import Client

c = Client()
# Provide a valid host to avoid DisallowedHost in test client
resp = c.get('/reminders/status/', HTTP_HOST='127.0.0.1')
print('STATUS:', resp.status_code)
try:
    data = resp.json()
    print(json.dumps(data, indent=2))
except Exception as e:
    print('Error parsing JSON:', e)
    print(resp.content)
