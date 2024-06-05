from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Student, Event, Payment, EVoucher
from .serializers import (StudentSerializer, EventSerializer, PaymentSerializer, EVoucherSerializer)


class StudentViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Student objects."""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for student access


class EventViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Event objects."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for event access


class PaymentViewSet(viewsets.ModelViewSet):
    """API endpoint for managing Payment objects."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for payment access


class EVoucherViewSet(viewsets.ModelViewSet):
    """API endpoint for managing EVoucher objects."""
    queryset = EVoucher.objects.all()
    serializer_class = EVoucherSerializer
    permission_classes = [IsAuthenticated]  # Require authentication for voucher access
