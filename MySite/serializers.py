from rest_framework import serializers
from .models import Student, Event, Payment, EVoucher


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class EVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = EVoucher
        fields = '__all__'
