from django.core.management.base import BaseCommand
from portal.models import Server, SiteSettings, Entry

class Command(BaseCommand):
    help = "Dodaj opcjonalne przykłady bez nadpisywania istniejących treści."
    def handle(self, *args, **options):
        SiteSettings.objects.get_or_create(pk=1)
        for slug, name, kind, address, description in [
            ("survival", "Survival · nowy początek", "PAPER", "mc.example.org", "Wspólne budowanie, wyprawy i własne zasady. Miejsce na świat Twojej społeczności."),
            ("modowany", "Więcej do odkrycia", "FORGE", "mc.example.org:25566", "Osobny świat z modami. Opisz tutaj paczkę i wymagania dla graczy."),
        ]:
            Server.objects.get_or_create(slug=slug, defaults={"name": name, "kind": kind, "address": address, "description": description, "is_published": True, "join_instructions": "To przykład. Zastąp go adresem swojego serwera i instrukcją instalacji właściwej wersji gry."})
        Entry.objects.get_or_create(slug="witaj-w-nowym-swiecie", defaults={"title": "Zaczynamy nową przygodę", "intro": "Pierwszy wpis Twojej społeczności. Zmień go w panelu i zaproś graczy do swojego świata.", "body": "Przed dołączeniem sprawdź adres, wersję gry oraz zasady wybranego serwera.", "is_published": True})
        self.stdout.write("Dodano brakujące przykłady. Adresy example.org są demonstracyjne; pomiar statusu jest wyłączony.")
