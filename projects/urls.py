from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    # ------------------------
    # PROJECT ROUTES
    # ------------------------
    path("", views.projects, name="projects"),  # all projects
    path("client/<int:client_id>/", views.projects, name="projects_by_client"),

    path("edit/<int:pk>/", views.project_edit, name="project_edit"),
    path("delete/<int:pk>/", views.project_delete, name="project_delete"),
    path("<int:pk>/", views.project_detail, name="project_detail"),

    # ------------------------
    # EPIC ROUTES
    # ------------------------
    path("epic/create/<int:project_id>/", views.epic_create, name="epic_create"),
    path("epic/<int:pk>/", views.epic_detail, name="epic_detail"),

    # ------------------------
    # TASK ROUTES
    # ------------------------
    path("task/create/<int:epic_id>/", views.task_create, name="task_create"),
    path("subtask/create/<int:task_id>/", views.subtask_create, name="subtask_create"),
  
    path("subtask/<int:subtask_id>/toggle/", views.toggle_subtask_completion, name="toggle_subtask_completion"),

    # ------------------------
    # CLIENT ROUTES
    # ------------------------
    path("clients/", views.clients, name="clients"),
    path("clients/delete/<int:pk>/", views.client_delete, name="client_delete"),

    path("subtask/<int:subtask_id>/track-time/", views.track_time, name="track_time"),
    path('subtask/<int:subtask_id>/complete/', views.complete_subtask, name='subtask_complete'),

  path('epic/<int:epic_id>/toggle/', views.toggle_epic_completion, name='toggle_epic_completion'),
  path('task/<int:task_id>/toggle/', views.toggle_task_completion, name='toggle_task_completion'),
  path("task/<int:task_id>/can-complete/", views.can_complete_task, name="can_complete_task"),
  path("epic/<int:epic_id>/can-complete/", views.can_complete_epic, name="can_complete_epic"),
path('task/<int:task_id>/can-complete/', views.task_can_complete, name='task_can_complete'),
path('epic/<int:epic_id>/can-complete/', views.epic_can_complete, name='epic_can_complete'),
# TASK ROUTES
path("task/<int:pk>/", views.task_detail, name="task_detail"),

# SUBTASK ROUTES
path("subtask/<int:pk>/", views.subtask_detail, name="subtask_detail"),

]
