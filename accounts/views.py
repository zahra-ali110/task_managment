from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile   # <-- Profile model
from django.contrib.auth.decorators import login_required

# ----------------- Landing page -----------------
def index(request):
    return render(request, "accounts/index.html")
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

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

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        # 🔥 Create user but set inactive until verification
        user = User.objects.create_user(
            username=full_name,
            email=email,
            password=password1,
            first_name=full_name,
            is_active=False
        )

        profile, created = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        # ✅ Send verification email
        current_site = get_current_site(request)
        subject = "Verify your email - TaskFlow"
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_url = f"http://{current_site.domain}/activate/{uid}/{token}/"

        message = render_to_string("accounts/verify_email.html", {
            "user": user,
            "verify_url": verify_url,
        })

        send_mail(subject, message, "no-reply@taskflow.com", [email])

        messages.success(request, "Account created! Please check your email to verify your account.")
        return redirect("login")

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



def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been verified! You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect("signup")

from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
# accounts/views.py
from django.shortcuts import render
from django.db.models import Q
from projects.models import Project, Epic, Task, SubTask
from django.core.serializers import serialize
from django.http import JsonResponse
import json
from django.utils.timezone import now
@login_required
def profile_view(request):
    from django.utils.timezone import now
    import json
    from django.db.models import Q

    profile = request.user.profile
    today = now().date()

    # Base data
    projects = Project.objects.filter(Q(team_members=profile) | Q(created_by=profile)).distinct()
    epics = Epic.objects.filter(assigned_users=profile).distinct()
    tasks = Task.objects.filter(assigned_users=profile).distinct()
    subtasks = SubTask.objects.filter(assigned_users=profile).distinct()

    assigned_to_me = Task.objects.filter(assigned_users=profile).exclude(status="completed").distinct()

    # Determine "assigned_by_me" tasks
    task_fields = [f.name for f in Task._meta.get_fields()]
    if "project" in task_fields:
        assigned_by_me = Task.objects.filter(Q(epic__project__in=projects)).exclude(assigned_users=profile).distinct()
    elif "epic" in task_fields:
        assigned_by_me = Task.objects.filter(Q(epic__in=epics)).exclude(assigned_users=profile).distinct()
    else:
        assigned_by_me = Task.objects.none()

    all_items = list(projects) + list(epics) + list(tasks) + list(subtasks)
    task_data = []

    for obj in all_items:
        # Determine actual deadline safely
        deadline = None
        if isinstance(obj, Project):
            deadline = obj.end_date
        elif isinstance(obj, Epic):
            deadline = obj.deadline
        elif isinstance(obj, Task):
            deadline = obj.deadline or (obj.epic.deadline if obj.epic else None)
        elif isinstance(obj, SubTask):
            deadline = obj.deadline or (obj.task.deadline if obj.task else None)

        # Status
        status = getattr(obj, "status", "pending")

        # Overdue check
        is_overdue = False
        if deadline:
            due_date = deadline if isinstance(deadline, (str,)) else deadline
            if due_date < today and status.lower() != "completed":
                is_overdue = True

        # Safe project title
        project_title = ""
        if isinstance(obj, Project):
            project_title = obj.name
        elif isinstance(obj, Epic) and obj.project:
            project_title = obj.project.name
        elif isinstance(obj, Task) and obj.epic and obj.epic.project:
            project_title = obj.epic.project.name
        elif isinstance(obj, SubTask) and obj.task and obj.task.epic and obj.task.epic.project:
            project_title = obj.task.epic.project.name

        # Assignees
        assignees = ""
        if hasattr(obj, "assigned_users"):
            assignees = ", ".join([str(u) for u in obj.assigned_users.all()])

        # Created by
        created_by_name = getattr(obj, "created_by", None)
        if not created_by_name:
            created_by_name = profile.user.get_full_name() if hasattr(profile, "user") else "Unknown"

        # Append to task_data
        task_data.append({
            "id": obj.id,
            "name": getattr(obj, "title", getattr(obj, "name", "Untitled")),
            "status": status,
            "deadline": deadline.strftime("%B %d, %I:%M %p") if deadline else "Not available",
            "createdBy": str(created_by_name),
            "assignee": assignees,
            "project": project_title,
            "role": "Owner" if getattr(obj, "created_by", None) == profile else "Assigned",
            "starred": False,
            "is_overdue": is_overdue,
        })

    # Stats summary
    overdue = sum(1 for item in task_data if item["is_overdue"])
    pending = sum(1 for item in task_data if item["status"].lower() == "pending")
    ongoing = sum(1 for item in task_data if item["status"].lower() in ["in_progress", "ongoing"])
    completed = sum(1 for item in task_data if item["status"].lower() == "completed")

    name = request.user.get_full_name() or request.user.username
    email = request.user.email
    role = getattr(profile, 'role', 'Employee')

    context = {
        "profile": profile,
        "name": name,
        "email": email,
        "role": role.title(),
        "overdueCount": overdue,
        "pendingCount": pending,
        "ongoingCount": ongoing,
        "completedCount": completed,
        "tasks_json": json.dumps(task_data),
        "assigned_to_me": assigned_to_me,
        "assigned_by_me": assigned_by_me,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def filter_tasks(request):
    profile = Profile.objects.get(user=request.user)
    role = request.GET.get("role")
    date = request.GET.get("date")

    tasks = Task.objects.all()

    if role == "owner":
        tasks = tasks.filter(epic__created_by=profile)
    elif role == "assigned":
        tasks = tasks.filter(assigned_users=profile)
    if date:
        tasks = tasks.filter(deadline=date)

    # Convert to JSON-friendly data
    data = []
    for t in tasks:
        data.append({
            "name": t.name,
            "status": t.status,
            "deadline": t.deadline.strftime("%Y-%m-%d") if t.deadline else None,
            "createdBy": t.epic.created_by.user.username if hasattr(t, 'epic') and t.epic.created_by else "N/A",
            "assignee": ", ".join([u.user.username for u in t.assigned_users.all()]) or "N/A",
            "project": t.epic.project.name if hasattr(t, 'epic') and t.epic.project else "N/A",
            "role": role or "N/A",
        })

    return JsonResponse({"tasks": data})