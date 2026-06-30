from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('create/', views.create_assignment, name='create_assignment'),
    path('manage/', views.manage_assignments, name='manage_assignments'),
    path('submissions/', views.all_submissions, name='all_submissions'),
    path('submissions/export/', views.export_submissions_csv, name='export_submissions_csv'),
    path('submissions/<int:class_id>/', views.class_submissions, name='class_submissions'),
    path('submissions/<int:class_id>/export/', views.export_class_submissions_csv, name='export_class_submissions_csv'),
    path('<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('<int:pk>/delete/', views.delete_assignment, name='delete_assignment'),
    path('<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('<int:pk>/edit/', views.edit_assignment, name='edit_assignment'),
    
]