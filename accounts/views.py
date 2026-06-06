from django.contrib.auth.forms import UserCreationForm
from django import forms
from accounts.models import CustomUser
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_lecturer():
                return redirect('lecturer_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_lecturer():
            return redirect('lecturer_dashboard')
        else:
            return redirect('student_dashboard')
    return render(request, 'landing.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_lecturer():
                return redirect('lecturer_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

from django.contrib.auth.decorators import login_required

@login_required
def lecturer_dashboard(request):
    from assignments.models import Assignment
    from submissions.models import Submission
    from accounts.models import CustomUser

    my_assignments = Assignment.objects.filter(created_by=request.user)
    total_assignments = my_assignments.count()
    total_submissions = Submission.objects.filter(assignment__in=my_assignments).count()
    total_students = CustomUser.objects.filter(role='student').count()

    recent_assignments = my_assignments.order_by('-created_at')[:5]

    return render(request, 'accounts/lecturer_dashboard.html', {
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'total_students': total_students,
        'recent_assignments': recent_assignments,
    })

@login_required
def student_dashboard(request):
    from assignments.models import Assignment
    from submissions.models import Submission
    from django.utils import timezone

    active_assignments = Assignment.objects.filter(is_published=True)
    my_submissions = Submission.objects.filter(
        student=request.user
    ).order_by('-submitted_at')
    
    total_submitted = my_submissions.values('assignment').distinct().count()
    average_score = 0
    
    submission_map = {}
    for sub in my_submissions:
        if sub.assignment_id not in submission_map:
            submission_map[sub.assignment_id] = sub

    scores = [s.score for s in submission_map.values()]
    if scores:
        average_score = round(sum(scores) / len(scores), 1)

    return render(request, 'accounts/student_dashboard.html', {
        'active_assignments': active_assignments,
        'total_active': active_assignments.count(),
        'total_submitted': total_submitted,
        'average_score': average_score,
        'now': timezone.now(),
        'submission_map': submission_map,
    })