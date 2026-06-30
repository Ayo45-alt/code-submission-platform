from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import CustomUser, CourseClass, ClassMembership


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'full_name', 'matric_number', 'department', 'year', 'password1', 'password2']

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


@login_required
def lecturer_dashboard(request):
    from assignments.models import Assignment
    from submissions.models import Submission

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
        'now': timezone.now(),
    })


@login_required
def student_dashboard(request):
    from assignments.models import Assignment
    from submissions.models import Submission

    my_class_ids = ClassMembership.objects.filter(
        student=request.user
    ).values_list('course_class_id', flat=True)

    my_submissions = Submission.objects.filter(
        student=request.user
    ).order_by('-submitted_at')

    submitted_assignment_ids = my_submissions.values_list('assignment_id', flat=True)

    active_assignments = Assignment.objects.filter(
        is_published=True,
        due_date__gt=timezone.now(),
        course_class_id__in=my_class_ids
    ).exclude(
        id__in=submitted_assignment_ids
    )

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


@login_required
def manage_classes(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    classes = CourseClass.objects.filter(lecturer=request.user)
    return render(request, 'accounts/manage_classes.html', {
        'classes': classes,
    })


@login_required
def create_class(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        department = request.POST.get('department')
        year = request.POST.get('year')
        CourseClass.objects.create(
            name=name,
            department=department,
            year=year,
            lecturer=request.user
        )
        return redirect('manage_classes')

    return render(request, 'accounts/create_class.html')


@login_required
def class_detail(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    course_class = get_object_or_404(CourseClass, pk=pk, lecturer=request.user)
    members = course_class.members.all().select_related('student')

    return render(request, 'accounts/class_detail.html', {
        'course_class': course_class,
        'members': members,
    })


@login_required
def join_class(request):
    if not request.user.is_student():
        return redirect('lecturer_dashboard')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        try:
            course_class = CourseClass.objects.get(code=code)
            membership, created = ClassMembership.objects.get_or_create(
                student=request.user,
                course_class=course_class
            )
            if created:
                messages.success(request, f'Successfully joined {course_class.name}!')
            else:
                messages.error(request, 'You are already in this class.')
        except CourseClass.DoesNotExist:
            messages.error(request, 'Invalid class code. Please check and try again.')

        return redirect('student_dashboard')

    return render(request, 'accounts/join_class.html')

@login_required
def profile_view(request):
    if request.method == 'POST':
        request.user.full_name = request.POST.get('full_name', '')
        request.user.department = request.POST.get('department', '')
        if request.user.is_student():
            request.user.matric_number = request.POST.get('matric_number', '')
            request.user.year = request.POST.get('year', '')
        request.user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'accounts/profile.html')

@login_required
def delete_class(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    course_class = get_object_or_404(CourseClass, pk=pk, lecturer=request.user)

    if request.method == 'POST':
        course_class.delete()
        messages.success(request, f'{course_class.name} has been deleted.')
        return redirect('manage_classes')

    return redirect('manage_classes')

@login_required
def edit_class(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    course_class = get_object_or_404(CourseClass, pk=pk, lecturer=request.user)

    if request.method == 'POST':
        course_class.name = request.POST.get('name')
        course_class.department = request.POST.get('department')
        course_class.year = request.POST.get('year')
        course_class.save()
        messages.success(request, f'Class "{course_class.name}" updated successfully!')
        return redirect('class_detail', pk=course_class.pk)

    return render(request, 'accounts/edit_class.html', {
        'course_class': course_class,
    })