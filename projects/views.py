from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from datetime import date, datetime
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Task, SubTask, Profile
from accounts.models import Profile
from .models import Project, Epic, Task, SubTask, Client
from .forms import ProjectForm, EpicForm, TaskForm, SubTaskForm, ClientForm

# --------------------------------------------------
# PROJECT VIEWS
# --------------------------------------------------
# PROJECT VIEWS
# --------------------------------------------------
@login_required
def projects(request, client_id=None):
    client = None
    if client_id:
        client = get_object_or_404(Client, pk=client_id)

    # Handle form submission
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        if project_id:  # editing existing project
            project = get_object_or_404(Project, pk=project_id)
            form = ProjectForm(request.POST, instance=project)
        else:  # creating new project
            form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user.profile
            if client:  # link project to client
                project.client = client
            project.save()
            form.save_m2m()

            # redirect back to correct page
            if client:
                return redirect('projects:projects_by_client', client_id=client.id)
            return redirect('projects:projects')
    else:
        form = ProjectForm()

    # Fetch correct projects
    if client:
        projects = Project.objects.filter(client=client).order_by('-created_at')
    else:
        projects = Project.objects.all().order_by('-created_at')

    return render(request, "projects/projects.html", {
        'projects': projects,
        'form': form,
        'client': client,
    })

@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('projects:projects')
    else:
        form = ProjectForm(instance=project)

    projects = Project.objects.all().order_by('-created_at')
    return render(request, "projects/projects.html", {
        'projects': projects,
        'form': form,
        'editing': project
    })


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('projects:projects')
    return render(request, "projects/project_confirm_delete.html", {
        'project': project
    })



# --------------------------------------------------
# EPIC CREATE
# --------------------------------------------------
@login_required
def epic_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        deadline = request.POST.get("deadline")
        priority = request.POST.get("priority")
        assigned_users_ids = request.POST.getlist("assigned_users")
        status = request.POST.get("status")

        if title:  # ✅ only save if there's a title
            epic = Epic.objects.create(
                project=project,
                title=title,
                description=description,
                deadline=deadline if deadline else None,
                priority=priority,
                status=status if status else "pending",
            )

            if assigned_users_ids:
                epic.assigned_users.set(assigned_users_ids)

            # ✅ Redirect back to project detail, open this epic
            return redirect(f"/projects/{project.id}/#epic-{epic.id}")

    return redirect(f"/projects/{project.id}/")


@login_required
def epic_detail(request, pk):
    epic = get_object_or_404(Epic, pk=pk)
    return render(request, "projects/epic_detail.html", {
        "epic": epic,
        "project": epic.project,
    })

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    client = project.client   # 🔥 get the related client

    epics = project.epics.all().order_by('-created_at')
    epic_form = EpicForm()
    profiles = Profile.objects.all()  # ✅ for assigned users in Task form

    progress = project.get_progress()   # ✅ calculate project progress

    return render(request, "projects/epic_task.html", {
        "project": project,
        "client": client,      
        "epics": epics,
        "epic_form": epic_form,
        "profiles": profiles,
        "progress": progress,   # ✅ send to template
    })
# --------------------------------------------------
# TASK CREATE (final fixed version — calculates estimated_time)
# --------------------------------------------------
from datetime import datetime, time
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from .models import Epic, Task


def parse_datetime_local(value):
    """Safely parse datetime-local string (from HTML input) into a time object."""
    if not value:
        return None
    try:
        # Handles both '2025-10-14T10:30' and '10:30'
        if "T" in value:
            return datetime.fromisoformat(value).time()
        return time.fromisoformat(value)
    except ValueError:
        return None


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from accounts.models import Profile
from projects.models import Epic, Task

