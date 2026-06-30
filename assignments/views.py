from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Assignment, TestCase


@login_required
def assignment_list(request):
    if request.user.is_lecturer():
        assignments = Assignment.objects.filter(is_published=True)
        context = {
            'assignments': assignments
        }
    else:
        from accounts.models import ClassMembership
        from submissions.models import Submission
        my_class_ids = ClassMembership.objects.filter(
            student=request.user
        ).values_list('course_class_id', flat=True)

        assignments = list(Assignment.objects.filter(
            is_published=True,
            course_class_id__in=my_class_ids
        ))
        
        submitted_assignments = 0
        scores = []
        
        for assignment in assignments:
            user_subs = Submission.objects.filter(
                student=request.user,
                assignment=assignment
            )
            assignment.submission_count = user_subs.count()
            if assignment.submission_count > 0:
                best_sub = user_subs.order_by('-score').first()
                assignment.best_score = best_sub.score
                assignment.attempts_remaining = max(0, 3 - assignment.submission_count)
                submitted_assignments += 1
                scores.append(best_sub.score)
            else:
                assignment.best_score = None
                assignment.attempts_remaining = 3
        
        total_assignments = len(assignments)
        completion_rate = int((submitted_assignments / total_assignments) * 100) if total_assignments > 0 else 0
        avg_score = int(sum(scores) / len(scores)) if len(scores) > 0 else 0

        context = {
            'assignments': assignments,
            'total_assignments': total_assignments,
            'submitted_assignments': submitted_assignments,
            'completion_rate': completion_rate,
            'avg_score': avg_score,
        }

    return render(request, 'assignments/assignment_list.html', context)

@login_required
def assignment_detail(request, pk):
    from submissions.models import Submission
    assignment = get_object_or_404(Assignment, pk=pk)

    submission_count = Submission.objects.filter(
        student=request.user,
        assignment=assignment
    ).count()

    attempts_remaining = max(0, 3 - submission_count)

    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'attempts_remaining': attempts_remaining,
        'submission_count': submission_count,
    })


