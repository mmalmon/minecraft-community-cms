from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, validate_slug
from django.db import models
from django.utils import timezone
import re

def validate_host(value):
    if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?", value) or ".." in value:
        raise ValidationError("Podaj nazwę DNS lub IPv4 bez protokołu i bez portu.")

class SiteSettings(models.Model):
    name = models.CharField("nazwa strony", max_length=80, default="Blockhaven")
    tagline = models.CharField("hasło", max_length=160, default="Twoje serwery. Twoja społeczność.")
    introduction = models.TextField("powitanie", default="Wybierz swój świat, poznaj zasady i dołącz do gry.")
    community_url = models.URLField("link społeczności", blank=True)
    class Meta:
        verbose_name = "ustawienia strony"
        verbose_name_plural = "ustawienia strony"
    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class Server(models.Model):
    TYPES = [("VANILLA", "Vanilla"), ("PAPER", "Paper"), ("FORGE", "Forge"), ("FABRIC", "Fabric"), ("OTHER", "Inny")]
    name = models.CharField("nazwa", max_length=100)
    slug = models.SlugField("adres strony", unique=True)
    kind = models.CharField("oprogramowanie", max_length=10, choices=TYPES, default="PAPER")
    address = models.CharField("adres dla graczy", max_length=253, help_text="Np. mc.example.org lub mc.example.org:25566")
    description = models.TextField("opis")
    game_version = models.CharField("wymagana wersja gry", max_length=60, blank=True)
    join_instructions = models.TextField("jak dołączyć / wymagane mody", blank=True)
    rules = models.TextField("regulamin", blank=True)
    modpack_url = models.URLField("link do paczki modów", blank=True)
    status_enabled = models.BooleanField("sprawdzaj status Java", default=False)
    status_host = models.CharField("wewnętrzny host statusu", max_length=253, blank=True, validators=[validate_host], help_text="Nazwa usługi Docker, DNS lub IPv4; widoczny tylko w panelu.")
    status_port = models.PositiveIntegerField("port statusu", default=25565, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    is_published = models.BooleanField("opublikowany", default=False)
    order = models.PositiveIntegerField("kolejność", default=0)
    status_online = models.BooleanField(null=True, default=None)
    status_checked_at = models.DateTimeField(null=True, blank=True)
    players_online = models.PositiveIntegerField(default=0)
    players_max = models.PositiveIntegerField(default=0)
    reported_version = models.CharField(max_length=160, blank=True)
    class Meta:
        ordering = ["order", "name"]
        verbose_name = "serwer"
        verbose_name_plural = "serwery"
    def clean(self):
        if self.status_enabled and not self.status_host:
            raise ValidationError({"status_host": "Podaj host sprawdzania statusu."})
    def __str__(self):
        return self.name
    @property
    def fresh_status(self):
        return self.status_enabled and self.status_checked_at and (timezone.now() - self.status_checked_at).total_seconds() < 120

class Entry(models.Model):
    KINDS = [("news", "Aktualność"), ("tutorial", "Poradnik"), ("page", "Strona / opis dodatku")]
    title = models.CharField("tytuł", max_length=180)
    slug = models.SlugField("adres", unique=True)
    kind = models.CharField("rodzaj", max_length=10, choices=KINDS, default="news")
    server = models.ForeignKey(Server, verbose_name="serwer (opcjonalnie)", null=True, blank=True, on_delete=models.SET_NULL)
    intro = models.CharField("krótki opis", max_length=280)
    body = models.TextField("treść", help_text="Zwykły tekst; akapity rozdziel pustym wierszem.")
    is_published = models.BooleanField("opublikowany", default=False)
    published_at = models.DateTimeField("data publikacji", default=timezone.now)
    class Meta:
        ordering = ["-published_at", "-pk"]
        verbose_name = "materiał"
        verbose_name_plural = "aktualności, poradniki i strony"
    def __str__(self):
        return self.title

class LegacyRoute(models.Model):
    path = models.CharField(max_length=300, unique=True)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
