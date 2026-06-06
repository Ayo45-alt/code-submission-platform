from django.db import models
from accounts.models import CustomUser

class Assignment(models.Model):
    
    YEAR_CHOICES = [
        ('1', 'Year 1'),
        ('2', 'Year 2'),
        ('3', 'Year 3'),
        ('4', 'Year 4'),
        ('5', 'Year 5'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    department = models.CharField(max_length=100)
    year = models.CharField(max_length=10, choices=YEAR_CHOICES)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(default=100)
    is_published = models.BooleanField(default=False)
    input_format = models.TextField(blank=True, default='', help_text='Describe how input should be read e.g. "First line is the name, second line is the score"')

    def __str__(self):
        return self.title
    

class TestCase(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField(blank=True)
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return f"Test case for {self.assignment.title}"
