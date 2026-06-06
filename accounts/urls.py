from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
]