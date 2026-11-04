import json
import re
from html.parser import HTMLParser
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from portal.models import Entry, Server, SiteSettings, LegacyRoute

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in {"p","h1","h2","h3","section","div","article","br"}:
            self.parts.append("\n\n")
        if tag == "li":
            self.parts.append("\n• ")
    def handle_endtag(self, tag):
        if tag in {"p","h1","h2","h3","section","div","article","code"}:
            self.parts.append("\n")
        elif tag == "span":
            self.parts.append(" ")
    def handle_data(self, data):
        self.parts.append(data)
    def text(self):
        return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", "".join(self.parts)).strip()

def plugin_text(template):
    match = re.search(r'{%\s*block content\s*%}(.*?){%\s*endblock\s*%}', template, re.S)
    parser = TextExtractor()
    parser.feed(re.sub(r"{%.*?%}", "", match.group(1) if match else template, flags=re.S))
    return parser.text()

class Command(BaseCommand):
    help = "Import OloCraft z kopii starej bazy oraz metadanych; nie zmienia źródła."
    def add_arguments(self, parser):
        parser.add_argument("metadata", type=Path)
        parser.add_argument("--community-editors", action="store_true", help="Pozwól grupie Redakcja OloCraft edytować wizytówki serwerów i ustawienia strony.")
    @transaction.atomic
    def handle(self, *args, **options):
        metadata = json.loads(options["metadata"].read_text(encoding="utf-8"))
        if not isinstance(metadata.get("servers"), list) or not metadata.get("dragonlife_html"):
            raise CommandError("Brak konfiguracji serwerów lub opisu DragonLife.")
        SiteSettings.objects.get_or_create(pk=1, defaults={
            "name": "OloCraft", "tagline": "Tu zaczyna się Twoja przygoda.",
            "introduction": "Dwa światy, własne zasady i masa miejsca na pomysły. Wskakuj na serwer albo zostań na chwilę po inspirację.",
        })
        paper = None
        for index, data in enumerate(metadata["servers"]):
            port = int(data["port"])
            address = data["host"]
            # OloCraft korzysta z nazw publicznych z rekordami SRV dla Forge.
            if not data.get("srv", False) and port != 25565:
                address += ":" + str(port)
            defaults = {
                "name": data["name"], "kind": data["edition"].upper(),
                "address": address, "description": data["description"],
                "status_host": metadata["status_host"], "status_port": port,
                "status_enabled": True, "is_published": True, "order": index,
                "game_version": data.get("version", ""),
                "join_instructions": data.get("instructions", "Minecraft Java Edition. Sprawdź zgodną wersję gry i wymagane dodatki przed dołączeniem."),
            }
            server, _ = Server.objects.get_or_create(slug=data["slug"], defaults=defaults)
            if server.kind == "PAPER":
                paper = server
        body = plugin_text(metadata["dragonlife_html"])
        if not body or "/dragonlife" not in body:
            raise CommandError("Opis DragonLife jest pusty lub nie zawiera komend.")
        plugin, _ = Entry.objects.get_or_create(slug="dragonlife", defaults={
            "title": "DragonLife", "kind": "page", "server": paper,
            "intro": "Autorski plugin dla Paper MC1: system serc, smocze przedmioty, cofanie stanu gracza i własna paczka zasobów.",
            "body": body, "is_published": True,
        })
        LegacyRoute.objects.get_or_create(path="dragonlife/", defaults={"entry": plugin})
        imported = {"news": 0, "tutorial": 0}
        tables = connection.introspection.table_names()
        for table, kind, prefix in [("content_post", "news", "blog"), ("content_tutorial", "tutorial", "poradniki")]:
            if table not in tables:
                continue
            with connection.cursor() as cursor:
                cursor.execute("SELECT title,slug,intro,body,is_published,published_at FROM " + table)
                rows = cursor.fetchall()
            for title, slug, intro, text, published, date in rows:
                route = LegacyRoute.objects.filter(path=prefix+"/"+slug+"/").first()
                if route:
                    continue
                candidate = slug
                if Entry.objects.filter(slug=candidate).exists():
                    candidate = kind + "-" + slug
                counter = 2
                base = candidate
                while Entry.objects.filter(slug=candidate).exists():
                    candidate = base+"-"+str(counter)
                    counter += 1
                if isinstance(date, str):
                    date = parse_datetime(date)
                entry = Entry.objects.create(title=title, slug=candidate, intro=intro, body=text, kind=kind, is_published=published, published_at=date)
                LegacyRoute.objects.create(path=prefix+"/"+slug+"/", entry=entry)
                imported[kind] += 1
        # Zachowaj uprawnienia redakcyjne; nie dodawaj administracji użytkownikami.
        for action in ("view", "add", "change", "delete"):
            old = Permission.objects.filter(content_type__app_label="content", codename__in=[action+"_post", action+"_tutorial"])
            new = Permission.objects.get(content_type__app_label="portal", codename=action+"_entry")
            for group in Group.objects.filter(permissions__in=old).distinct():
                group.permissions.add(new)
            for user in get_user_model().objects.filter(user_permissions__in=old).distinct():
                user.user_permissions.add(new)
        if options.get("community_editors"):
            group = Group.objects.filter(name="Redakcja OloCraft").first()
            if group:
                group.permissions.add(*Permission.objects.filter(content_type__app_label="portal", codename__in=["view_server", "add_server", "change_server", "view_sitesettings", "change_sitesettings"]))
        self.stdout.write(json.dumps({"servers": Server.objects.count(), "entries": Entry.objects.count(), "imported": imported, "users": get_user_model().objects.count()}))

