from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('classes/', views.manage_classes, name='manage_classes'),
    path('classes/create/', views.create_class, name='create_class'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/join/', views.join_class, name='join_class'),
    path('profile/', views.profile_view, name='profile'),
    path('classes/<int:pk>/edit/', views.edit_class, name='edit_class'),
    path('classes/<int:pk>/delete/', views.delete_class, name='delete_class'),
]