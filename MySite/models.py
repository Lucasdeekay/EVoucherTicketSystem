from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)
    middle_name = models.CharField(max_length=255, blank=True)  # Optional middle name
    matric_number = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)  # Ensure unique email