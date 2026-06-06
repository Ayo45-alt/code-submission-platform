import subprocess

def run_code(code, input_data, timeout=15):
    try:
        full_input = input_data + '\n' if input_data else '\n'
        
        result = subprocess.run(
            ['docker', 'run', '--rm', '-i',
             '--network', 'none',
             '--memory', '128m',
             '--cpus', '0.5',
             'python:3.12-slim',
             'python', '-c', code],
            input=full_input,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'success': result.returncode == 0
        }

    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': 'Time limit exceeded',
            'success': False
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': str(e),
            'success': False
        }