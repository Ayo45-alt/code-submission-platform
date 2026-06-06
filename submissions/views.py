from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from assignments.models import Assignment
from .models import Submission
from execution.runner import run_code
from django.utils import timezone

@login_required
def submit_code(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    
    if request.method == 'POST':
        code = request.POST.get('code', '')
        
        if not code.strip():
            messages.error(request, 'Please write some code before submitting!')
            return redirect('assignment_detail', pk=assignment_id)
        
        # Create submission
        submission = Submission.objects.create(
            student=request.user,
            assignment=assignment,
            code=code,
            status='running'
        )
        
        # Run against each test case
        test_cases = assignment.test_cases.all()
        total_cases = test_cases.count()
        passed_cases = 0
        feedback_lines = []
        
        for i, test_case in enumerate(test_cases, 1):
            result = run_code(code, test_case.input_data)
            actual_output = result['stdout'].strip()
            expected_output = test_case.expected_output.strip()
            
            if actual_output == expected_output:
                passed_cases += 1
                if not test_case.is_hidden:
                    feedback_lines.append(f'Test {i}: ✅ Passed')
            else:
                if not test_case.is_hidden:
                    feedback_lines.append(f'Test {i}: ❌ Failed')
                    feedback_lines.append(f'  Your output: {actual_output}')
                    feedback_lines.append(f'  Expected: {expected_output}')
                else:
                    feedback_lines.append(f'Test {i}: ❌ Failed (hidden test case)')
            
            if result['stderr'] and not test_case.is_hidden:
                feedback_lines.append(f'  Error: {result["stderr"]}')
        
        # Calculate score
        score = (passed_cases / total_cases) * assignment.max_score if total_cases > 0 else 0
        
        # Update submission
        submission.score = round(score, 2)
        submission.status = 'completed'
        submission.feedback = '\n'.join(feedback_lines)
        submission.save()
        
        return redirect('submission_result', pk=submission.pk)
    
    return redirect('assignment_detail', pk=assignment_id)


@login_required
def submission_result(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    return render(request, 'submissions/submission_result.html', {
        'submission': submission
    })


@login_required
def submission_history(request):
    submissions = Submission.objects.filter(
        student=request.user
    ).order_by('-submitted_at')
    return render(request, 'submissions/submission_history.html', {
        'submissions': submissions
    })


@login_required
def submit_code(request, assignment_id):
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    
    if timezone.now() > assignment.due_date:
        messages.error(request, 'The deadline for this assignment has passed.')
        return redirect('assignment_detail', pk=assignment_id)
    
    existing_submissions = Submission.objects.filter(
        student=request.user,
        assignment=assignment
    ).count()
    
    if existing_submissions >= 3:
        messages.error(request, 'You have reached the maximum of 3 submissions for this assignment.')
        return redirect('assignment_detail', pk=assignment_id)
    
    if request.method == 'POST':
        code = request.POST.get('code', '')
        
        if not code.strip():
            messages.error(request, 'Please write some code before submitting.')
            return redirect('assignment_detail', pk=assignment_id)
        
        submission = Submission.objects.create(
            student=request.user,
            assignment=assignment,
            code=code,
            status='running'
        )
        
        test_cases = assignment.test_cases.all()
        total_cases = test_cases.count()
        passed_cases = 0
        feedback_lines = []
        
        for i, test_case in enumerate(test_cases, 1):
            result = run_code(code, test_case.input_data)
            actual_output = result['stdout'].strip()
            expected_output = test_case.expected_output.strip()
            
            if actual_output == expected_output:
                passed_cases += 1
                if not test_case.is_hidden:
                    feedback_lines.append(f'Test {i}: ✅ Passed')
            else:
                if not test_case.is_hidden:
                    feedback_lines.append(f'Test {i}: ❌ Failed')
                    feedback_lines.append(f'  Your output: {actual_output}')
                    feedback_lines.append(f'  Expected: {expected_output}')
                else:
                    feedback_lines.append(f'Test {i}: ❌ Failed (hidden test case)')
            
            if result['stderr'] and not test_case.is_hidden:
                feedback_lines.append(f'  Error: {result["stderr"]}')
        
        score = (passed_cases / total_cases) * assignment.max_score if total_cases > 0 else 0
        
        submission.score = round(score, 2)
        submission.status = 'completed'
        submission.feedback = '\n'.join(feedback_lines)
        submission.save()
        
        return redirect('submission_result', pk=submission.pk)
    
    return redirect('assignment_detail', pk=assignment_id)