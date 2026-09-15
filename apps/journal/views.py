from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .services import archive_response

@require_GET
def archive_api(request):
    result, form = archive_response(request)
    response = JsonResponse(result.model_dump(mode="json"), status=200 if form.is_valid() else 400)
    response["Cache-Control"] = "private, no-store, max-age=0"
    return response
