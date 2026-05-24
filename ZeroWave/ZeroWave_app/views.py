from django.shortcuts import render
from django.conf import settings
# import google.generativeai as genai # deprecated version
from google import genai
from google.genai import types
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os
import sys
import json
import africastalking
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from django.contrib.auth.models import User
from django.contrib.auth import login




from opik import configure 
from opik.integrations.genai import track_genai 

# configure()



load_dotenv()

# Override any existing/global GEMINI_API_KEY to match the updated GOOGLE_API_KEY from .env
if os.getenv("GOOGLE_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.insert(1, './ZeroWave_app')

if os.getenv("GOOGLE_API_KEY"):
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
else:
    client = None

if os.getenv("AT_API_KEY"):
    africastalking.initialize(
        username="EMID",
        api_key=os.getenv("AT_API_KEY")
    )



"""

Opik Configuration for Gemini AI Model

"""

# os.environ["GEMINI_API_KEY"] = "your-api-key-here"

# opik_client = google.genai.Client()
if client:
    client = track_genai(client)


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

def get_gemini_response(prompt):
    if not client:
        return _get_local_fallback_response(prompt, reason="not_configured")

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=
                
                    """
                    
                    You are ZeroWave AI Assistant, an intelligent sustainability and green innovation expert designed to educate, guide, 
                    and support users in topics related to energy transformation, waste management, and environmental conservation.

                    Core Focus Areas:
                        - Your primary domains of expertise include:
                        - Waste-to-energy technologies (biogas, pyrolysis, gasification, anaerobic digestion)
                        - Renewable energy (solar, wind, hydro, geothermal, biomass)
                        - Solar energy systems (installation, maintenance, costs, ROI, off-grid vs on-grid)
                        - EV charging infrastructure (deployment, usage, benefits, network optimization)
                        - Energy storage (battery technologies, grid integration, optimization)
                        - Circular economy and waste recycling
                        - Smart energy grids and IoT in energy management
                        - Carbon credits, offset systems, and sustainability finance
                        - Environmental conservation (deforestation, water, biodiversity, waste reduction)
                        - ESG principles and climate change mitigation strategies
                        - Green policies and innovations in Africa (especially Kenya and East Africa)

                
                    
                    Capabilities:
                    You should:
                        1. Explain complex sustainability topics clearly and accurately.

                        2. Provide actionable insights and data-driven recommendations.

                        3. Suggest policies, technologies, or startups working in the sector.

                        4. Offer localized examples and initiatives in Kenya and Africa.

                        5. Educate users on how they can contribute to environmental sustainability.

                        6. Guide innovators on integrating AI, IoT, and Data Science into green solutions.

                        7. Respond to both technical (engineers, developers) and non-technical (students, activists) audiences with suitable tone and depth.

                    
                    Tone & Style:

                    - Use a professional, inspiring, and knowledgeable tone, Keep answers short for conversational response behaviors.
                    - Avoid unnecessary jargon — explain technical terms simply when used.
                    - Encourage eco-awareness, innovation, and collaboration.
                    - Be data-informed, evidence-based, and globally aware while remaining locally relevant.

                    
                    Important:
                    If the user’s question is outside the scope of energy, sustainability, or environmental technology, politely decline and redirect to related eco-innovation topics.

                    Example Topics Users May Ask About:

                    - “How can Kenya scale waste-to-energy projects?”

                    - “What are the best EV charging companies in Africa?”

                    - “How do carbon credits work for small communities?”

                    - “What AI models are used for energy optimization?”

                    - “How can households reduce energy waste?”

                    """,
                max_output_tokens= 1000,
                top_k= 2,
                top_p= 0.5,
                temperature= 0.9,
                # response_mime_type= 'application/json',
                # stop_sequences= ['\n'],
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
        return "You can drop off sorted waste (organic, plastic, metals, e-waste) at any of our hubs to earn ZeroTokens."
    elif "hub" in msg or "station" in msg or "nearby" in msg:
        return "You can find nearby ZeroWave collection points and community hubs on our 'Nearby' map."
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







# Initialize Firebase Admin SDK
try:
    firebase_admin.get_app()
except ValueError:
    cred_path = settings.BASE_DIR / 'firebase-credentials.json'
    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
    else:
        # Fallback: Try loading Firebase Admin credentials from env vars if the JSON file is missing
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

# Create your views here.
def home(request):
    return render(request, 'index.html')


def registration(request):
    context = get_firebase_context()
    return render(request, 'registration.html', context)


def signin(request):
    context = get_firebase_context()
    return render(request, 'signin.html', context)


def dashboard(request):
    return render(request, 'dashboard.html')


def settings(request):
    return render(request, 'settings.html')


def rewards(request):
    return render(request, 'rewards.html')


def impact(request):
    return render(request, 'impact.html')


def analytics(request):
    return render(request, 'analytics.html')


def nearby(request):
    return render(request, 'nearby.html')


def community(request):
    return render(request, 'community.html')



@csrf_exempt
@require_POST
def firebase_auth_view(request):
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')

        print(f"Authenticated Firebase user: {email} ({uid})")

        # Get or create user
        user, created = User.objects.get_or_create(username=uid, defaults={'email': email})

        if created:
            print(f"Created new Django user for {email}")
        else:
            print(f"Logged in existing Django user {email}")

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

