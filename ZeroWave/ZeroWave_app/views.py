from django.shortcuts import render, redirect
from django.conf import settings
from google import genai
from google.genai import types
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import os
import sys
import json
import random
from decimal import Decimal
from datetime import timedelta
from django.utils.timezone import now
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from django.contrib.auth.models import User
from django.contrib.auth import login

from opik import configure 
from opik.integrations.genai import track_genai 

# Load environment variables
load_dotenv()

# Override any existing/global GEMINI_API_KEY
if os.getenv("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.insert(1, './ZeroWave_app')

if os.getenv("GOOGLE_API_KEY"):
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
else:
    client = None

# Opik configuration
if client:
    client = track_genai(client)

from .models import UserProfile, WasteCollection, Redemption, Community, CommunityMember, CarbonListing, ImpactCampaign, WasteRequirement, CollectionTicket

# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    cred_path = settings.BASE_DIR / 'firebase-credentials.json'
    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    else:
        firebase_private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        firebase_client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        if firebase_private_key and firebase_client_email:
            cred_dict = {
                "type": "service_account",
                "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                "private_key": firebase_private_key.replace('\\n', '\n'),
                "client_email": firebase_client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app(options={
                'projectId': os.getenv('FIREBASE_PROJECT_ID'),
            })

def get_firebase_context():
    return {
        'firebase_api_key': os.getenv('FIREBASE_API_KEY', ''),
        'firebase_auth_domain': os.getenv('FIREBASE_AUTH_DOMAIN', ''),
        'firebase_project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
        'firebase_storage_bucket': os.getenv('FIREBASE_STORAGE_BUCKET', ''),
        'firebase_messaging_sender_id': os.getenv('FIREBASE_MESSAGING_SENDER_ID', ''),
        'firebase_app_id': os.getenv('FIREBASE_APP_ID', ''),
    }

# Data Seeding Helpers
def ensure_default_communities():
    pass


def seed_user_history(user, profile):
    if not WasteCollection.objects.filter(user=user).exists():
        categories = ['organic', 'e-waste', 'recyclables', 'agriculture']
        hubs = ['CBD central hub', 'Kibera station', 'Westlands collect', 'Karen green buffer']
        today = now().date()
        
        total_waste = Decimal('0.0')
        total_energy = Decimal('0.0')
        total_tokens = 0
        
        # Create 5 mock collections
        for i in range(1, 6):
            days_ago = 14 - (i * 2)
            c_date = today - timedelta(days=days_ago)
            cat = random.choice(categories)
            weight = Decimal(f"{random.randint(8, 30)}.{random.randint(0, 9)}")
            
            if cat == 'organic':
                energy = weight * Decimal('0.85')
            elif cat == 'agriculture':
                energy = weight * Decimal('0.60')
            else:
                energy = weight * Decimal('0.30')
            
            tokens = int(weight * 10)
            
            col = WasteCollection.objects.create(
                user=user,
                category=cat,
                weight=weight,
                energy_generated=energy,
                tokens_earned=tokens,
                hub_name=random.choice(hubs),
                status=random.choice(['Empty', 'Pre-Occupied'])
            )
            # update the historical date directly
            WasteCollection.objects.filter(id=col.id).update(date=c_date)
            
            total_waste += weight
            total_energy += energy
            total_tokens += tokens
            
        # Create 2 mock redemptions
        Redemption.objects.create(
            user=user,
            reward_name='Basi Go Discount',
            tokens_spent=500,
            phone_number=profile.phone_number or '0712345678',
            status='success'
        )
        Redemption.objects.create(
            user=user,
            reward_name='Pay Go',
            tokens_spent=300,
            phone_number=profile.phone_number or '0712345678',
            status='success'
        )
        total_tokens = max(0, total_tokens - 800)
        
        profile.tokens_balance = total_tokens
        profile.total_waste_recycled = total_waste
        profile.total_energy_generated = total_energy
        profile.carbon_credits = int(total_waste / 20)
        profile.trees_planted = int(total_waste / 50)
        profile.save()

def get_active_profile(request):
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'household_id': f"ZW-2026-{random.randint(1000, 9999)}",
                'phone_number': '0712345678',
                'tokens_balance': 0  # Starts with 0 tokens for a fresh profile
            }
        )
        ensure_default_communities()
        return profile
    return None

# Core Views
def home(request):
    return render(request, 'index.html')

def registration(request):
    context = get_firebase_context()
    return render(request, 'registration.html', context)

