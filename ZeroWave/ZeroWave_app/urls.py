from django.urls import path, include
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
]
