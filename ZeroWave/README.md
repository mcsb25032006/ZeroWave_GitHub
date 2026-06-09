# ZeroWave — Waste-to-Energy and Sustainability Platform

ZeroWave is a premium, full-stack sustainability and green rewards platform designed to incentivize dry waste segregation, promote circular economy practices (biogas generation, recycling), and build eco-friendly communities. 

The platform allows individuals to earn **ZeroTokens** and **Carbon Credits** by dropping off sorted waste (organic, plastics, paper, metal, e-waste) at collection hubs. These tokens can be redeemed for local Indian utility rewards, green transit discounts, clean cooking fuel, and solar energy support.

ZeroWave features a responsive web interface equipped with an interactive AI Chatbot (powered by Google Gemini), Leaflet maps for geolocating collection hubs, and a low-connectivity USSD sub-module for users with basic mobile phones or poor internet access.

---

## 1. Aim of the Project

The primary goal of ZeroWave is to democratize waste-to-energy initiatives and dry waste segregation. By combining financial incentives (ZeroTokens and Carbon Credits) with accessible tools (such as low-bandwidth offline USSD interfaces and advanced web diagnostics), ZeroWave drives behavioral change towards clean energy conversion and a sustainable circular economy.

---

## 2. What it Does (Core Features)

*   **Dual-Role Dashboards**:
    *   **Individual User Dashboard**: Allows citizens to track their token balance, carbon credits saved, trees planted equivalent, raise waste collection pickup tickets, and manage settings.
    *   **Waste Collection Bank Dashboard**: Empowers verified collection centers to search and verify members, record waste drop-offs, issue ZeroTokens, claim pickup requests, and post specific dry waste requirements (with customized reward rates).
*   **Collection Ticket Lifecycle**: Users can raise pickup tickets specifying waste category, estimated weight, region, and address. Collection banks can claim these tickets, drive to the location, weigh the waste, and complete the collection to automatically issue tokens to the user.
*   **Eco-Rewards Hub**: Users spend ZeroTokens to redeem vouchers for:
    *   *Tata Power Rooftop Solar*: Subsidies on home solar installations.
    *   *Swachh Cities Credits*: Offsets for municipal waste/water bills.
    *   *Ola S1 EV Rides*: Subsidized electric scooter rides.
    *   *Clean Cooking Gas*: LPG cylinder refills or stove accessories.
    *   *E-Waste Buyback*: Cashback vouchers at retail partners like Croma and Reliance Digital.
*   **Geospatial Hub Locator (Leaflet)**: Interactive map showing nearby collection points, color-coded by occupancy status (*Empty*, *Pre-Occupied*, *Fully Occupied*) based on log weights.
*   **Carbon Credit Marketplace**: A mini-exchange where users can sell carbon credits for INR or buy credits to offset their footprints, tracking transactions on a ledger.
*   **AI Sustainability Advisor**: A floating chatbot interface powered by `gemini-2.5-flash` that answers environmental queries (with a robust local rule-based fallback system).
*   **Offline USSD Gateway**: A Flask USSD simulator supporting offline interactions (balance checks, redemptions, reporting illegal dumping, and requesting AI-generated eco-tips sent via SMS alerts).

---

## 3. Workflow of the Project

```mermaid
graph TD
    A[User Visits ZeroWave Web / Dials USSD] -->|Web| B[Firebase Sign Up / Sign In]
    A -->|USSD| C[Africa's Talking USSD Gateway]
    B -->|Frontend Auth Success| D[Django Session Verification via Firebase ID Token]
    D -->|Session Started| E[User Accesses Web Dashboard]
    C -->|Flask USSD Route| F[Check Balance / Redeem Tokens / Request AI Eco-Tips]
    E -->|Drop Off sorted waste| G[Earn ZeroTokens & Carbon Credits]
    E -->|Interact with Leaflet Map| H[Geolocate stations & join community groups]
    E -->|Open Chat Widget| I[Gemini 2.5 Chatbot responds to sustainability queries]
    G -->|Redeem Page| J[Exchange Tokens for Solar, EV rides, or LPG vouchers]
```

1.  **Auth Flow**: Users register/login using Firebase Auth. Client-side ID tokens are verified securely on the Django backend, and a local profile mapping is updated.
2.  **Collection Flow**: Users drop off segregated waste at collection points. The Waste Bank inputs the weight, which increments the user's token balance and updates global carbon offset metrics.
3.  **USSD/SMS Flow**: Offline users dial the USSD shortcode to query balances, report issues, or trigger a Gemini API hook that compiles and texts them an eco-tip via SMS.

---

## 4. Tech Stack