@login_required
def task_create(request, epic_id):
    epic = get_object_or_404(Epic, id=epic_id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        priority = request.POST.get("priority") or "medium"
        status = request.POST.get("status") or "pending"
        assigned_users_ids = request.POST.getlist("assigned_users")

        # --------------------------
        # Parse datetime-local inputs
        # --------------------------
        start_dt_raw = request.POST.get("start_time")  # format: "YYYY-MM-DDTHH:MM"
        end_dt_raw = request.POST.get("end_time")      # format: "YYYY-MM-DDTHH:MM"

        start_dt = datetime.strptime(start_dt_raw, "%Y-%m-%dT%H:%M") if start_dt_raw else None
        end_dt = datetime.strptime(end_dt_raw, "%Y-%m-%dT%H:%M") if end_dt_raw else None

        # Split into date and time for model fields
        start_date = start_dt.date() if start_dt else None
        start_time = start_dt.time() if start_dt else None
        end_date = end_dt.date() if end_dt else None
        end_time = end_dt.time() if end_dt else None

        # --------------------------
        # Create Task instance
        # --------------------------
        task = Task(
            epic=epic,
            title=title,
            description=description,
            priority=priority,
            status=status,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
        )
        task.save()  # triggers model.save() → calculates estimated_time

        # --------------------------
        # Assign users (if any)
        # --------------------------
        if assigned_users_ids:
            profiles = Profile.objects.filter(id__in=assigned_users_ids)
            task.assigned_users.set(profiles)

        # Redirect to the project page and scroll to the new task
        return redirect(f"/projects/{epic.project.id}/#task-{task.id}")

    # Fallback redirect if not POST
    return redirect(f"/projects/{epic.project.id}/")

# SUBTASK CREATE
# --------------------------------------------------# views.py
# projects/views.py (only the subtask_create function)
from decimal import Decimal

@login_required
def subtask_create(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        start_str = request.POST.get("start_datetime")
        end_str = request.POST.get("end_datetime")
        priority = request.POST.get("priority", "medium")
        assigned_users_ids = request.POST.getlist("assigned_users")

        start_dt = None
        end_dt = None
        estimated_time = Decimal("0.00")

        # Parse datetimes from datetime-local (format: YYYY-MM-DDTHH:MM)
        if start_str and end_str:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
                end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
                delta = end_dt - start_dt
                if delta.total_seconds() > 0:
                    estimated_time = Decimal(delta.total_seconds() / 3600).quantize(Decimal("0.01"))
                else:
                    estimated_time = Decimal("0.00")
            except ValueError:
                start_dt = None
                end_dt = None

        if title:
            subtask = SubTask.objects.create(
                task=task,
                title=title,
                description=description,
                start_datetime=start_dt,
                end_datetime=end_dt,
                priority=priority,
                status="pending",
                estimated_time=estimated_time,
            )

            if assigned_users_ids:
                profiles = Profile.objects.filter(id__in=assigned_users_ids)
                subtask.assigned_users.set(profiles)

            return redirect(f"/projects/{task.epic.project.id}/#subtask-{subtask.id}")

    return redirect(f"/projects/{task.epic.project.id}/#task-{task.id}")

# CLIENT VIEWS
# --------------------------------------------------
@login_required
def clients(request):
    clients = Client.objects.prefetch_related("projects").all()
    form = ClientForm()

    editing = None
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = ClientForm(request.POST, instance=client)
            editing = client
        else:
            form = ClientForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("projects:clients")

    return render(request, "projects/clients.html", {
        "clients": clients,
        "form": form,
        "editing": editing,
    })



@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        client.delete()
        return redirect("projects:clients")
    return redirect("projects:clients")
@login_required
@require_POST
def toggle_subtask_completion(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)

    if subtask.status != "completed":
        subtask.status = "completed"
        subtask.save()

        # ✅ Update parent Task's tracked_time after subtask completion
        subtask.task.update_tracked_time()

        task = subtask.task
        task_completed = False
        epic_completed = False

        if not task.subtasks.filter(status__in=["pending", "in_progress"]).exists():
            task.status = "completed"
            task.save()
            task_completed = True

            epic = task.epic
            if not epic.tasks.filter(status__in=["pending", "in_progress"]).exists():
                epic.status = "completed"
                epic.save()
                epic_completed = True

        # helper to format hours
        def format_time(hours):
            hours = float(hours or 0)
            if hours >= 24:
                days = int(hours // 24)
                hrs = int(hours % 24)
                return f"{days}d {hrs}h" if hrs else f"{days}d"
            return f"{int(hours)}h"

        return JsonResponse({
            "success": True,
            "subtask_id": subtask.id,
            "status": subtask.status,
            "task_id": task.id,
            "task_completed": task_completed,
            "epic_id": task.epic.id,
            "epic_completed": epic_completed,
            "tracked": float(task.tracked_time),             # ✅ aggregated tracked time
            "tracked_display": format_time(task.tracked_time),
        })

    return JsonResponse({"success": False, "error": "Already completed"})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
@login_required
@require_POST
def track_time(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)

    try:
        hours = Decimal(request.POST.get("time_tracked", "0") or "0")
    except (TypeError, ValueError, InvalidOperation):
        return JsonResponse({"success": False, "error": "Invalid time value"}, status=400)

    # accumulate decimal
    subtask.time_tracked = (subtask.time_tracked or Decimal('0')) + hours
    subtask.status = "completed"
    subtask.save()

    # ✅ Update parent Task's tracked_time
    subtask.task.update_tracked_time()

    # propagate completion up the chain if appropriate
    task = subtask.task
    task_completed = False
    epic_completed = False
    if not task.subtasks.filter(status__in=["pending", "in_progress"]).exists():
        task.status = "completed"
        task.save()
        task_completed = True

        epic = task.epic
        if not epic.tasks.filter(status__in=["pending", "in_progress"]).exists():
            epic.status = "completed"
            epic.save()
            epic_completed = True

    return JsonResponse({
        "success": True,
        "subtask_id": subtask.id,
        "time_tracked": float(subtask.time_tracked),
        "task_tracked_time": float(task.tracked_time),  # ✅ send aggregated tracked time
        "status": subtask.status,
        "task_id": task.id,
        "task_completed": task_completed,
        "epic_id": task.epic.id,
        "epic_completed": epic_completed
    })



# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import SubTask

@require_POST
@login_required
def complete_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id)

    # Only update if not already completed
    if subtask.status != "completed":
        subtask.status = "completed"
        subtask.save()
        return JsonResponse({"success": True, "subtask_id": subtask.id})
    
    return JsonResponse({"success": False, "error": "Already completed"})



 
@login_required
@require_POST
def toggle_task_completion(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if task.status != "completed":
        # only allow marking complete if all subtasks are done
        if task.subtasks.filter(status__in=["pending", "in_progress"]).exists():
            return JsonResponse({"success": False, "error": "Complete all subtasks first"})

        task.status = "completed"
        task.save()

        epic = task.epic
        if epic.tasks.filter(status__in=["pending", "in_progress"]).count() == 0:
            epic.status = "completed"
            epic.save()

        return JsonResponse({
            "success": True,
            "task_id": task.id,
            "status": task.status
        })

    return JsonResponse({"success": False, "error": "Already completed"})

@login_required
@require_POST
def toggle_epic_completion(request, epic_id):
    epic = get_object_or_404(Epic, id=epic_id)

    if epic.status != "completed":
        # ✅ first check: all tasks must be completed
        if epic.tasks.filter(status__in=["pending", "in_progress"]).exists():
            return JsonResponse({"success": False, "error": "Complete all tasks first"})

        # ✅ second check: make sure no subtasks are incomplete
        for task in epic.tasks.all():
            if task.subtasks.filter(status__in=["pending", "in_progress"]).exists():
                return JsonResponse({"success": False, "error": f"Complete all subtasks in task '{task.title}' first"})

        # if passed both checks → mark epic as completed
        epic.status = "completed"
        epic.save()
        return JsonResponse({"success": True, "epic_id": epic.id, "status": epic.status})

    return JsonResponse({"success": False, "error": "Already completed"})



@login_required
def can_complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    allowed = not task.subtasks.filter(status__in=["pending", "in_progress"]).exists()
    return JsonResponse({"allowed": allowed})

@login_required
def can_complete_epic(request, epic_id):
    epic = get_object_or_404(Epic, id=epic_id)
    allowed = not epic.tasks.filter(status__in=["pending", "in_progress"]).exists()
    return JsonResponse({"allowed": allowed})



@login_required
def task_can_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    allowed = not task.subtasks.filter(status__in=["pending", "in_progress"]).exists()
    return JsonResponse({"allowed": allowed})

@login_required
def epic_can_complete(request, epic_id):
    epic = get_object_or_404(Epic, id=epic_id)
    allowed = not epic.tasks.filter(status__in=["pending", "in_progress"]).exists()
    return JsonResponse({"allowed": allowed})



@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, "projects/task_detail.html", {
        "task": task,
        "epic": task.epic,
        "project": task.epic.project,
    })


@login_required
def subtask_detail(request, pk):
    subtask = get_object_or_404(SubTask, pk=pk)
    return render(request, "projects/subtask_detail.html", {
        "subtask": subtask,
        "task": subtask.task,
        "epic": subtask.task.epic,
        "project": subtask.task.epic.project,
    })




# ----------------- DASHBOARD -----------------
@login_required
def dashboard_view(request):
    return render(request, "dashboard/dashboard.html", context)