def signin(request):
    context = get_firebase_context()
    return render(request, 'signin.html', context)

def bank_dashboard(request, profile):
    requirements = WasteRequirement.objects.filter(bank=request.user).order_by('-created_at')
    
    # Recent collections verified by this bank
    collections = WasteCollection.objects.filter(hub_name=profile.bank_name or request.user.username).order_by('-date')[:10]
    
    total_collected = sum(c.weight for c in collections)
    total_tokens_issued = sum(c.tokens_earned for c in collections)
    active_req_count = requirements.filter(status='Active').count()
    
    # Pickup tickets for this bank
    available_tickets = CollectionTicket.objects.filter(status='pending', region=profile.region).order_by('-created_at')
    claimed_tickets = CollectionTicket.objects.filter(status='assigned', assigned_bank=request.user).order_by('-created_at')
    
    context = {
        'profile': profile,
        'requirements': requirements,
        'collections': collections,
        'total_collected': total_collected,
        'total_tokens_issued': total_tokens_issued,
        'active_req_count': active_req_count,
        'categories': WasteCollection.CATEGORIES,
        'available_tickets': available_tickets,
        'claimed_tickets': claimed_tickets,
    }
    return render(request, 'bank_dashboard.html', context)

@login_required(login_url='signin')
def dashboard(request):
    profile = get_active_profile(request)
    if profile.role == 'bank':
        return bank_dashboard(request, profile)
    
    collections = WasteCollection.objects.filter(user=request.user).order_by('-date')[:5]
    redemptions = Redemption.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Merge activities for recent activity table
    activities = []
    for c in collections:
        activities.append({
            'date': c.date.strftime('%Y-%m-%d'),
            'action': 'Waste Dropped Off',
            'category': c.category.capitalize(),
            'tokens': f"+{c.tokens_earned}",
            'status': 'success'
        })
    for r in redemptions:
        activities.append({
            'date': r.date.strftime('%Y-%m-%d'),
            'action': f"Redeemed {r.reward_name}",
            'category': 'Reward',
            'tokens': f"-{r.tokens_spent}",
            'status': r.status
        })
    activities = sorted(activities, key=lambda x: x['date'], reverse=True)[:5]
    
    # Calculate monthly data for past 6 months
    today = now().date()
    months_labels = []
    organic_data = [0.0]*6
    ewaste_data = [0.0]*6
    recyclables_data = [0.0]*6
    agriculture_data = [0.0]*6
    
    for i in range(5, -1, -1):
        target_date = today - timedelta(days=i*30)
        months_labels.append(target_date.strftime('%b'))
        
    user_collections = WasteCollection.objects.filter(user=request.user)
    
    pie_data = [0.0, 0.0, 0.0, 0.0]
    for col in user_collections:
        cat = col.category.lower()
        w = float(col.weight)
        if cat == 'organic': pie_data[0] += w
        elif cat == 'e-waste': pie_data[1] += w
        elif cat == 'recyclables': pie_data[2] += w
        elif cat == 'agriculture': pie_data[3] += w
        
        col_month = col.date.strftime('%b')
        if col_month in months_labels:
            m_idx = months_labels.index(col_month)
            if cat == 'organic': organic_data[m_idx] += w
            elif cat == 'e-waste': ewaste_data[m_idx] += w
            elif cat == 'recyclables': recyclables_data[m_idx] += w
            elif cat == 'agriculture': agriculture_data[m_idx] += w
            
    active_requirements = WasteRequirement.objects.filter(status='Active', bank__profile__region=profile.region).order_by('-created_at')[:8]
    tickets = CollectionTicket.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'profile': profile,
        'activities': activities,
        'months_labels': months_labels,
        'organic_data': organic_data,
        'ewaste_data': ewaste_data,
        'recyclables_data': recyclables_data,
        'agriculture_data': agriculture_data,
        'pie_data': pie_data,
        'active_requirements': active_requirements,
        'tickets': tickets,
        'categories': WasteCollection.CATEGORIES,
        'regions': Community.REGIONS,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='signin')
def settings(request):
    profile = get_active_profile(request)
    context = {
        'profile': profile,
    }
    return render(request, 'settings.html', context)

@login_required(login_url='signin')
def rewards(request):
    profile = get_active_profile(request)
    campaigns = ImpactCampaign.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'profile': profile,
        'campaigns': campaigns,
    }
    return render(request, 'rewards.html', context)