*   **Web Backend**: Django 5.x (Python 3), Gunicorn WSGI server.
*   **Web Frontend**: HTML5, Vanilla JavaScript, CSS3 (Comfort HSL-tailored Light/Dark mode themes), Bootstrap 5, FontAwesome Icons.
*   **Database**: PostgreSQL (hosted on Supabase) with local SQLite development fallback.
*   **Authentication**: Client-side Firebase Authentication verified securely via `firebase-admin` SDK.
*   **AI Integrations**: Google GenAI SDK (`gemini-2.5-flash` model for chat assistance and USSD automated SMS tip generator).
*   **USSD/SMS Sub-module**: Flask-based web service integrating with Africa's Talking API.
*   **Observability & Analytics**: Opik SDK (for tracking AI generator trace steps).
*   **Geospatial & Charts**: Leaflet.js (for map geolocation), Chart.js (for analytics rendering).

---

## 5. Database Design (Django Models)

The database consists of 9 core tables designed to track user profiles, waste logs, transactions, communities, and pickup tickets:

```mermaid
erDiagram
    UserProfile ||--|| User : "extends"
    WasteCollection }o--|| User : "logged by"
    Redemption }o--|| User : "redeemed by"
    Community }o--|| User : "created by"
    CommunityMember }o--|| Community : "belongs to"
    CommunityMember }o--|| User : "is member"
    CarbonListing }o--|| User : "listed by"
    ImpactCampaign }o--|| User : "managed by"
    WasteRequirement }o--|| User : "posted by"
    CollectionTicket }o--|| User : "raised by"
    CollectionTicket }o--|| User : "assigned to (bank)"
```

### 1. UserProfile
Extends the standard Django User model. Tracks tokens, credits, roles, and regions.
*   `user` (OneToOneField to User)
*   `firebase_uid` (CharField, unique)
*   `role` (CharField: `user` or `bank`)
*   `tokens_balance` (IntegerField, default 0)
*   `carbon_credits` (IntegerField, default 0)
*   `total_waste_recycled` (DecimalField)
*   `total_energy_generated` (DecimalField)
*   `trees_planted` (IntegerField)
*   `bank_name` (CharField, optional)
*   `region` (CharField: delhi, mumbai, bengaluru, etc.)

### 2. WasteCollection
Logs verified waste drop-offs at collection hubs.
*   `user` (ForeignKey to User)
*   `category` (CharField: organic, e-waste, recyclables, agriculture, metal, plastic, paper)
*   `weight` (DecimalField in kg)
*   `energy_generated` (DecimalField in kWh)
*   `tokens_earned` (IntegerField)
*   `hub_name` (CharField)
*   `status` (CharField: Empty, Pre-Occupied, Fully Occupied)

### 3. Redemption
Tracks coupon redemptions for utilities or vouchers.
*   `user` (ForeignKey to User)
*   `reward_name` (CharField)
*   `tokens_spent` (IntegerField)
*   `phone_number` (CharField)
*   `status` (CharField: pending, success, failed)

### 4. Community
Tracks regional environmental groups and carbon offsets.
*   `name` (CharField, unique)
*   `region` (CharField)
*   `category` (CharField: recycling, reforestation, energy, education)
*   `description` (TextField)
*   `creator` (ForeignKey to User)
*   `verified` (BooleanField)
*   `points` (IntegerField)
*   `members_count` (IntegerField)
*   `credits` (IntegerField)
*   `diverted_kg` (DecimalField)
*   `energy_kwh` (DecimalField)
*   `lat`, `lng` (DecimalField coordinates)

### 5. CollectionTicket
Manages user-raised waste pickup requests.
*   `user` (ForeignKey to User - requester)
*   `category` (CharField)
*   `estimated_weight` (DecimalField)
*   `region` (CharField)
*   `address` (TextField)
*   `phone_number` (CharField)
*   `status` (CharField: pending, assigned, completed, cancelled)
*   `assigned_bank` (ForeignKey to User - assignee)

---

