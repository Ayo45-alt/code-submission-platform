from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Assignment
from django.utils import timezone

@login_required
def assignment_list(request):
    assignments = Assignment.objects.filter(is_published=True)
    return render(request, 'assignments/assignment_list.html', {
        'assignments': assignments
    })

@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Assignment, TestCase

@login_required
def create_assignment(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        department = request.POST.get('department')
        year = request.POST.get('year')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score', 100)
        is_published = request.POST.get('is_published') == 'on'
        input_format = request.POST.get('input_format', ''),

        assignment = Assignment.objects.create(
            title=title,
            description=description,
            department=department,
            year=year,
            due_date=due_date,
            max_score=max_score,
            is_published=is_published,
            created_by=request.user
        )

        # Save test cases
        inputs = request.POST.getlist('input_data')
        outputs = request.POST.getlist('expected_output')
        hidden = request.POST.getlist('is_hidden')

        for i in range(len(inputs)):
            if outputs[i].strip():
                TestCase.objects.create(
                    assignment=assignment,
                    input_data=inputs[i],
                    expected_output=outputs[i],
                    is_hidden=str(i) in hidden
                )

        return redirect('lecturer_dashboard')

    return render(request, 'assignments/create_assignment.html')

@login_required
def manage_assignments(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')
    
    assignments = Assignment.objects.filter(
        created_by=request.user
    ).order_by('-created_at')
    
    assignment_data = []
    for assignment in assignments:
        submission_count = assignment.submission_set.count()
        assignment_data.append({
            'assignment': assignment,
            'submission_count': submission_count,
        })
    
    return render(request, 'assignments/manage_assignments.html', {
        'assignment_data': assignment_data,
    })

@login_required
def delete_assignment(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        assignment.delete()
        return redirect('manage_assignments')
    
    return redirect('manage_assignments')

@login_required
def assignment_submissions(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    
    all_submissions = assignment.submission_set.all().order_by('-submitted_at')
    
    seen_students = set()
    latest_submissions = []
    for sub in all_submissions:
        if sub.student_id not in seen_students:
            seen_students.add(sub.student_id)
            latest_submissions.append(sub)
    
    total = len(latest_submissions)
    avg_score = 0
    if total > 0:
        avg_score = round(sum([s.score for s in latest_submissions]) / total, 1)
    
    return render(request, 'assignments/assignment_submissions.html', {
        'assignment': assignment,
        'submissions': latest_submissions,
        'total': total,
        'avg_score': avg_score,
    })

@login_required
def edit_assignment(request, pk):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')
    
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        assignment.title = request.POST.get('title')
        assignment.description = request.POST.get('description')
        assignment.input_format = request.POST.get('input_format', '')
        assignment.department = request.POST.get('department')
        assignment.year = request.POST.get('year')
        assignment.due_date = request.POST.get('due_date')
        assignment.max_score = request.POST.get('max_score', 100)
        assignment.is_published = request.POST.get('is_published') == 'on'
        assignment.save()
        return redirect('manage_assignments')
    
    return render(request, 'assignments/edit_assignment.html', {
        'assignment': assignment,
        'now': timezone.now(),
    })