from django.contrib import admin
from . models import Profile, ServiceRequest, Offer, Rating



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone', 'created']
    list_filter = ['user_type', 'created']
    search_fields = ['user__username', 'user__email']



@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'request_type', 'assigned_engineer', 'status', 'created']
    list_filter = ['request_type', 'status', 'created']
    search_fields = ['title', 'client__username']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'engineer', 'price', 'status', 'created']
    list_filter = ['status', 'created']
    search_fields = ['service_request__title', 'engineer__username']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'engineer', 'client', 'stars', 'created']
    list_filter = ['stars', 'created']
    search_fields = ['engineer__username', 'client__username']

