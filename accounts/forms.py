from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class SignupForm(UserCreationForm):
    ROLE_CHOICES = (
        ("manager", "Manager"),
        ("employee", "Employee"),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]
