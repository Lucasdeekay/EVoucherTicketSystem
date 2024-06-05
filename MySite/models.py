from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)
    matric_number = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)  # Ensure unique email


class Event(models.Model):
    """Model for storing event information."""
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EVoucher(models.Model):
    """Model for storing e-voucher information."""
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    unique_identifier = models.CharField(max_length=100, unique=True)
    purchase_date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='voucher_images/')
    status = models.CharField(max_length=20, choices=(('UNUSED', 'Unused'), ('USED', 'Used')), default='UNUSED')

    def __str__(self):
        return f"E-Voucher for {self.event.name} - {self.unique_identifier}"


class Payment(models.Model):
    """Model for storing payment information."""
    voucher = models.ForeignKey(EVoucher, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=255, unique=True)  # Store unique transaction ID
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Voucher - {self.voucher}"
