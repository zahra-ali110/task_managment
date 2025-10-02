from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile   # <-- Profile model
from django.contrib.auth.decorators import login_required

# ----------------- Landing page -----------------
def index(request):
    return render(request, "accounts/index.html")


# ----------------- SIGNUP -----------------
def signup_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        user = User.objects.create_user(
            username=full_name,        # ✅ save full name as username
            email=email,
            password=password1,
            first_name=full_name
        )

        # ✅ fix: create OR update profile
        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect("dashboard")

    return render(request, "accounts/signup.html")


# ----------------- LOGIN -----------------
from django.contrib.auth.models import User

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)  # ✅ find by email
            user = authenticate(request, username=user_obj.username, password=password)  
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "accounts/login.html")

    return render(request, "accounts/login.html")

# ----------------- LOGOUT -----------------
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


# ----------------- DASHBOARD -----------------
# ----------------- DASHBOARD -----------------
@login_required
def dashboard_view(request):
    profile = Profile.objects.get(user=request.user)  # fetch the profile

    context = {
        "name": request.user.first_name or request.user.username,
        "role": profile.role if profile.role else "N/A",
    }

    return render(request, "dashboard/dashboard.html", context)
