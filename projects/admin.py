from django.contrib import admin
from .models import Project, Epic, Task, SubTask, Client


# -------------------------
# Project Admin
# -------------------------
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "start_date", "end_date", "created_by")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("name", "description")


# -------------------------
# Epic Admin
# -------------------------
@admin.register(Epic)
class EpicAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "priority", "status", "deadline", "get_assigned_users")
    list_filter = ("priority", "status", "project")
    search_fields = ("title", "description")

    def get_assigned_users(self, obj):
        return ", ".join([user.user.username for user in obj.assigned_users.all()])
    get_assigned_users.short_description = "Assigned Users"
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "epic",
        "priority",
        "status",
        "estimated_time",
        "tracked_time",
        "get_assigned_users",
    )
    list_filter = ("priority", "status", "epic")
    search_fields = ("title", "description")

    def get_assigned_users(self, obj):
        return ", ".join([user.user.username for user in obj.assigned_users.all()])
    get_assigned_users.short_description = "Assigned Users"

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "task",
        "priority",
        "status",
        "start_datetime",
        "end_datetime",
        "get_assigned_users",
        "estimated_time",
        "time_tracked",
    )
    list_filter = ("priority", "status", "task")
    search_fields = ("title", "description")

    def get_assigned_users(self, obj):
        return ", ".join([user.user.username for user in obj.assigned_users.all()])
    get_assigned_users.short_description = "Assigned Users"


# -------------------------
# Client Admin (NEW)
# -------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "address")
    search_fields = ("name", "email", "phone")


