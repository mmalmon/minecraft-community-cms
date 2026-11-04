from .models import SiteSettings, Entry
from django.utils import timezone
def site_settings(request):
    return {"site": SiteSettings.objects.first() or SiteSettings(), "site_pages": Entry.objects.filter(kind="page", is_published=True, published_at__lte=timezone.now())}