@login_required(login_url='signin')
def impact(request):
    profile = get_active_profile(request)
    context = {
        'profile': profile,
    }
    return render(request, 'impact.html', context)

@login_required(login_url='signin')
def analytics(request):
    profile = get_active_profile(request)
    collections = WasteCollection.objects.filter(user=request.user).order_by('date')
    
    days = []
    waste_kg = []
    energy_kwh = []
    tokens_issued = []
    
    comp = {'organic': 0.0, 'e-waste': 0.0, 'recyclables': 0.0, 'agriculture': 0.0, 'other': 0.0}
    
    for c in collections:
        days.append(c.date.strftime('%Y-%m-%d'))
        waste_kg.append(float(c.weight))
        energy_kwh.append(float(c.energy_generated))
        tokens_issued.append(c.tokens_earned)
        cat_key = c.category.lower()
        if cat_key in comp:
            comp[cat_key] += float(c.weight)
            
    hubs = []
    db_hubs = Community.objects.all().order_by('-points')[:5]
    for dh in db_hubs:
        hubs.append({
            'name': dh.name,
            'kg': float(dh.diverted_kg),
            'credits': dh.credits
        })
        
    anomalies = [
        {
            'hub': 'Delhi Metro Recycling Hub',
            'desc': 'Unusually high organic waste volume detected',
            'date': '2026-06-07',
            'status': 'Fully Occupied'
        },
        {
            'hub': 'Bengaluru Clean Hub',
            'desc': 'Smart bin offline alert',
            'date': '2026-06-06',
            'status': 'Pre-Occupied'
        }
    ]
    
    events = []
    all_collections = WasteCollection.objects.filter(user=request.user).order_by('-date')[:5]
    all_redemptions = Redemption.objects.filter(user=request.user).order_by('-date')[:5]
    
    for c in all_collections:
        events.append({
            'desc': f"Recycled {c.weight} kg at {c.hub_name}",
            'time': c.date.strftime('%b %d, %Y'),
            'amt': c.tokens_earned
        })
    for r in all_redemptions:
        events.append({
            'desc': f"Redeemed {r.reward_name}",
            'time': r.date.strftime('%b %d, %Y'),
            'amt': -r.tokens_spent
        })
    events = sorted(events, key=lambda x: x['time'], reverse=True)[:5]
    
    # Query hubs locations for the Leaflet map
    db_communities = Community.objects.all()
    locations = []
    for c in db_communities:
        locations.append({
            'neighbourhood': c.name,
            'type': c.category.capitalize(),
            'status': 'Fully Occupied' if c.diverted_kg > 1000 else ('Pre-Occupied' if c.diverted_kg > 100 else 'Empty'),
            'weight': float(c.diverted_kg),
            'lat': float(c.lat),
            'lng': float(c.lng)
        })

    context = {
        'profile': profile,
        'days': json.dumps(days),
        'wasteKg': json.dumps(waste_kg),
        'energyKwh': json.dumps(energy_kwh),
        'tokensIssued': json.dumps(tokens_issued),
        'comp': json.dumps(comp),
        'hubs': json.dumps(hubs),
        'anomalies': json.dumps(anomalies),
        'events': json.dumps(events),
        'locations_json': json.dumps(locations)
    }
    return render(request, 'analytics.html', context)

@login_required(login_url='signin')
def nearby(request):
    profile = get_active_profile(request)
    db_communities = Community.objects.all()
    
    locations = []
    for c in db_communities:
        locations.append({
            'city': c.name,
            'county': capitalize(c.region),
            'lat': float(c.lat),
            'lng': float(c.lng),
            'weight': float(c.diverted_kg),
            'status': 'Fully Occupied' if c.diverted_kg > 1000 else ('Pre-Occupied' if c.diverted_kg > 100 else 'Empty'),
            'type': c.category.capitalize()
        })
        
    context = {
        'profile': profile,
        'locations_json': json.dumps(locations)
    }
    return render(request, 'nearby.html', context)