## 6. API Architecture (Endpoints Catalog)

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/` | GET | No | Landing / Marketing Page |
| `/signin` | GET | No | User Sign-in Page |
| `/registration` | GET | No | User Registration Page |
| `/dashboard` | GET | Yes | Individual User Dashboard |
| `/analytics` | GET | Yes | Detailed visual analytics charts |
| `/nearby` | GET | Yes | Leaflet map locating collection hubs |
| `/community` | GET | Yes | Groups list and carbon credit exchange portal |
| `/settings` | GET | Yes | User Profile settings panel |
| `/auth/firebase/` | POST | No | Firebase Auth token exchange and login |
| `/chatbot-response/` | POST | No | Google Gemini 2.5 flash chatbot endpoint |
| `/api/redeem/` | POST | Yes | Redeems ZeroTokens for local vouchers |
| `/api/community/join/` | POST | Yes | Toggles joining/leaving a community group |
| `/api/community/create/` | POST | Yes | Creates a new community group |
| `/api/marketplace/trade/` | POST | Yes | Buys or sells carbon offset credits |
| `/api/settings/update/` | POST | Yes | Updates profile details (phone, region, etc.) |
| `/api/bank/validate-user/` | GET | Yes (Bank) | Validates user ID exists before collection |
| `/api/bank/record-collection/` | POST | Yes (Bank) | Logs drop-off weight and issues tokens |
| `/api/bank/requirements/create/` | POST | Yes (Bank) | Publishes target waste requirement lists |
| `/api/tickets/create/` | POST | Yes | Raises a new pickup request ticket |
| `/api/tickets/claim/<id>/` | POST | Yes (Bank) | Claims a pending pickup request |
| `/api/tickets/complete/<id>/` | POST | Yes (Bank) | Records measured weight and completes ticket |
| `/api/tickets/cancel/<id>/` | POST | Yes | Cancels a pickup ticket |

---

## 7. Step-by-Step Execution Commands

Follow these steps to configure and run the project locally on your system:

### 1. Clone the Repository and Navigate to Directory
```bash
git clone https://github.com/mcsb25032006/ZeroWave.git
cd ZeroWave
```

### 2. Set Up Virtual Environment and Install Dependencies
```powershell
# Create venv
python -m venv venv

# Activate venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate venv (macOS/Linux)
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root folder of the project (`ZeroWave/`) containing:
```env
# Gemini config
GOOGLE_API_KEY=your_gemini_api_key

# Supabase Database URL (Optional, falls back to local sqlite)
DATABASE_URL=postgresql://username:password@host:5432/dbname

# Firebase config (for auth client-side validation)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Firebase Admin configuration (fallback when JSON credential file is missing)
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END PRIVATE KEY-----"

# Africa's Talking API config
AT_API_KEY=your_africas_talking_api_key
```

### 4. Run Migrations & Apply Seeds
```powershell
# Navigate to Django folder
cd ZeroWave

# Apply migrations
python manage.py migrate
```

### 5. Run the Web Server
```powershell
python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your browser.

### 6. Run the USSD Gateway Flask App (Optional)
Open a new terminal window, activate the venv, and run:
```powershell
cd ZeroWave
python ZeroWave_app/ZeroWave_ussd/ussd.py
```
This launches a listener at `http://127.0.0.1:8000/ussd` that can be mapped to Africa's Talking sandbox.

### 7. Run Unit Tests
```powershell
python manage.py test
```

---

## 8. Deployment Guide

### A. Vercel (Frontend & Serverless Views)
Vercel is used to host your Django templates and serverless web views using the configured `vercel.json` at the root of the project:
1. Connect your GitHub repository to **Vercel**.
2. Add your environment variables in Vercel project settings (ensure `FIREBASE_PRIVATE_KEY` and `FIREBASE_CLIENT_EMAIL` are configured so Vercel can initialize Firebase Admin without the file).
3. Click **Deploy**. Vercel will serve your app.

### B. Render (Backend Web Service)
Render hosts your persistent Django backend and database connections:
1. Log in to **Render** and click **New Web Service**, linking your Git repository.
2. Set **Root Directory** to `ZeroWave`.
3. Set **Build Command** to `pip install -r requirements.txt && python manage.py collectstatic --noinput`.
4. Set **Start Command** to `gunicorn ZeroWave.wsgi:application`.
5. Insert your environment variables under advanced settings and click **Create Web Service**.

### C. USSD Gateway (Render Web Service)
1. In Render, click **New Web Service** and select the same repository.
2. Set **Root Directory** to `ZeroWave`.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `gunicorn ZeroWave_app.ZeroWave_ussd.ussd:app`.
5. Configure `GOOGLE_API_KEY` and `AT_API_KEY` in environment settings, then deploy.
6. Link the generated public webhook URL to your **Africa's Talking Sandbox** dashboard.

---

## 9. Conclusion

ZeroWave bridges the gap between digital waste accountability and local clean energy incentives. By offering a high-fidelity analytics dashboard alongside an offline-friendly USSD gateway, the platform removes barriers to entry for waste recycling in urban centers. Supported by Google's generative models, robust database schemas, and structured web services, ZeroWave equips users with the knowledge and rewards required to transition communities into sustainable, circular hubs.
