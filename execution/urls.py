from django.urls import path
from . import views

urlpatterns = [
    path('run/', views.run_code_view, name='run_code'),
]
