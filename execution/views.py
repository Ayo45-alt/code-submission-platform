from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .runner import run_code
import json

@login_required
def run_code_view(request):
    if request.method == 'POST':
        # Accept JSON or form POST data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                code = data.get('code', '')
                input_data = data.get('input_data', '')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
        else:
            code = request.POST.get('code', '')
            input_data = request.POST.get('input_data', '')

        if not code.strip():
            return JsonResponse({'error': 'Code cannot be empty'}, status=400)

        result = run_code(code, input_data)
        return JsonResponse(result)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
