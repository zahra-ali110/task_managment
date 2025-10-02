from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from projects.models import Project, Epic, Task
from accounts.models import Profile  # adjust if your Profile model is elsewhere
from accounts.models import Profile  # make sure this is imported

from accounts.models import Profile

@login_required
def dashboard_view(request):
    profile = Profile.objects.get(user=request.user)  # current user profile
    profiles = Profile.objects.all()  # ✅ fetch all team members

    context = {
        "name": request.user.first_name or request.user.username,
        "role": profile.role if profile.role else "N/A",
        "profiles": profiles,   # ✅ pass to template
    }
    return render(request, "dashboard/dashboard.html", context)

@login_required
def calendar_view(request):
    return render(request, "dashboard/calendar.html")