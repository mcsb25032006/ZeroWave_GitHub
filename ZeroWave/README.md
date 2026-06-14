# 🌍 ZeroWave — Premium Waste-to-Energy & Sustainability Rewards Platform (India)

<div align="center">

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-39ff14?style=for-the-badge&logo=vercel&logoColor=black)](https://zero-wave.vercel.app)
[![Render Backend](https://img.shields.io/badge/Render-Active-00bfff?style=for-the-badge&logo=render&logoColor=white)](https://zerowave-ussd.onrender.com)
[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django Framework](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-f39c12.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

### 🚀 **Vercel Live Production URL:** [https://zero-wave.vercel.app](https://zero-wave.vercel.app)
### 🔗 **Render USSD Service URL:** [https://zerowave-ussd.onrender.com/ussd](https://zerowave-ussd.onrender.com/ussd)

---

## 📖 Project Overview

**ZeroWave** is a state-of-the-art, full-stack sustainability and green rewards ecosystem designed to incentivize dry waste segregation, promote circular economy practices (such as biogas generation and recycling), and foster active eco-friendly communities across major Indian metros. 

Aligned with India's **Swachh Bharat Mission (Urban 2.0)** goals, ZeroWave bridges the gap between digital waste accountability and local clean energy incentives. By dropping off sorted waste (organic, plastics, paper, metal, e-waste) at collection hubs, citizens earn **ZeroTokens** and **Carbon Credits**. These tokens are redeemable for premium green rewards from partners like Tata Power Rooftop Solar, Ola S1 EV rides, Swachh Cities municipal bill offsets, clean cooking LPG cylinder subsidies, and e-waste cashbacks at Croma or Reliance Digital.

The platform provides a responsive, beautifully styled web portal, an interactive **AI Sustainability Advisor** powered by Google Gemini (with Opik tracing analytics), interactive **Leaflet Geospatial Maps** locating metro collection points, and a low-connectivity **USSD Gateway** for offline users.

---

## 🎥 Video Demonstration

A detailed walkthrough of the platform, user workflows, and dashboards is available locally:
👉 **[View Demo Video](file:///c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/ZeroWave/ZeroWave.mp4)**

---

## ✨ Key Features

### 👤 1. Dual-Role Dashboards
*   **Citizen / Individual Dashboard**: Track your token balances, carbon credits saved, equivalent trees planted, and log recent recycling actions. Raise waste pickup tickets, select regions, and view local requirements.
*   **Waste Collection Bank Dashboard**: Designed for verified hubs. Search/verify members by phone number, log waste drop-offs, award ZeroTokens, claim pending pickup tickets, and publish regional dry waste requirements with custom incentive rates.

### 🎟️ 2. Integrated Eco-Rewards Hub
Redeem accumulated ZeroTokens for premium green vouchers:
*   **Tata Power Rooftop Solar**: Subsidies on residential solar setups.
*   **Swachh Cities Credits**: Deduct points directly from your municipal waste and water bills.
*   **Ola S1 EV Vouchers**: Safe, clean electric scooter rides.
*   **Clean Cooking Subsidies**: Refills for cleaner household LPG cylinders.
*   **Retail Cashbacks**: Cash back at electronic partners (Croma, Reliance Digital) for recycling e-waste.

### 🗺️ 3. Leaflet Geospatial Hub Locator
*   Interactive, high-fidelity maps pinpointing hubs in major Indian cities (**Bengaluru, Mumbai, Delhi NCR, Pune, Chennai, Hyderabad, Kolkata**).
*   Live occupancy status indicators (*Empty*, *Pre-Occupied*, *Fully Occupied*) based on registered storage weights.

### 💱 4. Carbon Credit Marketplace
*   A localized credit exchange.
*   Citizens can sell accumulated carbon credits for INR cashouts.
*   Corporate/Institutional buyers can purchase credits to offset organizational carbon footprints.

### 💬 5. AI Sustainability Advisor & Opik Observability
*   A responsive floating chatbot powered by `gemini-2.5-flash` to answer environmental questions.
*   Features a robust, rule-based fallback system in case of network outages.
*   Fully integrated with the **Opik SDK** to trace and monitor LLM pipelines.

### 📱 6. Offline USSD Telecom Gateway
*   A Flask-based USSD gateway simulating offline interactions for users without internet.
*   Supports balance inquiries, rewards redemption, reporting illegal dumping, and requests for Gemini-generated eco-tips delivered via automated SMS.

---

## ⚙️ Architecture & Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Citizen
    actor Bank as Waste Bank Agent
    participant Web as Web Interface (Vercel)
    participant Django as Django Backend (Render)
    participant USSD as USSD Gateway (Flask)
    participant DB as Postgres (Supabase)
    participant Gemini as Gemini AI API

    User->>Web: Register / Sign In (Firebase Auth)
    Web->>Django: Verify Firebase ID Token
    Django-->>Web: Session Verified & Local Profile Mapped
    
    rect rgb(200, 240, 200)
        Note over User, Django: Waste Drop-off Workflow
        User->>Bank: Drop off segregated waste
        Bank->>Web: Search user & log weight + type
        Web->>Django: Record Collection API
        Django->>DB: Update UserProfile (Tokens & Credits)
        Django-->>Web: Success Response (Tokens Issued)
    end

    rect rgb(240, 200, 200)
        Note over User, USSD: Offline USSD Workflow
        User->>USSD: Dial *384*90607# (Low-Connectivity)
        USSD->>Django: Query Balance / Request Tips
        Django->>Gemini: Request Eco-Tip Prompt
        Gemini-->>Django: Eco-Tip Text
        Django-->>USSD: Deliver balance / SMS text message
        USSD-->>User: Screen display / SMS notification
    end
```

---

## 📊 Database Design (Entity-Relationship)

The system consists of 9 core tables designed to track profiles, recycling logs, redemption transactions, community groups, and pickup tickets.

```mermaid
erDiagram
    USER ||--|| USERPROFILE : "has profile"
    USER ||--o{ WASTECOLLECTION : "logs collections"
    USER ||--o{ REDEMPTION : "redeems coupons"
    USER ||--o{ COMMUNITY : "creates community"
    USER ||--o{ COMMUNITYMEMBER : "joins community"
    COMMUNITY ||--o{ COMMUNITYMEMBER : "has members"
    USER ||--o{ CARBONLISTING : "creates listing"
    USER ||--o{ IMPACTCAMPAIGN : "manages campaign"
    USER ||--o{ WASTEREQUIREMENT : "posts requirement"
    USER ||--o{ COLLECTIONTICKET : "raises ticket"

    USERPROFILE {
        string firebase_uid UK
        string phone_number
        int tokens_balance
        int carbon_credits
        string household_id
        decimal total_waste_recycled
        decimal total_energy_generated
        int trees_planted
        string role "user or bank"
        string bank_name
        string region
    }

    WASTECOLLECTION {
        date date
        string category "organic or e-waste or recyclables or etc"
        decimal weight "kg"
        decimal energy_generated "kWh"
        int tokens_earned
        string hub_name
        string status "Empty or Pre-Occupied or Fully Occupied"
    }

    REDEMPTION {
        string reward_name
        int tokens_spent
        datetime date
        string phone_number
        string status "pending or success or failed"
    }

    COMMUNITY {
        string name UK
        string region "delhi or mumbai or bengaluru or etc"
        string category "recycling or reforestation or etc"
        string description
        string tagline
        boolean verified
        int points
        int members_count
        int credits
        decimal diverted_kg
        decimal energy_kwh
        decimal lat
        decimal lng
    }

    COLLECTIONTICKET {
        string category
        decimal estimated_weight
        string region
        text address
        string phone_number
        string status "pending or assigned or completed or cancelled"
        datetime created_at
    }
```

---

## 🔌 API Architecture (Catalog of Endpoints)

| Category | Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :---: | :--- |
| **Authentication** | `/` | GET | No | Landing / Marketing Page |
| | `/signin` | GET | No | User Sign-in Page |
| | `/registration` | GET | No | User Registration Page |
| | `/auth/firebase/` | POST | No | Firebase Auth token exchange and session login |
| **Portals** | `/dashboard` | GET | Yes | Citizen/Bank Role-Based Dashboard |
| | `/analytics` | GET | Yes | Detailed visual analytics charts |
| | `/nearby` | GET | Yes | Leaflet map locating metropolitan collection hubs |
| | `/community` | GET | Yes | Regional community hubs & carbon exchange portal |
| | `/settings` | GET | Yes | User Profile settings panel |
| **Chatbot** | `/chatbot-response/` | POST | No | Google Gemini 2.5 flash sustainability advisor |
| **User APIs** | `/api/redeem/` | POST | Yes | Redeems ZeroTokens for rewards vouchers |
| | `/api/community/join/` | POST | Yes | Toggles joining/leaving a community group |
| | `/api/community/create/` | POST | Yes | Creates a new community group |
| | `/api/marketplace/trade/` | POST | Yes | Buys or sells carbon offset credits |
| | `/api/settings/update/` | POST | Yes | Updates profile details (phone, region, etc.) |
| | `/api/tickets/create/` | POST | Yes | Raises a new waste pickup request ticket |
| | `/api/tickets/cancel/<id>/` | POST | Yes | Cancels a pending pickup ticket |
| **Bank APIs** | `/api/bank/validate-user/` | GET | Yes (Bank) | Validates user ID exists before recording collection |
| | `/api/bank/record-collection/` | POST | Yes (Bank) | Logs drop-off weight and issues tokens |
| | `/api/bank/requirements/create/` | POST | Yes (Bank) | Publishes target waste requirement lists |
| | `/api/tickets/claim/<id>/` | POST | Yes (Bank) | Claims a pending pickup request |
| | `/api/tickets/complete/<id>/` | POST | Yes (Bank) | Records measured weight and completes ticket |

---

## 🛠️ Local Installation & Development Setup

Follow these steps to configure and run the project locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/mcsb25032006/ZeroWave_GitHub.git
cd ZeroWave_GitHub
```

### 2. Set Up a Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (macOS/Linux)
# source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root folder of the project (`ZeroWave_GitHub/`) and populate it with your credentials:
```env
# Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key

# Supabase / PostgreSQL URL (Optional: Falls back to local SQLite if left empty)
DATABASE_URL=postgresql://username:password@host:5432/dbname

# Firebase Client Configuration (Web interface auth)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Firebase Admin Configuration (For token validation)
FIREBASE_CLIENT_EMAIL=your_service_account_email
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END PRIVATE KEY-----"

# Africa's Talking API (USSD SMS Gateway)
AT_API_KEY=your_telecom_api_key
```

### 4. Run Migrations & Apply Database Schema
```powershell
# Navigate to the Django directory
cd ZeroWave

# Run migrations
python manage.py migrate
```

### 5. Launch the Servers

#### Start Django Web Server:
```powershell
python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your web browser.

#### Start USSD Gateway Flask App (Optional):
In a separate terminal window with your venv activated:
```powershell
cd ZeroWave
python ZeroWave_app/ZeroWave_ussd/ussd.py
```
This starts a local USSD gateway listener at `http://127.0.0.1:8000/ussd`.

### 6. Run Automated Unit Tests
To run all tests locally using the SQLite fallback configuration:
```powershell
cmd /c "set DATABASE_URL=sqlite:///localhost_db.sqlite3& python manage.py test"
```

---

## 🚀 Deployment Guide

### A. Vercel (Web Serverless Frontend & Edge CDN)
Vercel hosts the web frontend and routes the python entrypoint. It reads the root [vercel.json](file:///c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/vercel.json) and triggers [build_files.sh](file:///c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/build_files.sh):
1. **GitHub Connection:** Connect your GitHub repository to your **Vercel** dashboard.
2. **Build Settings:** Keep default settings; Vercel detects and triggers the custom build script.
3. **Environment Variables:** Set all required env variables (`DATABASE_URL`, Firebase keys, and `GOOGLE_API_KEY`) under **Project Settings** → **Environment Variables**.
4. **Deploy:** Click **Deploy**. Vercel routes all web views through Django's WSGI application.

### B. Render (Backend Web Service)
Render hosts the persistent backend APIs, database connections, and ticket lifecycle handlers:
1. **New Web Service:** Log in to **Render** and click **New Web Service**, linking the repository.
2. **Root Directory:** Set **Root Directory** to `ZeroWave`.
3. **Build Command:** Set to `pip install -r requirements.txt`.
4. **Start Command:** Set to `gunicorn ZeroWave.wsgi:application --timeout 90`.
5. **Environment Variables:** Configure all keys from your `.env` under the **Environment** tab.

### C. USSD Gateway (Render Web Service)
The low-connectivity telecom USSD Flask service runs on Render:
1. **New Web Service:** Select the same repository on Render.
2. **Root Directory:** Set **Root Directory** to `ZeroWave`.
3. **Build Command:** Set to `pip install -r requirements.txt`.
4. **Start Command:** Set to `gunicorn ZeroWave_app.ZeroWave_ussd.ussd:app --timeout 90`.
5. **Callback Linking:** Copy the deployed USSD URL (e.g. `https://zerowave-ussd.onrender.com/ussd`) and paste it as the **Callback URL** inside the **Africa's Talking Sandbox USSD Settings**.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](file:///c:/Users/sragv/VSCODEWORK/Full_Stack_Projects/ZeroWave/LICENSE) file for details.
