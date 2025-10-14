from django import forms
from .models import Project, Epic, Task, SubTask, Client
from accounts.models import Profile


# -------------------------
# Project Form (unchanged)
# -------------------------
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'start_date', 'end_date', 'team_members']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': 'Project Name',
            'description': 'Project Description',
            'status': 'Project Status',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'team_members': 'Team Members',
        }

    team_members = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )


# -------------------------
# Epic Form (unchanged)
# -------------------------
class EpicForm(forms.ModelForm):
    class Meta:
        model = Epic
        fields = ["title", "description", "deadline", "priority", "status", "assigned_users"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "assigned_users": forms.SelectMultiple(attrs={"class": "form-multiselect"}),
        }
        labels = {
            "title": "Epic Title",
            "description": "Epic Description",
            "deadline": "Deadline",
            "priority": "Priority",
            "status": "Status",
            "assigned_users": "Assigned Users",
        }
from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "priority", "status", "assigned_users", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "assigned_users": forms.SelectMultiple(attrs={"class": "form-multiselect"}),
        }


from django import forms
from .models import SubTask

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = [
            "title",
            "description",
            "start_datetime",
            "end_datetime",
            "priority",
            "status",
            "assigned_users",
            "time_tracked",
        ]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "assigned_users": forms.SelectMultiple(attrs={"class": "form-multiselect"}),
        }
        labels = {
            "title": "SubTask Title",
            "description": "SubTask Description",
            "start_datetime": "Start Date & Time",
            "end_datetime": "End Date & Time",
            "priority": "Priority",
            "status": "Status",
            "assigned_users": "Assigned Users",
            "time_tracked": "Time Tracked (hrs)",
        }

# -------------------------
# Client Form (NEW)
# -------------------------
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "address", "email", "phone"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "email": forms.EmailInput(),
            "phone": forms.TextInput(),
        }
        labels = {
            "name": "Client Name",
            "address": "Client Address",
            "email": "Email",
            "phone": "Phone Number",
        }
