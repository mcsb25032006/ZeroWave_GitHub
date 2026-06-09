import os
import sys
import django

# Set up Django context
sys.path.insert(0, 'c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/ZeroWave')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZeroWave.settings')
django.setup()

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from django.contrib.auth.models import User
from django.conf import settings
from ZeroWave_app.models import (
    UserProfile, WasteCollection, Redemption, Community, 
    CommunityMember, CarbonListing, ImpactCampaign, WasteRequirement
)

# 1. Initialize Firebase Admin SDK
print("Initializing Firebase...")
cred_path = settings.BASE_DIR / 'firebase-credentials.json'
if cred_path.exists():
    cred = credentials.Certificate(str(cred_path))
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass  # Already initialized
else:
    print("Error: firebase-credentials.json not found!")
    sys.exit(1)

# 2. Delete all users from Firebase Auth
print("Fetching Firebase users...")
firebase_uids = []
try:
    page = firebase_auth.list_users()
    while page:
        for user in page.users:
            firebase_uids.append(user.uid)
        page = page.get_next_page()
    
    print(f"Found {len(firebase_uids)} users in Firebase.")
    if firebase_uids:
        print("Deleting users from Firebase Auth...")
        result = firebase_auth.delete_users(firebase_uids)
        print(f"Successfully deleted {result.success_count} Firebase users.")
        if result.failure_count > 0:
            print(f"Failed to delete {result.failure_count} Firebase users.")
            for err in result.errors:
                print(f" - Error details: {err.reason}")
except Exception as e:
    print("Error managing Firebase users:", e)

# 3. Clean Django Database
print("Cleaning Django database tables...")
try:
    # Delete related models first
    print("Deleting Waste requirements...")
    WasteRequirement.objects.all().delete()
    
    print("Deleting Impact Campaigns...")
    ImpactCampaign.objects.all().delete()
    
    print("Deleting Carbon Listings...")
    CarbonListing.objects.all().delete()
    
    print("Deleting Redemptions...")
    Redemption.objects.all().delete()
    
    print("Deleting Waste Collections...")
    WasteCollection.objects.all().delete()
    
    print("Deleting Community Members...")
    CommunityMember.objects.all().delete()
    
    print("Deleting Communities...")
    Community.objects.all().delete()
    
    print("Deleting User Profiles...")
    UserProfile.objects.all().delete()
    
    # Delete users (excluding superusers)
    print("Deleting Django User records (excluding superusers)...")
    non_superusers = User.objects.filter(is_superuser=False)
    count = non_superusers.count()
    non_superusers.delete()
    print(f"Deleted {count} Django user accounts.")
    
    print("🎉 Database successfully cleared and reset to fresh state!")
except Exception as e:
    print("Database cleaning error:", e)
