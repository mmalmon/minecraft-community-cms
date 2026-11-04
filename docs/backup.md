# Kopia i odtwarzanie

Dane CMS znajdują się w wolumenie `cms-data`: baza SQLite zawiera serwery,
materiały, ustawienia strony oraz konta. Światy Minecraft są w innych,
osobnych wolumenach. Kopia samej strony nie jest kopią światów gry.

## CMS

Zapisz prywatnie również `.env`, użyty Compose i wersję kodu.
Kopia zawiera prywatne dane i hashe haseł; chroń ją i przechowuj poza hostem.

Z katalogu repo zatrzymaj oba procesy, aby nie kopiować aktywnej bazy:

```bash
mkdir -p backups
docker compose stop status-worker web
docker compose run --rm --no-deps --entrypoint python web -c "import shutil; shutil.copy2('/data/portal.sqlite3','/data/portal-backup.sqlite3')"
docker compose cp web:/data/portal-backup.sqlite3 backups/portal.sqlite3
docker compose start web status-worker
```

Polecenie kopiuje bazę z istniejącego wolumenu, bez wykonywania migracji.
Przenieś plik poza serwer. Roboczy plik w wolumenie nie jest niezależną kopią.
Nie dodawaj `backups` ani `.env` do Git.

## Próbne odtworzenie

Przygotuj osobnego hosta testowego, ten sam kod, własne ustawienia domen
i prywatną kopię `.env`. Nie podłączaj go do produkcyjnego DNS.
Najpierw utwórz puste kontenery i wolumen, a potem wgraj bazę:

```bash
docker compose create
docker compose cp backups/portal.sqlite3 web:/data/portal.sqlite3
docker compose run --rm --no-deps --user 0:0 --entrypoint chown web 10001:10001 /data/portal.sqlite3
docker compose up -d
```

Uruchamiaj to wyłącznie na pustym środowisku testowym. Polecenie copy może
nadpisać bazę. Nie stosuj go do działającej strony.
Sprawdź logowanie, listę serwerów, publikacje, szkice i zapis nowego materiału.
Na czas testu wyłącz zewnętrzne pomiary statusu lub odizoluj sieć.

## Minecraft

Zatrzymaj wybrany serwer przed wykonaniem kopii całego jego wolumenu.
Uwzględnij świat, konfigurację, pluginy/mody i ich własne dane.
Zachowaj wersje gry, loadera, dodatków i obrazu. Test odtworzenia wykonuj
osobno od produkcji. `docker compose down -v` usuwa wolumeny i dane.
