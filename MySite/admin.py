from django.contrib import admin
from .models import Student, Event, Payment, EVoucher


# Register your models here.

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'matric_number', 'email')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')


@admin.register(EVoucher)
class EVoucherAdmin(admin.ModelAdmin):
    list_display = ('event', 'student', 'unique_identifier', 'purchase_date', 'status')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('voucher', 'transaction_id', 'amount_paid', 'payment_date')

