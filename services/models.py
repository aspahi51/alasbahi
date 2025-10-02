from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save

class Profile(models.Model):
    USER_TYPES = (
        ('client', 'عميل'),
        ('engineer', 'مهندس'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    phone = models.CharField(max_length=15, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f'{self.user.username} - {self.get_user_type_display()}'


class ServiceRequest(models.Model):
  
    REQUEST_TYPES = (
        ('private', 'طلب خاص'),
        ('public', 'طلب عام'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )
    
    title = models.CharField(max_length=250)
    description = models.TextField()
    image = models.ImageField(upload_to='requests/%Y/%m/%d/', blank=True)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
    assigned_engineer = models.ForeignKey( User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='assigned_requests',
        limit_choices_to={'profile__user_type': 'engineer'}
    )
    client = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created']
        
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('services:request_detail', args=[self.id])


# العروض
class Offer(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
    )
    
    service_request = models.ForeignKey(ServiceRequest,on_delete=models.CASCADE,related_name='offers')
    engineer = models.ForeignKey(User, on_delete=models.CASCADE,related_name='offers')
    details = models.TextField()
    duration = models.CharField(max_length=100)  # مثل "3 أيام" أو "أسبوع"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created']
        unique_together = ['service_request', 'engineer']
    
    def __str__(self):
        return f'عرض {self.engineer.username} لـ {self.service_request.title}'



class Rating(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest, 
        on_delete=models.CASCADE,
        related_name='rating'
    )
    engineer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    client = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='given_ratings'
    )
    stars = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f'تقييم {self.client.username} للمهندس {self.engineer.username} - {self.stars} نجوم'




@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance, user_type='client')

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()