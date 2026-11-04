# Publikacja strony

Domyślny Compose udostępnia HTTP tylko na 127.0.0.1:8090. Dodanie domeny do
ALLOWED_HOSTS nie ustawia DNS, routera ani certyfikatu.

Przed publikacją skonfiguruj własne reverse proxy z HTTPS. Ustaw w `.env`:

```dotenv
DJANGO_ALLOWED_HOSTS=minecraft.example.org
DJANGO_CSRF_TRUSTED_ORIGINS=https://minecraft.example.org
DJANGO_HTTPS=1
DJANGO_TRUST_PROXY=1
```

Ostatnia opcja ufa X-Forwarded-Proto. Włącz ją tylko wtedy, gdy do aplikacji
prowadzi wyłącznie Twoje proxy, które usuwa/nadpisuje nagłówek użytkownika.
Przy proxy w kontenerze dołącz web i proxy do wspólnej sieci i kieruj ruch
na port 8000 aplikacji. Nie wystawiaj dodatkowo portu CMS na wszystkich
interfejsach. Szczegóły zależą od użytego proxy i dotychczasowej infrastruktury.

Wewnętrzny `/health/` nie wymusza przekierowania HTTPS, żeby kontrola
kontenera działała bez certyfikatu. Nie zwraca konfiguracji ani danych.

SQLite to prosty wybór dla małej strony społeczności. CMS ma jednego workera
Gunicorna i osobny proces aktualizacji statusów. Przy wielu redaktorach,
dużym ruchu lub wielu instancjach aplikacji zaplanuj migrację do PostgreSQL,
współdzielony magazyn i osobną strategię zadań w tle.

Hosty sprawdzania statusu zmienia tylko zaufany administrator z uprawnieniami
do serwerów. Mogą kierować do sieci wewnętrznej, dlatego nie nadawaj tego
uprawnienia niezaufanym kontom. Endpoint publiczny nie przyjmuje adresów
do odpytania i nie ujawnia wewnętrznych nazw.

Zadbaj o unikalne hasła kont, aktualizacje zależności, ograniczenie /admin/
przez VPN lub proxy, kopie i ich odtwarzanie. Przy wyłączaniu statusu dla
serwera publiczny wynik natychmiast zmienia się na nieznany.
