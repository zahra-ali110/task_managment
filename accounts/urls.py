from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),  # Landing page
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),  # Dashboard
    path("activate/<uidb64>/<token>/", views.activate_account, name="activate"),
    path('profile/', views.profile_view, name='profile'),
    path("filter-tasks/", views.filter_tasks, name="filter_tasks"),

]
