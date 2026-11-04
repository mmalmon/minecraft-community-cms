# Architektura i zakres pierwszej wersji

Projekt inspirowany jest Django obsługującym OloCraft. Zachowuje pomysł
panelu redakcyjnego i odczytu statusu Java, ale zastępuje stałą listę
serwerów oraz markę modelami `Server` i `SiteSettings`.
`Entry` obsługuje aktualności, poradniki i ogólne strony — opis pluginu
może być zwykłą stroną powiązaną z serwerem.

Publiczny frontend renderuje dane w Django i czyta ostatni status z bazy.
Proces `status-worker` odpytuje opublikowane serwery z włączonym statusem.
Odpowiedzi są ograniczone do 64 KiB, czas odczytu jest ograniczony, a
nieudany pomiar nie blokuje strony. DNS zależy od resolvera hosta.
Nie zbieramy nazw graczy ani ich identyfikatorów.

CMS nie uruchamia poleceń serwera gry. Podział:
- Docker Compose: kontenery, sieci i trwałe dane;
- Django admin: opisy, adresy, wymagania, publikacje i wygląd tekstowy;
- proces statusu: odczyt protokołu Java, bez konsoli, RCON i Docker socketu.

Opcjonalny [importer OloCraft](olocraft-migration.md) przenosi dane starszej
aplikacji na kopii bazy i zachowuje stare adresy. Projekt nie zawiera
rejestracji graczy, wizualnego edytora motywu ani mechanizmu dodatków. Osobne typy wpisów i pola można
rozwijać po sprawdzeniu potrzeb użytkowników.

## Testy lokalne

Python 3.12 i wirtualne środowisko:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SECRET_KEY=$(openssl rand -hex 32)
python manage.py collectstatic --noinput
python manage.py test
python manage.py makemigrations --check --dry-run
```

Nie używaj serwera deweloperskiego Django do publicznego hostingu.
Testy sprawdzają m.in. publikacje przyszłe i szkice, dostęp do panelu,
ukryte serwery, escaping tekstu i granice parsera pakietów statusu.
