from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    STUDENT = 'student'
    LECTURER = 'lecturer'
    
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (LECTURER, 'Lecturer'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=STUDENT
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True
    )

    def is_lecturer(self):
        return self.role == self.LECTURER

    def is_student(self):
        return self.role == self.STUDENT