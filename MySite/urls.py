from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .viewset import (StudentViewSet, EventViewSet, PaymentViewSet, EVoucherViewSet)

router = DefaultRouter()
router.register('students', StudentViewSet, basename='students')
router.register('events', EventViewSet, basename='events')
router.register('payments', PaymentViewSet, basename='payments')
router.register('evouchers', EVoucherViewSet, basename='evouchers')

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<int:reset_uid>/', views.retrieve_password_view, name='retrieve_password'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('initiate-payment/', views.initiate_voucher_payment, name='initiate_voucher_payment'),
    path('verify-payment/', views.verify_voucher_payment, name='verify_voucher_payment'),
    path('download-voucher/<int:voucher_id>/', views.download_voucher_image, name='download_voucher_image'),
    path('scan-qr-code/', views.scan_qr_code, name='scan_qr_code'),
    path('api/', include(router.urls)),
]
