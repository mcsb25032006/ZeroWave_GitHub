from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from .models import UserProfile, WasteRequirement, WasteCollection, CollectionTicket

class ZeroWaveBankTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create user profile
        self.user = User.objects.create_user(username='test_user', email='user@test.com', password='password123')
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='user',
            household_id='ZW-2026-1111',
            tokens_balance=100
        )
        
        # Create bank profile
        self.bank = User.objects.create_user(username='test_bank', email='bank@test.com', password='password123')
        self.bank_profile = UserProfile.objects.create(
            user=self.bank,
            role='bank',
            bank_name='Bengaluru Waste Bank',
            region='bengaluru',
            household_id='ZW-BANK-2222'
        )

    def test_user_and_bank_profiles(self):
        self.assertEqual(self.user_profile.role, 'user')
        self.assertEqual(self.bank_profile.role, 'bank')
        self.assertEqual(self.bank_profile.bank_name, 'Bengaluru Waste Bank')

    def test_create_requirement(self):
        self.client.login(username='test_bank', password='password123')
        
        # Post a requirement
        response = self.client.post(
            reverse('api_bank_create_requirement'),
            data='{"category": "plastic", "quantity_required": 50, "tokens_per_kg": 15}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['requirement']['tokens_per_kg'], 15)
        
        req = WasteRequirement.objects.get(bank=self.bank)
        self.assertEqual(req.category, 'plastic')
        self.assertEqual(req.quantity_required, Decimal('50.00'))
        self.assertEqual(req.percentage_collected, 0)

    def test_validate_user(self):
        self.client.login(username='test_bank', password='password123')
        
        # Validate valid user
        response = self.client.get(reverse('api_bank_validate_user'), {'user_id': 'ZW-2026-1111'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['username'], 'test_user')
        
        # Validate invalid user
        response = self.client.get(reverse('api_bank_validate_user'), {'user_id': 'ZW-INVALID-999'})
        self.assertEqual(response.status_code, 404)

    def test_record_collection_with_requirement(self):
        # Create active requirement first
        req = WasteRequirement.objects.create(
            bank=self.bank,
            category='plastic',
            quantity_required=50,
            tokens_per_kg=15,
            status='Active'
        )
        
        self.client.login(username='test_bank', password='password123')
        
        # Record a dropoff
        response = self.client.post(
            reverse('api_bank_record_collection'),
            data='{"user_id": "ZW-2026-1111", "category": "plastic", "weight": 10}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['tokens_earned'], 150)  # 10 kg * 15 rate
        
        # Check user profile updated
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.tokens_balance, 250)  # 100 base + 150 earned
        self.assertEqual(self.user_profile.total_waste_recycled, Decimal('10.00'))
        
        # Check requirement updated
        req.refresh_from_db()
        self.assertEqual(req.quantity_collected, Decimal('10.00'))
        self.assertEqual(req.percentage_collected, 20)
        self.assertEqual(req.status, 'Active')
        
        # Record another dropoff to complete requirement
        response = self.client.post(
            reverse('api_bank_record_collection'),
            data='{"user_id": "ZW-2026-1111", "category": "plastic", "weight": 40}',
            content_type='application/json'
        )
        req.refresh_from_db()
        self.assertEqual(req.status, 'Completed')

    def test_collection_ticket_lifecycle(self):
        # 1. Create ticket (logged in as User)
        self.client.login(username='test_user', password='password123')
        response = self.client.post(
            reverse('api_create_ticket'),
            data='{"category": "organic", "estimated_weight": 25, "region": "bengaluru", "address": "123 Street", "phone_number": "0711111111"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        ticket_id = data['ticket']['id']
        
        # Verify in database
        ticket = CollectionTicket.objects.get(id=ticket_id)
        self.assertEqual(ticket.status, 'pending')
        self.assertEqual(ticket.estimated_weight, Decimal('25.00'))
        
        # 2. Claim ticket (logged in as Bank)
        self.client.login(username='test_bank', password='password123')
        response = self.client.post(reverse('api_claim_ticket', args=[ticket_id]))
        self.assertEqual(response.status_code, 200)
        
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'assigned')
        self.assertEqual(ticket.assigned_bank, self.bank)
        
        # 3. Complete ticket pickup (logged in as Bank)
        response = self.client.post(
            reverse('api_complete_ticket_pickup', args=[ticket_id]),
            data='{"actual_weight": 28}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['tokens_earned'], 280) # 28 kg * 10 (default rate)
        
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'completed')
        
        # Check user profile received tokens
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.tokens_balance, 380) # 100 base + 280 earned

    def test_firebase_auth_role_mismatch(self):
        # Authenticate user with role 'bank' (they are registered as 'user')
        # I mock the verification by calling the endpoint directly
        self.client.login(username='test_user', password='password123')
        
        # Mocking Firebase verify_id_token is not needed if I mock the backend payload
        # Wait, the endpoint expects a real ID token and verifies it. I can patch firebase_auth.verify_id_token
        from unittest.mock import patch
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {'uid': 'test_user', 'email': 'user@test.com'}
            response = self.client.post(
                reverse('firebase_auth'),
                data='{"idToken": "mock_token", "role": "bank"}',
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data['status'], 'error')
            self.assertIn('This account is registered as an Individual User', data['message'])

    def test_firebase_auth_email_conflict(self):
        # Try to register a new user UID but with an existing email 'user@test.com'
        from unittest.mock import patch
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {'uid': 'new_unique_uid', 'email': 'user@test.com'}
            response = self.client.post(
                reverse('firebase_auth'),
                data='{"idToken": "mock_token", "role": "bank"}',
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 400)
            data = response.json()
            self.assertEqual(data['status'], 'error')
            self.assertIn('already registered as an Individual User', data['message'])

    def test_api_redeem(self):
        self.client.login(username='test_user', password='password123')
        
        # Valid redemption
        response = self.client.post(
            reverse('api_redeem'),
            data='{"reward_name": "Tata Power Solar", "tokens_spent": 50, "phone_number": "9999999999"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_balance'], 50)
        
        # Insufficient tokens redemption
        response = self.client.post(
            reverse('api_redeem'),
            data='{"reward_name": "Ola Electric Voucher", "tokens_spent": 60, "phone_number": "9999999999"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Insufficient token balance')

    def test_api_community_join(self):
        from .models import Community
        self.client.login(username='test_user', password='password123')
        
        # Create a test community
        community = Community.objects.create(
            name="Mumbai Green Brigade",
            region="mumbai",
            category="waste",
            description="Active waste group in Mumbai",
            tagline="Green Mumbai",
            lat=Decimal("19.0760"),
            lng=Decimal("72.8777"),
            members_count=0
        )
        
        # Join community
        response = self.client.post(
            reverse('api_community_join'),
            data=f'{{"community_id": "c_{community.id}"}}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'joined')
        self.assertEqual(data['members_count'], 1)
        
        # Leave community
        response = self.client.post(
            reverse('api_community_join'),
            data=f'{{"community_id": "c_{community.id}"}}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'left')
        self.assertEqual(data['members_count'], 0)

    def test_api_marketplace_trade_buy(self):
        self.client.login(username='test_user', password='password123')
        
        # Buy carbon credits
        response = self.client.post(
            reverse('api_marketplace_trade'),
            data='{"type": "buy", "amount": 10}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_balance'], 110) # 100 base + 10 bought

    def test_api_marketplace_trade_sell(self):
        self.client.login(username='test_user', password='password123')
        
        # Sell carbon credits
        response = self.client.post(
            reverse('api_marketplace_trade'),
            data='{"type": "sell", "amount": 40}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['new_balance'], 60) # 100 base - 40 sold
        
        # Insufficient credits list for sale
        response = self.client.post(
            reverse('api_marketplace_trade'),
            data='{"type": "sell", "amount": 70}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Insufficient token balance to list for sale')

    def test_api_settings_update(self):
        self.client.login(username='test_user', password='password123')
        
        # Update settings
        response = self.client.post(
            reverse('api_settings_update'),
            data='{"full_name": "Amit Kumar", "email": "amit@test.com", "phone": "+919999999999", "region": "mumbai"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify db updates
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Amit')
        self.assertEqual(self.user.last_name, 'Kumar')
        self.assertEqual(self.user.email, 'amit@test.com')
        
        self.user_profile.refresh_from_db()
        self.assertEqual(self.user_profile.phone_number, '+919999999999')
        self.assertEqual(self.user_profile.region, 'mumbai')

    def test_chatbot_response(self):
        # Local fallback test
        response = self.client.post(
            reverse('chatbot_response'),
            data='{"message": "tell me about ZeroTokens"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)
        self.assertTrue(len(data['response']) > 0)

    def test_ussd_flask_app(self):
        # Mock Africa's Talking USSD Flask Endpoint
        from ZeroWave_app.ZeroWave_ussd.ussd import app
        from unittest.mock import patch
        
        flask_client = app.test_client()
        
        # 1. Start USSD session (welcome screen)
        response = flask_client.post('/ussd', data={
            'sessionId': 'session_123',
            'phoneNumber': '+919999999999',
            'serviceCode': '*384*20880#',
            'text': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to ZeroWave', response.data)
        
        # 2. Select option 2 (ZeroTokens)
        response = flask_client.post('/ussd', data={
            'sessionId': 'session_123',
            'phoneNumber': '+919999999999',
            'serviceCode': '*384*20880#',
            'text': '2'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Get to know your ZeroTokens', response.data)
        
        # 3. Select option 4 (Locate Stations)
        response = flask_client.post('/ussd', data={
            'sessionId': 'session_123',
            'phoneNumber': '+919999999999',
            'serviceCode': '*384*20880#',
            'text': '4'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'www.zerowave.in/stations', response.data)
        
        # 4. Mock the Gemini autogenerate tips SMS endpoint
        with patch('ZeroWave_app.ZeroWave_ussd.ussd_response.ai_response.autogenerate_tips_response') as mock_tips:
            mock_tips.return_value = "Mocked eco-tip message."
            # Select option 5 (Get Tips & Alerts)
            response = flask_client.post('/ussd', data={
                'sessionId': 'session_123',
                'phoneNumber': '+919999999999',
                'serviceCode': '*384*20880#',
                'text': '5'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'recieve a message shortly', response.data)

