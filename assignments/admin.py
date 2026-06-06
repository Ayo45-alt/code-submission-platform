from django.contrib import admin
from .models import Assignment, TestCase

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 3

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'due_date', 'is_published']
    inlines = [TestCaseInline]

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(TestCase)