@login_required(login_url='signin')
def community(request):
    profile = get_active_profile(request)
    db_communities = Community.objects.all()
    
    communities = []
    for c in db_communities:
        communities.append({
            'id': f"c_{c.id}",
            'name': c.name,
            'region': c.region,
            'category': c.category,
            'tagline': c.tagline,
            'desc': c.description,
            'verified': c.verified,
            'members': c.members_count,
            'points': c.points,
            'credits': c.credits,
            'divertedKg': float(c.diverted_kg),
            'energyKwh': float(c.energy_kwh),
            'lat': float(c.lat),
            'lng': float(c.lng),
            'leadApplicant': c.lead_applicant_uid is not None,
            'impact': [f"{c.diverted_kg} kg waste diverted", f"{c.energy_kwh} kWh biogas generated"],
            'events': [{'title': 'Tree planting buffer day', 'date': '2026-06-15'}],
            'membersList': ['Alice', 'Bob', 'Charlie']
        })
        
    user_joined = [f"c_{membership.community.id}" for membership in request.user.memberships.all()]
    user_following = [] # simulated following
    
    context = {
        'profile': profile,
        'communities_json': json.dumps(communities),
        'user_joined_json': json.dumps(user_joined),
        'user_following_json': json.dumps(user_following)
    }
    return render(request, 'community.html', context)

