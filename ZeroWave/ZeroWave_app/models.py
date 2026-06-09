from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Individual User'),
        ('bank', 'Waste Collection Bank'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    tokens_balance = models.IntegerField(default=0)
    carbon_credits = models.IntegerField(default=0)
    household_id = models.CharField(max_length=50, default='ZW-2026-0000')
    total_waste_recycled = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_energy_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    trees_planted = models.IntegerField(default=0)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    bank_name = models.CharField(max_length=150, null=True, blank=True)
    region = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        if self.role == 'bank' and self.bank_name:
            return f"{self.bank_name} Profile"
        return f"{self.user.username}'s Profile"

class WasteCollection(models.Model):
    CATEGORIES = [
        ('organic', 'Organic'),
        ('e-waste', 'E-waste'),
        ('recyclables', 'Recyclables'),
        ('agriculture', 'Agriculture'),
        ('metal', 'Metal Waste'),
        ('pharma', 'Pharma Waste'),
        ('plastic', 'Plastic Waste'),
        ('paper', 'Paper Waste'),
    ]
    STATUS_CHOICES = [
        ('Empty', 'Empty'),
        ('Pre-Occupied', 'Pre-Occupied'),
        ('Fully Occupied', 'Fully Occupied'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    weight = models.DecimalField(max_digits=10, decimal_places=2)  # In Kgs
    energy_generated = models.DecimalField(max_digits=10, decimal_places=2)  # In kWh
    tokens_earned = models.IntegerField()
    hub_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Empty')

    def __str__(self):
        return f"{self.category} collection at {self.hub_name} ({self.weight} kg)"

class Redemption(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='redemptions')
    reward_name = models.CharField(max_length=100)
    tokens_spent = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='success')

    def __str__(self):
        return f"{self.user.username} redeemed {self.reward_name} for {self.tokens_spent} tokens"

class Community(models.Model):
    REGIONS = [
        ('delhi', 'Delhi NCR'),
        ('mumbai', 'Mumbai Metro'),
        ('bengaluru', 'Bengaluru'),
        ('hyderabad', 'Hyderabad'),
        ('chennai', 'Chennai'),
        ('kolkata', 'Kolkata'),
        ('pune', 'Pune'),
    ]
    CATEGORIES = [
        ('recycling', 'Recycling'),
        ('reforestation', 'Reforestation'),
        ('energy', 'Renewable Energy'),
        ('education', 'Education'),
    ]
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=50, choices=REGIONS)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    description = models.TextField()
    tagline = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_communities')
    verified = models.BooleanField(default=False)
    points = models.IntegerField(default=0)
    members_count = models.IntegerField(default=1)
    credits = models.IntegerField(default=0)
    diverted_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    energy_kwh = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    createdAt = models.DateTimeField(auto_now_add=True)
    lead_applicant_uid = models.CharField(max_length=128, null=True, blank=True)

    def __str__(self):
        return self.name

class CommunityMember(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    joined_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, default='Member')  # Member, Lead

    class Meta:
        unique_together = ('community', 'user')

class CarbonListing(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carbon_listings')
    amount = models.IntegerField()
    price_per_credit = models.DecimalField(max_digits=10, decimal_places=2)  # In INR
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} credits at {self.price_per_credit} INR by {self.user.username}"


class ImpactCampaign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    title = models.CharField(max_length=100)
    campaign_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    status = models.CharField(max_length=20, default='Active')  # Active, Completed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class WasteRequirement(models.Model):
    bank = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requirements')
    category = models.CharField(max_length=50, choices=WasteCollection.CATEGORIES)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2)  # In Kgs
    quantity_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # In Kgs
    tokens_per_kg = models.IntegerField(default=10)
    status = models.CharField(max_length=20, default='Active')  # Active, Completed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank.profile.bank_name or self.bank.username} requires {self.quantity_required} kg of {self.category}"

    @property
    def percentage_collected(self):
        if self.quantity_required > 0:
            pct = (self.quantity_collected / self.quantity_required) * 100
            return min(int(pct), 100)
        return 0

class CollectionTicket(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Pickup'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pickup_tickets')
    category = models.CharField(max_length=50, choices=WasteCollection.CATEGORIES)
    estimated_weight = models.DecimalField(max_digits=10, decimal_places=2)  # In Kgs
    region = models.CharField(max_length=50, choices=Community.REGIONS)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_bank = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_pickups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket {self.id} ({self.category}) raised by {self.user.username} - Status: {self.status}"

