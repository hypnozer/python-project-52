from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "index.html"


def trigger_error(request):
    raise RuntimeError("Bugsink production integration test")