@login_required
def create_assignment(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    from accounts.models import CourseClass
    my_classes = CourseClass.objects.filter(lecturer=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score', 100)
        is_published = request.POST.get('is_published') == 'on'
        input_format = request.POST.get('input_format', '')
        course_class_id = request.POST.get('course_class')

        if not course_class_id:
            return render(request, 'assignments/create_assignment.html', {
                'now': timezone.now(),
                'my_classes': my_classes,
                'error': 'Please select a class for this assignment.',
            })

        course_class = get_object_or_404(CourseClass, pk=course_class_id, lecturer=request.user)

        assignment = Assignment.objects.create(
            title=title,
            description=description,
            department=course_class.department,
            year=course_class.year,
            due_date=due_date,
            max_score=max_score,
            is_published=is_published,
            input_format=input_format,
            created_by=request.user,
            course_class=course_class,
        )

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

    return render(request, 'assignments/create_assignment.html', {
        'now': timezone.now(),
        'my_classes': my_classes,
    })

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

        # Update test cases
        assignment.test_cases.all().delete()
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

        return redirect('manage_assignments')

    return render(request, 'assignments/edit_assignment.html', {
        'assignment': assignment,
        'now': timezone.now(),
    })

@login_required
def all_submissions(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    from submissions.models import Submission
    from accounts.models import CourseClass

    assignments = Assignment.objects.filter(created_by=request.user)

    subs = Submission.objects.filter(
        assignment__in=assignments
    ).select_related('assignment__course_class')

    seen = set()
    latest_submissions = []
    for sub in subs:
        key = (sub.student_id, sub.assignment_id)
        if key not in seen:
            seen.add(key)
            latest_submissions.append(sub)

    class_data = {}
    no_class_subs = []

    for sub in latest_submissions:
        course_class = sub.assignment.course_class
        if course_class:
            if course_class.id not in class_data:
                class_data[course_class.id] = {
                    'course_class': course_class,
                    'submissions': [],
                }
            class_data[course_class.id]['submissions'].append(sub)
        else:
            no_class_subs.append(sub)

    class_cards = []
    for data in class_data.values():
        subs_list = data['submissions']
        total = len(subs_list)
        avg = round(sum(s.score for s in subs_list) / total, 1) if total else 0
        class_cards.append({
            'course_class': data['course_class'],
            'total': total,
            'avg_score': avg,
        })

    class_cards.sort(key=lambda c: c['course_class'].name)

    total_overall = len(latest_submissions)
    avg_overall = round(sum(s.score for s in latest_submissions) / total_overall, 1) if total_overall else 0

    return render(request, 'assignments/all_submissions.html', {
        'class_cards': class_cards,
        'no_class_count': len(no_class_subs),
        'total': total_overall,
        'avg_score': avg_overall,
    })


@login_required
def class_submissions(request, class_id):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    from submissions.models import Submission
    from accounts.models import CourseClass

    course_class = get_object_or_404(CourseClass, pk=class_id, lecturer=request.user)

    assignments = Assignment.objects.filter(
        created_by=request.user, course_class=course_class
    ).order_by('-created_at')

    subs = Submission.objects.filter(
        assignment__in=assignments
    ).select_related('student', 'assignment').order_by('-submitted_at')

    seen = set()
    latest_submissions = []
    for sub in subs:
        key = (sub.student_id, sub.assignment_id)
        if key not in seen:
            seen.add(key)
            latest_submissions.append(sub)

    # Group by assignment
    grouped = {}
    for sub in latest_submissions:
        aid = sub.assignment_id
        if aid not in grouped:
            grouped[aid] = {
                'assignment': sub.assignment,
                'submissions': [],
            }
        grouped[aid]['submissions'].append(sub)

    # Keep assignment order (newest assignment first), even ones with zero submissions
    assignment_groups = []
    for assignment in assignments:
        group = grouped.get(assignment.id)
        subs_list = group['submissions'] if group else []
        total = len(subs_list)
        avg = round(sum(s.score for s in subs_list) / total, 1) if total else 0
        assignment_groups.append({
            'assignment': assignment,
            'submissions': subs_list,
            'total': total,
            'avg_score': avg,
        })

    total = len(latest_submissions)
    avg_score = round(sum(s.score for s in latest_submissions) / total, 1) if total else 0

    return render(request, 'assignments/class_submissions.html', {
        'course_class': course_class,
        'assignment_groups': assignment_groups,
        'total': total,
        'avg_score': avg_score,
    })


@login_required
def export_submissions_csv(request):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    import csv
    from django.http import HttpResponse
    from submissions.models import Submission

    assignments = Assignment.objects.filter(created_by=request.user)

    subs = Submission.objects.filter(
        assignment__in=assignments
    ).select_related('student', 'assignment', 'assignment__course_class').order_by(
        'assignment__course_class__name', 'assignment__title', '-submitted_at'
    )

    seen = set()
    latest_submissions = []
    for sub in subs:
        key = (sub.student_id, sub.assignment_id)
        if key not in seen:
            seen.add(key)
            latest_submissions.append(sub)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_submissions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Class', 'Assignment', 'Student Name', 'Matric Number', 'Score', 'Max Score', 'Status', 'Submitted At'])

    for sub in latest_submissions:
        class_name = sub.assignment.course_class.name if sub.assignment.course_class else 'No Class Assigned'
        writer.writerow([
            class_name,
            sub.assignment.title,
            sub.student.full_name or sub.student.username,
            sub.student.matric_number or '',
            sub.score,
            sub.assignment.max_score,
            sub.status,
            sub.submitted_at.strftime('%b %d, %Y, %I:%M %p'),
        ])

    return response

@login_required
def export_class_submissions_csv(request, class_id):
    if not request.user.is_lecturer():
        return redirect('student_dashboard')

    import csv
    from django.http import HttpResponse
    from submissions.models import Submission
    from accounts.models import CourseClass

    course_class = get_object_or_404(CourseClass, pk=class_id, lecturer=request.user)
    assignments = Assignment.objects.filter(created_by=request.user, course_class=course_class)

    subs = Submission.objects.filter(
        assignment__in=assignments
    ).select_related('student', 'assignment').order_by('assignment__title', '-submitted_at')

    seen = set()
    latest_submissions = []
    for sub in subs:
        key = (sub.student_id, sub.assignment_id)
        if key not in seen:
            seen.add(key)
            latest_submissions.append(sub)

    response = HttpResponse(content_type='text/csv')
    filename = f"{course_class.name.replace(' ', '_')}_submissions.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Assignment', 'Student Name', 'Matric Number', 'Score', 'Max Score', 'Status', 'Submitted At'])

    for sub in latest_submissions:
        writer.writerow([
            sub.assignment.title,
            sub.student.full_name or sub.student.username,
            sub.student.matric_number or '',
            sub.score,
            sub.assignment.max_score,
            sub.status,
            sub.submitted_at.strftime('%b %d, %Y, %I:%M %p'),
        ])

    return response