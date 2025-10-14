from django.db import models
from accounts.models import Profile  # using Profile instead of User


class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Project(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField()
    end_date = models.DateField()

    client = models.ForeignKey(  # ✅ link each project to a client
        Client, on_delete=models.CASCADE, related_name="projects", null=True, blank=True
    )

    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='created_projects')
    team_members = models.ManyToManyField(Profile, related_name='projects')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # 🔥 Progress calculation
    def get_progress(self):
        total_items = 0
        completed_items = 0

        for epic in self.epics.all():
            total_items += 1
            if epic.status == "completed":
                completed_items += 1

            for task in epic.tasks.all():
                total_items += 1
                if task.status == "completed":
                    completed_items += 1

                for subtask in task.subtasks.all():
                    total_items += 1
                    if subtask.status == "completed":
                        completed_items += 1

        if total_items == 0:
            return 0

        return int((completed_items / total_items) * 100)

    # ✅ New method to auto-update status
    def update_status(self):
        epics = self.epics.all()
        if not epics.exists():
            return

        if all(epic.status == "completed" for epic in epics):
            self.status = "completed"
        elif any(epic.status == "in_progress" for epic in epics):
            self.status = "in_progress"
        else:
            self.status = "pending"

        self.save(update_fields=["status"])


class Epic(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Relations
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="epics")
    assigned_users = models.ManyToManyField(Profile, related_name="epics", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} → {self.project.name}"

    # ✅ Override save to auto-update project status
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # save epic first
        self.project.update_status()   # then update project status
from django.db import models
from accounts.models import Profile
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum

class Task(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    epic = models.ForeignKey("projects.Epic", on_delete=models.CASCADE, related_name="tasks")
    assigned_users = models.ManyToManyField(Profile, related_name="tasks", blank=True)

    estimated_time = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    tracked_time = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} → {self.epic.title}"

    def save(self, *args, **kwargs):
        """
        Auto-calculate and store estimated_time based on full date+time difference.
        If any of start_date, end_date, start_time, or end_time is missing,
        estimated_time stays 0.00.
        """
        if self.start_date and self.end_date and self.start_time and self.end_time:
            start_dt = datetime.combine(self.start_date, self.start_time)
            end_dt = datetime.combine(self.end_date, self.end_time)

            # handle end before start (overnight or next day)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)

            diff = end_dt - start_dt
            hours = diff.total_seconds() / 3600
            self.estimated_time = Decimal(str(round(hours, 2)))
        else:
            self.estimated_time = Decimal("0.00")

        super().save(*args, **kwargs)

    @property
    def estimated_time_display(self):
        """Convert stored hours → readable days, hours, minutes."""
        hours = float(self.estimated_time)
        total_minutes = round(hours * 60)
        days = total_minutes // (24 * 60)
        hours_left = (total_minutes % (24 * 60)) // 60
        minutes_left = total_minutes % 60

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours_left:
            parts.append(f"{hours_left}h")
        if minutes_left:
            parts.append(f"{minutes_left}m")
        if not parts:
            parts.append("0h")
        return " ".join(parts)

    # ----------------------------
    # NEW METHOD: SUM OF SUBTASKS
    # ----------------------------
    def update_tracked_time(self):
        """
        Recalculate Task.tracked_time as the sum of all its subtasks' time_tracked.
        """
        total = self.subtasks.aggregate(
            total_tracked=Sum('time_tracked')
        )['total_tracked'] or Decimal('0.00')
        self.tracked_time = total
        self.save(update_fields=['tracked_time'])


from django.db import models
from decimal import Decimal
from datetime import timedelta

class SubTask(models.Model):
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    # NEW: store start and end datetimes (replaces the old `deadline` concept)
    start_datetime = models.DateTimeField(blank=True, null=True)
    end_datetime = models.DateTimeField(blank=True, null=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Keep storing estimated_time as decimal hours in DB (for calculations)
    estimated_time = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    time_tracked = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    task = models.ForeignKey("Task", on_delete=models.CASCADE, related_name="subtasks")
    assigned_users = models.ManyToManyField("accounts.Profile", related_name="subtasks", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def completed(self):
        return self.status == "completed"

    # ---------- Helpers ----------
    # Convert total hours → readable days + hours + minutes
    def _format_time(self, total_hours):
        try:
            total_minutes = int(round(float(total_hours) * 60))
        except Exception:
            total_minutes = 0
        days = total_minutes // (24 * 60)
        hours = (total_minutes % (24 * 60)) // 60
        minutes = total_minutes % 60

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if not parts:
            parts.append("0h")
        return " ".join(parts)

    # ---------- Display properties ----------
    # Estimated time display: human readable (e.g. "1d 2h 15m" or "10h")
    @property
    def estimated_time_display(self):
        return self._format_time(self.estimated_time or 0)

    # Time tracked display: full readable format
    @property
    def time_tracked_display(self):
        total_hours = float(self.time_tracked or 0)
        if total_hours == 0:
            return "Today"
        return self._format_time(total_hours)

    def save(self, *args, **kwargs):
        """
        If both start_datetime and end_datetime exist, compute estimated_time
        as decimal hours (with 2 decimal places). If not present, keep existing value.
        """
        try:
            if self.start_datetime and self.end_datetime:
                delta = self.end_datetime - self.start_datetime
                # Prevent negative durations
                if delta.total_seconds() > 0:
                    hours = Decimal(delta.total_seconds() / 3600)
                    # round to 2 decimal places
                    self.estimated_time = hours.quantize(Decimal("0.01"))
                else:
                    self.estimated_time = Decimal("0.00")
        except Exception:
            # fallback: keep existing estimated_time unchanged
            pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} → {self.task.title}"
