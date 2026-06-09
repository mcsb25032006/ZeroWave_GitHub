from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("registration", views.registration, name="registration"),
    path("signin", views.signin, name="signin"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("settings", views.settings, name="settings"),
    path("analytics", views.analytics, name="analytics"),
    path("impact", views.impact, name="impact"),
    path("rewards", views.rewards, name="reward"),
    path("nearby", views.nearby, name="nearby"),
    path("community", views.community, name="community"),
    path("chatbot-response/", views.chatbot_response, name="chatbot_response"),
    path("auth/firebase/", views.firebase_auth_view, name="firebase_auth"),
    
    # API endpoints
    path("api/redeem/", views.api_redeem, name="api_redeem"),
    path("api/create-campaign/", views.api_create_campaign, name="api_create_campaign"),
    path("api/community/join/", views.api_community_join, name="api_community_join"),
    path("api/community/apply-lead/", views.api_community_apply_lead, name="api_community_apply_lead"),
    path("api/community/create/", views.api_community_create, name="api_community_create"),
    path("api/marketplace/trade/", views.api_marketplace_trade, name="api_marketplace_trade"),
    path("api/settings/update/", views.api_settings_update, name="api_settings_update"),
    
    # Bank Dashboard endpoints
    path("api/bank/validate-user/", views.api_bank_validate_user, name="api_bank_validate_user"),
    path("api/bank/record-collection/", views.api_bank_record_collection, name="api_bank_record_collection"),
    path("api/bank/requirements/create/", views.api_bank_create_requirement, name="api_bank_create_requirement"),
    path("api/bank/requirements/delete/<int:req_id>/", views.api_bank_delete_requirement, name="api_bank_delete_requirement"),
    
    # Collection Ticket endpoints
    path("api/tickets/create/", views.api_create_ticket, name="api_create_ticket"),
    path("api/tickets/claim/<int:ticket_id>/", views.api_claim_ticket, name="api_claim_ticket"),
    path("api/tickets/complete/<int:ticket_id>/", views.api_complete_ticket_pickup, name="api_complete_ticket_pickup"),
    path("api/tickets/cancel/<int:ticket_id>/", views.api_cancel_ticket, name="api_cancel_ticket"),
]
