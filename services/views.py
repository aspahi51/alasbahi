from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Profile, ServiceRequest, Offer, Rating
from .forms import UserRegistrationForm, ServiceRequestForm, OfferForm, RatingForm

def home(request):
    return render(request, 'services/home.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()

            profile = new_user.profile
            profile.user_type = form.cleaned_data['user_type']
            profile.phone = form.cleaned_data['phone']
            profile.save()

            login(request, new_user)
            messages.success(request, 'تم إنشاء الحساب بنجاح!')
            return redirect('services:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if profile.user_type == 'client':
        service_requests = ServiceRequest.objects.filter(client=request.user)
        context = {
            'profile': profile,
            'service_requests': service_requests,
        }
        return render(request, 'services/client_dashboard.html', context)
    
    elif profile.user_type == 'engineer':
        # الطلبات العامة
        public_requests = ServiceRequest.objects.filter(
            request_type='public', 
            status='pending'
        ).exclude(offers__engineer=request.user)
        
        # الطلبات الخاصة الموجهة للمهندس
        private_requests = ServiceRequest.objects.filter(
            request_type='private',
            assigned_engineer=request.user,
            status='pending'
        )
        
        # الطلبات المقبولة
        accepted_requests = ServiceRequest.objects.filter(
            Q(offers__engineer=request.user, offers__status='accepted') |
            Q(assigned_engineer=request.user, status__in=['accepted', 'in_progress'])
        )
        
        # العروض المقدمة
        my_offers = Offer.objects.filter(engineer=request.user)
        
        context = {
            'profile': profile,
            'public_requests': public_requests,
            'private_requests': private_requests,
            'accepted_requests': accepted_requests,
            'my_offers': my_offers,
        }
        return render(request, 'services/engineer_dashboard.html', context)

@login_required
def create_request(request):
    if request.user.profile.user_type != 'client':
        messages.error(request, 'العملاء فقط يمكنهم إنشاء طلبات.')
        return redirect('services:dashboard')
    
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, request.FILES)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.client = request.user
            new_request.save()
            messages.success(request, 'تم إنشاء الطلب بنجاح!')
            return redirect('services:dashboard')
    else:
        form = ServiceRequestForm()
    
    return render(request, 'services/create_request.html', {'form': form})

@login_required
def request_detail(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    offers = service_request.offers.all()
    
    context = {
        'service_request': service_request,
        'offers': offers,
    }
    return render(request, 'services/request_detail.html', context)

@login_required
def create_offer(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    if request.user.profile.user_type != 'engineer':
        messages.error(request, 'المهندسون فقط يمكنهم تقديم عروض.')
        return redirect('services:request_detail', request_id=request_id)
    
    # التحقق من نوع الطلب
    if service_request.request_type == 'private' and service_request.assigned_engineer != request.user:
        messages.error(request, 'لا يمكنك تقديم عرض على هذا الطلب الخاص.')
        return redirect('services:dashboard')
    
    # التحقق من وجود عرض سابق
    if Offer.objects.filter(service_request=service_request, engineer=request.user).exists():
        messages.error(request, 'لقد قدمت عرضاً على هذا الطلب مسبقاً.')
        return redirect('services:dashboard')
    
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            new_offer = form.save(commit=False)
            new_offer.service_request = service_request
            new_offer.engineer = request.user
            new_offer.save()
            messages.success(request, 'تم تقديم العرض بنجاح!')
            return redirect('services:dashboard')
    else:
        form = OfferForm()
    
    return render(request, 'services/create_offer.html', {
        'form': form,
        'service_request': service_request
    })

@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if offer.service_request.client != request.user:
        messages.error(request, 'لا يمكنك قبول هذا العرض.')
        return redirect('services:dashboard')
    
    # قبول العرض ورفض باقي العروض
    offer.status = 'accepted'
    offer.save()
    
    # رفض باقي العروض
    Offer.objects.filter(service_request=offer.service_request).exclude(id=offer.id).update(status='rejected')
    
    # تحديث حالة الطلب
    offer.service_request.status = 'in_progress'
    offer.service_request.save()
    
    messages.success(request, 'تم قبول العرض بنجاح!')
    return redirect('services:dashboard')

@login_required
def reject_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    
    if offer.service_request.client != request.user:
        messages.error(request, 'لا يمكنك رفض هذا العرض.')
        return redirect('services:dashboard')
    
    offer.status = 'rejected'
    offer.save()
    
    messages.success(request, 'تم رفض العرض.')
    return redirect('services:dashboard')

@login_required
def complete_request(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    # التحقق من الصلاحية
    if service_request.client != request.user and not (
        hasattr(service_request, 'offers') and 
        service_request.offers.filter(engineer=request.user, status='accepted').exists()
    ):
        messages.error(request, 'لا يمكنك تعديل حالة هذا الطلب.')
        return redirect('services:dashboard')
    
    service_request.status = 'completed'
    service_request.save()
    
    messages.success(request, 'تم إكمال الطلب بنجاح!')
    return redirect('services:dashboard')

@login_required
def rate_engineer(request, request_id):
    service_request = get_object_or_404(ServiceRequest, id=request_id)
    
    if service_request.client != request.user:
        messages.error(request, 'لا يمكنك تقييم هذا الطلب.')
        return redirect('services:dashboard')
    
    if service_request.status != 'completed':
        messages.error(request, 'يجب إكمال الطلب أولاً قبل التقييم.')
        return redirect('services:dashboard')
    
    # الحصول على المهندس
    engineer = None
    if service_request.request_type == 'private':
        engineer = service_request.assigned_engineer
    else:
        accepted_offer = service_request.offers.filter(status='accepted').first()
        if accepted_offer:
            engineer = accepted_offer.engineer
    
    if not engineer:
        messages.error(request, 'لا يمكن العثور على المهندس للتقييم.')
        return redirect('services:dashboard')
    
    # التحقق من وجود تقييم سابق
    if Rating.objects.filter(service_request=service_request).exists():
        messages.error(request, 'لقد قمت بتقييم هذا الطلب مسبقاً.')
        return redirect('services:dashboard')
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.service_request = service_request
            rating.engineer = engineer
            rating.client = request.user
            rating.save()
            messages.success(request, 'تم إضافة التقييم بنجاح!')
            return redirect('services:dashboard')
    else:
        form = RatingForm()
    
    return render(request, 'services/rate_engineer.html', {
        'form': form,
        'service_request': service_request,
        'engineer': engineer
    })

@login_required
def engineer_profile(request, engineer_id):
    engineer = get_object_or_404(User, id=engineer_id, profile__user_type='engineer')
    ratings = Rating.objects.filter(engineer=engineer)
    
    # حساب متوسط التقييم
    if ratings:
        avg_rating = sum(r.stars for r in ratings) / len(ratings)
    else:
        avg_rating = 0
    
    context = {
        'engineer': engineer,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1),
        'total_ratings': len(ratings)
    }
    return render(request, 'services/engineer_profile.html', context)
