from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

class CustomUser(AbstractUser):
    STUDENT = 'student'
    LECTURER = 'lecturer'

    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (LECTURER, 'Lecturer'),
    ]

    YEAR_CHOICES = [
        ('1', 'Year 1'),
        ('2', 'Year 2'),
        ('3', 'Year 3'),
        ('4', 'Year 4'),
        ('5', 'Year 5'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=STUDENT
    )
    full_name = models.CharField(max_length=200, blank=True, default='')
    matric_number = models.CharField(max_length=20, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    year = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True, default='')

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

    def __str__(self):
        return self.full_name if self.full_name else self.username
    


class CourseClass(models.Model):
    YEAR_CHOICES = [
        ('1', 'Year 1'),
        ('2', 'Year 2'),
        ('3', 'Year 3'),
        ('4', 'Year 4'),
        ('5', 'Year 5'),
    ]

    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100, blank=True, default='')
    year = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True, default='')
    code = models.CharField(max_length=10, unique=True, blank=True)
    lecturer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='classes')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def generate_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not CourseClass.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f"{self.name} — {self.code}"


class ClassMembership(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships')
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'course_class']

    def __str__(self):
        return f"{self.student.username} in {self.course_class.name}"