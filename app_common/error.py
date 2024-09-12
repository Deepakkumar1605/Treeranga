from django.shortcuts import render


def render_error_page(request, error_message, status_code=500):
    context = {
        'error_message': error_message
    }
    return render(request, 'app_common/error_message/error.html', context, status=status_code)