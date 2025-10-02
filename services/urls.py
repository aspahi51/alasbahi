
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'services'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.home, name='home'),
    
    # المصادقة
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # اللوحات
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # الطلبات
    path('request/create/', views.create_request, name='create_request'),
    path('request/<int:request_id>/', views.request_detail, name='request_detail'),
    path('request/<int:request_id>/complete/', views.complete_request, name='complete_request'),
    
    # العروض
    path('request/<int:request_id>/offer/', views.create_offer, name='create_offer'),
    path('offer/<int:offer_id>/accept/', views.accept_offer, name='accept_offer'),
    path('offer/<int:offer_id>/reject/', views.reject_offer, name='reject_offer'),
    
    # التقييمات
    path('request/<int:request_id>/rate/', views.rate_engineer, name='rate_engineer'),
    path('engineer/<int:engineer_id>/', views.engineer_profile, name='engineer_profile'),
]
