from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),  # /dashboard/
    path('calendar/', views.calendar_view, name='calendar'),  # /dashboard/calendar/
]