# API Endpoints
@csrf_exempt
@require_POST
def firebase_auth_view(request):
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
        except Exception as e:
            if "used too early" in str(e).lower():
                import time
                time.sleep(2)
                decoded_token = firebase_auth.verify_id_token(id_token)
            else:
                raise e
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        
        role = data.get('role', 'user')
        bank_name = data.get('bankName', '')
        region = data.get('region', '')
        phone = data.get('phone', '')

        # Check for email conflicts with different accounts (e.g. registered under different UID)
        if email:
            existing_user = User.objects.filter(email=email).exclude(username=uid).first()
            if existing_user:
                has_profile = hasattr(existing_user, 'profile')
                existing_role = existing_user.profile.role if has_profile else 'user'
                role_display = "Individual User" if existing_role == 'user' else "Waste Collection Bank"
                return JsonResponse({
                    'status': 'error',
                    'message': f'The email {email} is already registered as an {role_display}. Please use a different email or sign in with the correct option.'
                }, status=400)

        # Get or create user
        user, created = User.objects.get_or_create(username=uid, defaults={'email': email})

        # Check for profile and validate role matching
        profile_exists = UserProfile.objects.filter(user=user).exists()
        if profile_exists:
            profile = UserProfile.objects.get(user=user)
            if profile.role != role:
                role_display = "Individual User" if profile.role == 'user' else "Waste Collection Bank"
                target_role_display = "Individual User" if role == 'user' else "Waste Collection Bank"
                return JsonResponse({
                    'status': 'error',
                    'message': f'This account is registered as an {role_display}. You cannot log in or register as a {target_role_display}.'
                }, status=400)
            
            # Update info if matches
            if bank_name and role == 'bank':
                profile.bank_name = bank_name
            if region:
                profile.region = region
            if phone:
                profile.phone_number = phone
            profile.save()
        else:
            # Create a brand new profile
            id_prefix = "ZW-BANK" if role == "bank" else "ZW-2026"
            profile = UserProfile.objects.create(
                user=user,
                firebase_uid=uid,
                household_id=f"{id_prefix}-{random.randint(1000, 9999)}",
                tokens_balance=0,  # All profiles start with 0 tokens for a fresh start
                role=role,
                bank_name=bank_name if role == 'bank' else '',
                region=region,
                phone_number=phone
            )
        
        ensure_default_communities()

        # Log the user in
        login(request, user)

        return JsonResponse({'status': 'success'})
    except Exception as e:
        print(f"Firebase auth error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        if user_message:
            bot_reply = get_gemini_response(user_message)
            try:
                opik_response = opik_gemini_agent(user_message)
            except Exception as e:
                print(f"Opik agent failed: {e}")
            return JsonResponse({'response': bot_reply})
        else:
            return JsonResponse({'response': "Sorry, I didn't catch that."}, status=400)

@login_required
@require_POST
def api_redeem(request):
    try:
        data = json.loads(request.body)
        reward_name = data.get('reward_name')
        tokens_spent = int(data.get('tokens_spent', 0))
        phone_number = data.get('phone_number')
        
        profile = request.user.profile
        if profile.tokens_balance < tokens_spent:
            return JsonResponse({'status': 'error', 'message': 'Insufficient token balance'}, status=400)
            
        profile.tokens_balance -= tokens_spent
        profile.save()
        
        Redemption.objects.create(
            user=request.user,
            reward_name=reward_name,
            tokens_spent=tokens_spent,
            phone_number=phone_number,
            status='success'
        )
        return JsonResponse({'status': 'success', 'new_balance': profile.tokens_balance})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_create_campaign(request):
    try:
        data = json.loads(request.body)
        title = data.get('title')
        campaign_type = data.get('campaign_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        description = data.get('description')
        
        campaign = ImpactCampaign.objects.create(
            user=request.user,
            title=title,
            campaign_type=campaign_type,
            start_date=start_date,
            end_date=end_date,
            description=description
        )
        return JsonResponse({
            'status': 'success',
            'campaign': {
                'id': campaign.id,
                'title': campaign.title,
                'campaign_type': campaign.campaign_type,
                'start_date': campaign.start_date.strftime('%Y-%m-%d'),
                'end_date': campaign.end_date.strftime('%Y-%m-%d'),
                'description': campaign.description,
                'status': campaign.status
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_community_join(request):
    try:
        data = json.loads(request.body)
        raw_id = data.get('community_id')
        db_id = int(raw_id.replace('c_', ''))
        
        community = Community.objects.get(id=db_id)
        membership = CommunityMember.objects.filter(community=community, user=request.user)
        
        if membership.exists():
            membership.delete()
            community.members_count = max(0, community.members_count - 1)
            action = 'left'
        else:
            CommunityMember.objects.create(community=community, user=request.user)
            community.members_count += 1
            action = 'joined'
            
        community.save()
        return JsonResponse({'status': 'success', 'action': action, 'members_count': community.members_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_community_apply_lead(request):
    try:
        data = json.loads(request.body)
        raw_id = data.get('community_id')
        db_id = int(raw_id.replace('c_', ''))
        
        community = Community.objects.get(id=db_id)
        community.lead_applicant_uid = request.user.username
        community.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_community_create(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        region = data.get('region')
        category = data.get('category')
        description = data.get('description')
        
        # Geolocation randomized around the selected Indian city center
        city_coords = {
            'delhi': (28.6139, 77.2090),
            'mumbai': (19.0760, 72.8777),
            'bengaluru': (12.9716, 77.5946),
            'hyderabad': (17.3850, 78.4867),
            'chennai': (13.0827, 80.2707),
            'kolkata': (22.5726, 88.3639),
            'pune': (18.5204, 73.8567),
        }
        base_lat, base_lng = city_coords.get(region, (12.9716, 77.5946))
        lat = Decimal(f"{base_lat}") + Decimal(f"{random.uniform(-0.05, 0.05)}")
        lng = Decimal(f"{base_lng}") + Decimal(f"{random.uniform(-0.05, 0.05)}")
        
        c = Community.objects.create(
            name=name,
            region=region,
            category=category,
            description=description,
            tagline=description[:60],
            creator=request.user,
            lat=lat,
            lng=lng,
            members_count=1
        )
        # Add creator as member
        CommunityMember.objects.create(community=c, user=request.user, role='Lead')
        
        return JsonResponse({
            'status': 'success',
            'community': {
                'id': f"c_{c.id}",
                'name': c.name,
                'region': c.region,
                'category': c.category,
                'tagline': c.tagline,
                'desc': c.description,
                'verified': c.verified,
                'members': c.members_count,
                'points': c.points,
                'credits': c.credits,
                'divertedKg': float(c.diverted_kg),
                'energyKwh': float(c.energy_kwh),
                'lat': float(c.lat),
                'lng': float(c.lng)
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_marketplace_trade(request):
    try:
        data = json.loads(request.body)
        trade_type = data.get('type') # buy, sell
        amount = int(data.get('amount', 0))
        
        profile = request.user.profile
        if trade_type == 'buy':
            cost = amount * 40
            # Check balance (if simulated payment works, I just deduct tokens from profile or let them buy)
            profile.tokens_balance += amount
            profile.save()
            
            CarbonListing.objects.create(
                user=request.user,
                amount=amount,
                price_per_credit=Decimal('40.0'),
                status='sold'
            )
            return JsonResponse({'status': 'success', 'new_balance': profile.tokens_balance})
        elif trade_type == 'sell':
            if profile.tokens_balance < amount:
                return JsonResponse({'status': 'error', 'message': 'Insufficient token balance to list for sale'}, status=400)
                
            profile.tokens_balance -= amount
            profile.save()
            
            CarbonListing.objects.create(
                user=request.user,
                amount=amount,
                price_per_credit=Decimal('35.0'),
                status='active'
            )
            return JsonResponse({'status': 'success', 'new_balance': profile.tokens_balance})
            
        return JsonResponse({'status': 'error', 'message': 'Invalid trade type'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def api_settings_update(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        household_id = data.get('household_id')
        bank_name = data.get('bank_name')
        region = data.get('region')
        
        # Update User
        user = request.user
        user.email = email
        if full_name:
            names = full_name.split(' ', 1)
            user.first_name = names[0]
            if len(names) > 1:
                user.last_name = names[1]
        user.save()
        
        # Update Profile
        profile = user.profile
        profile.phone_number = phone
        if region:
            profile.region = region
        if profile.role == 'bank':
            if bank_name:
                profile.bank_name = bank_name
        else:
            if household_id:
                profile.household_id = household_id
        profile.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# Local Fallback Chatbot
def _get_local_fallback_response(prompt: str, reason: str = "expired") -> str:
    msg = prompt.lower().strip()
    if not msg:
        return "Hello! How can I help you today?"
        
    if any(greet in msg for greet in ["hello", "hi", "hey", "jambo", "habari", "good morning", "good afternoon", "good evening", "greetings", "good day", "yo"]):
        greeting_reply = "Hello"
        if "good morning" in msg:
            greeting_reply = "Good morning"
        elif "good afternoon" in msg:
            greeting_reply = "Good afternoon"
        elif "good evening" in msg:
            greeting_reply = "Good evening"
        return f"{greeting_reply}! I am ZeroWave AI Assistant. I can help you with ZeroWave, waste management, and renewable energy topics. How can I assist you today?"
    elif "how are you" in msg:
        return "I am doing great, thank you! I'm ready to help you save the planet and manage ZeroTokens."
    elif "token" in msg:
        return "ZeroTokens are earned by dropping off sorted waste at ZeroWave hubs. You can redeem them for rewards like Koko Fuel, KPLC tokens, and solar lights."
    elif "waste" in msg or "recycle" in msg or "drop" in msg:
        return "You can drop off sorted waste (organic, plastic, metals, e-waste) at any ZeroWave hubs to earn ZeroTokens."
    elif "hub" in msg or "station" in msg or "nearby" in msg:
        return "You can find nearby ZeroWave collection points and community hubs on the 'Nearby' map."
    elif "solar" in msg:
        return "Solar energy systems are highly recommended in East Africa. ZeroWave partner rewards include subsidized solar installations and SunKing solar lights."
    elif "energy" in msg or "power" in msg:
        return "ZeroWave converts waste into energy using technologies like anaerobic digestion to produce biogas and organic fertilizers. You earn ZeroTokens for contributing!"
    else:
        reason_str = "is expired"
        if reason == "quota_exceeded":
            reason_str = "has exceeded its quota / billing limits"
        elif reason == "invalid_key":
            reason_str = "is invalid"
        elif reason == "not_configured":
            reason_str = "is not configured"
        return f"Thank you for your message! I'm currently running in local backup mode (since the Google Gemini API key {reason_str}). Ask me about ZeroTokens, recycling hubs, or energy transformation!"

def get_gemini_response(prompt):
    if not client:
        return _get_local_fallback_response(prompt, reason="not_configured")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="""
                    You are ZeroWave AI Assistant, an intelligent sustainability and green innovation expert designed to educate, guide, 
                    and support users in topics related to energy transformation, waste management, and environmental conservation.
                    Core Focus Areas: Waste-to-energy, renewable energy, solar energy, carbon credits, and environmental conservation.
                    Tone: Professional, inspiring, and concise.
                """,
                max_output_tokens=1000,
                top_k=2,
                top_p=0.5,
                temperature=0.9,
                seed=42,
            ),
        )
        return response.text
    except Exception as e:
        print(f"Gemini API call failed, using local backup response: {e}")
        err_str = str(e).lower()
        reason = "expired"
        if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
            reason = "quota_exceeded"
        elif "invalid" in err_str or "key not found" in err_str:
            reason = "invalid_key"
        return _get_local_fallback_response(prompt, reason=reason)

def opik_gemini_agent(prompt: str):
    if not client:
        return "Gemini client not initialized"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Opik client generate_content failed: {e}")
        return "Opik client failed"

def capitalize(s):
    if not s: return ''
    return s[0].toUpperCase() + s[1:] if hasattr(s, 'toUpperCase') else s.capitalize()


# Bank Dashboard API Views

@login_required
def api_bank_validate_user(request):
    user_id = request.GET.get('user_id', '').strip()
    try:
        target_profile = UserProfile.objects.get(household_id=user_id, role='user')
        return JsonResponse({
            'status': 'success',
            'username': target_profile.user.username,
            'name': f"{target_profile.user.first_name} {target_profile.user.last_name}".strip() or target_profile.user.email,
            'email': target_profile.user.email,
            'phone': target_profile.phone_number
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid Member ID or User not found.'}, status=404)


@login_required
@require_POST
@csrf_exempt
def api_bank_record_collection(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', '').strip()
        category = data.get('category', '').strip()
        weight = Decimal(str(data.get('weight', 0)))
        
        if weight <= 0:
            return JsonResponse({'status': 'error', 'message': 'Weight must be greater than 0.'}, status=400)
            
        try:
            target_profile = UserProfile.objects.get(household_id=user_id, role='user')
        except UserProfile.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User profile not found.'}, status=404)
            
        bank_profile = request.user.profile
        if bank_profile.role != 'bank':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized. Only Waste Collection Banks can log drop-offs.'}, status=403)
            
        # Check active requirement
        req = WasteRequirement.objects.filter(bank=request.user, category=category, status='Active').first()
        rate = req.tokens_per_kg if req else 10  # Default rate is 10 tokens per kg
        
        tokens_earned = int(weight * rate)
        
        # Calculate simulated energy generated
        if category == 'organic':
            energy = weight * Decimal('0.85')
        elif category == 'agriculture':
            energy = weight * Decimal('0.60')
        elif category == 'plastic':
            energy = weight * Decimal('0.40')
        else:
            energy = weight * Decimal('0.30')
            
        col = WasteCollection.objects.create(
            user=target_profile.user,
            category=category,
            weight=weight,
            energy_generated=energy,
            tokens_earned=tokens_earned,
            hub_name=bank_profile.bank_name or request.user.username,
            status='Pre-Occupied'
        )
        
        target_profile.tokens_balance += tokens_earned
        target_profile.total_waste_recycled += weight
        target_profile.total_energy_generated += energy
        target_profile.carbon_credits = int(target_profile.total_waste_recycled / 20)
        target_profile.trees_planted = int(target_profile.total_waste_recycled / 50)
        target_profile.save()
        
        if req:
            req.quantity_collected += weight
            if req.quantity_collected >= req.quantity_required:
                req.status = 'Completed'
            req.save()
            
        return JsonResponse({
            'status': 'success',
            'tokens_earned': tokens_earned,
            'user_name': f"{target_profile.user.first_name} {target_profile.user.last_name}".strip() or target_profile.user.email,
            'new_balance': target_profile.tokens_balance
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def api_bank_create_requirement(request):
    try:
        bank_profile = request.user.profile
        if bank_profile.role != 'bank':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized. Only Banks can post requirements.'}, status=403)
            
        data = json.loads(request.body)
        category = data.get('category', '').strip()
        quantity_required = Decimal(str(data.get('quantity_required', 0)))
        tokens_per_kg = int(data.get('tokens_per_kg', 10))
        
        if quantity_required <= 0:
            return JsonResponse({'status': 'error', 'message': 'Quantity required must be greater than 0.'}, status=400)
            
        req = WasteRequirement.objects.create(
            bank=request.user,
            category=category,
            quantity_required=quantity_required,
            tokens_per_kg=tokens_per_kg,
            status='Active'
        )
        
        return JsonResponse({
            'status': 'success',
            'requirement': {
                'id': req.id,
                'category': req.get_category_display(),
                'quantity_required': float(req.quantity_required),
                'tokens_per_kg': req.tokens_per_kg,
                'status': req.status
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def api_bank_delete_requirement(request, req_id):
    try:
        req = WasteRequirement.objects.get(id=req_id, bank=request.user)
        req.delete()
        return JsonResponse({'status': 'success'})
    except WasteRequirement.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Requirement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Collection Tickets API Views

@login_required
@require_POST
@csrf_exempt
def api_create_ticket(request):
    try:
        profile = request.user.profile
        if profile.role != 'user':
            return JsonResponse({'status': 'error', 'message': 'Only standard users can raise pickup tickets.'}, status=403)
            
        data = json.loads(request.body)
        category = data.get('category', '').strip()
        estimated_weight = Decimal(str(data.get('estimated_weight', 0)))
        region = data.get('region', '').strip()
        address = data.get('address', '').strip()
        phone_number = data.get('phone_number', '').strip() or profile.phone_number or ''
        
        if estimated_weight <= 0:
            return JsonResponse({'status': 'error', 'message': 'Estimated weight must be greater than 0.'}, status=400)
        if not address:
            return JsonResponse({'status': 'error', 'message': 'Pickup address is required.'}, status=400)
        if not region:
            return JsonResponse({'status': 'error', 'message': 'Region is required.'}, status=400)
            
        ticket = CollectionTicket.objects.create(
            user=request.user,
            category=category,
            estimated_weight=estimated_weight,
            region=region,
            address=address,
            phone_number=phone_number,
            status='pending'
        )
        
        return JsonResponse({
            'status': 'success',
            'ticket': {
                'id': ticket.id,
                'category': ticket.get_category_display(),
                'estimated_weight': float(ticket.estimated_weight),
                'region': ticket.get_region_display(),
                'address': ticket.address,
                'phone_number': ticket.phone_number,
                'status': ticket.get_status_display(),
                'created_at': ticket.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def api_claim_ticket(request, ticket_id):
    try:
        bank_profile = request.user.profile
        if bank_profile.role != 'bank':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized. Only Waste Collection Banks can claim tickets.'}, status=403)
            
        ticket = CollectionTicket.objects.get(id=ticket_id, status='pending')
        ticket.assigned_bank = request.user
        ticket.status = 'assigned'
        ticket.save()
        
        return JsonResponse({'status': 'success'})
    except CollectionTicket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found or already claimed.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def api_complete_ticket_pickup(request, ticket_id):
    try:
        bank_profile = request.user.profile
        if bank_profile.role != 'bank':
            return JsonResponse({'status': 'error', 'message': 'Unauthorized. Only Waste Collection Banks can complete pickups.'}, status=403)
            
        ticket = CollectionTicket.objects.get(id=ticket_id, assigned_bank=request.user, status='assigned')
        
        data = json.loads(request.body)
        actual_weight = Decimal(str(data.get('actual_weight', 0)))
        
        if actual_weight <= 0:
            return JsonResponse({'status': 'error', 'message': 'Actual weight must be greater than 0.'}, status=400)
            
        req = WasteRequirement.objects.filter(bank=request.user, category=ticket.category, status='Active').first()
        rate = req.tokens_per_kg if req else 10
        
        tokens_earned = int(actual_weight * rate)
        
        if ticket.category == 'organic':
            energy = actual_weight * Decimal('0.85')
        elif ticket.category == 'agriculture':
            energy = actual_weight * Decimal('0.60')
        elif ticket.category == 'plastic':
            energy = actual_weight * Decimal('0.40')
        else:
            energy = actual_weight * Decimal('0.30')
            
        col = WasteCollection.objects.create(
            user=ticket.user,
            category=ticket.category,
            weight=actual_weight,
            energy_generated=energy,
            tokens_earned=tokens_earned,
            hub_name=bank_profile.bank_name or request.user.username,
            status='Pre-Occupied'
        )
        
        target_profile = ticket.user.profile
        target_profile.tokens_balance += tokens_earned
        target_profile.total_waste_recycled += actual_weight
        target_profile.total_energy_generated += energy
        target_profile.carbon_credits = int(target_profile.total_waste_recycled / 20)
        target_profile.trees_planted = int(target_profile.total_waste_recycled / 50)
        target_profile.save()
        
        if req:
            req.quantity_collected += actual_weight
            if req.quantity_collected >= req.quantity_required:
                req.status = 'Completed'
            req.save()
            
        ticket.status = 'completed'
        ticket.save()
        
        return JsonResponse({
            'status': 'success',
            'tokens_earned': tokens_earned,
            'user_name': f"{ticket.user.first_name} {ticket.user.last_name}".strip() or ticket.user.email,
            'new_balance': target_profile.tokens_balance
        })
    except CollectionTicket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found or not assigned to this bank.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
@csrf_exempt
def api_cancel_ticket(request, ticket_id):
    try:
        profile = request.user.profile
        if profile.role == 'bank':
            ticket = CollectionTicket.objects.get(id=ticket_id, assigned_bank=request.user, status='assigned')
        else:
            ticket = CollectionTicket.objects.get(id=ticket_id, user=request.user)
            if ticket.status in ['completed', 'cancelled']:
                return JsonResponse({'status': 'error', 'message': 'Cannot cancel a completed or already cancelled ticket.'}, status=400)
                
        ticket.status = 'cancelled'
        ticket.save()
        
        return JsonResponse({'status': 'success'})
    except CollectionTicket.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ticket not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
