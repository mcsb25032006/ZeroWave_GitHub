import os
import django
import sys

# Set up django environment
sys.path.insert(0, 'c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/ZeroWave')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZeroWave.settings')
django.setup()

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from django.conf import settings

print("Checking firebase initialization...")
try:
    cred_path = settings.BASE_DIR / 'firebase-credentials.json'
    print("Certificate path exists:", cred_path.exists())
    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        app = firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK successfully initialized!", app.name)
except Exception as e:
    print("Firebase initialization error:", e)
