from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import Entry, Server

def published():
    return Entry.objects.filter(is_published=True, published_at__lte=timezone.now())

def home(request):
    return render(request, "home.html", {"servers": Server.objects.filter(is_published=True), "entries": published()[:3]})

def server_detail(request, slug):
    server = get_object_or_404(Server, slug=slug, is_published=True)
    return render(request, "server.html", {"server": server, "entries": published().filter(server=server)})

def news(request):
    return render(request, "entries.html", {"title": "Aktualności", "entries": published().filter(kind="news")})

def tutorials(request):
    return render(request, "entries.html", {"title": "Poradniki", "entries": published().filter(kind="tutorial")})

def entry_detail(request, slug):
    return render(request, "entry.html", {"entry": get_object_or_404(published(), slug=slug)})

def status_json(request):
    servers = []
    for s in Server.objects.filter(is_published=True):
        servers.append({"slug": s.slug, "online": s.status_online if s.fresh_status else None, "checked_at": s.status_checked_at, "players_online": s.players_online if s.fresh_status and s.status_online else None, "players_max": s.players_max if s.fresh_status and s.status_online else None})
    return JsonResponse({"servers": servers})

def health(request):
    return HttpResponse("ok\n", content_type="text/plain")
