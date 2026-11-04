# Migracja istniejącego OloCraft

Importer jest przeznaczony dla wcześniejszej aplikacji Django OloCraft
z modelami `content.Post` i `content.Tutorial` oraz statyczną stroną DragonLife.
Najpierw przygotuj prywatną kopię bazy SQLite i źródeł starej strony.
Nie uruchamiaj migracji bezpośrednio na produkcyjnej bazie starej wersji.

Skopiowaną bazę umieść jako `portal.sqlite3` w nowym katalogu danych.
Dzięki temu zachowane są konta, hashe haseł, grupy i historia uprawnień.
Następnie wykonaj migracje nowej aplikacji. Stare tabele treści pozostają
w kopii bazy; importer ich nie usuwa ani nie zmienia.

## Metadane

Przygotuj prywatny JSON, przekazując jedynie wybrane ustawienia starej strony:

```json
{
  "status_host": "192.0.2.10",
  "servers": [
    {
      "slug": "mc1",
      "name": "MC1 — Paper",
      "edition": "Paper",
      "host": "mc.example.org",
      "port": 25565,
      "description": "Opis serwera",
      "version": "Wersja Twojej gry",
      "srv": false
    }
  ],
  "dragonlife_html": "{% block content %}<h1>DragonLife</h1><p>Pełny opis i komendy /dragonlife.</p>{% endblock %}"
}
```

`192.0.2.10` jest adresem dokumentacyjnym, nie adresem serwera.
`srv: true` zachowuje adres dla graczy bez dopisywania portu, jeśli
istniejący rekord DNS SRV wskazuje prawidłowy port. Pomiar statusu zawsze
używa jawnego hosta i portu. Nie eksportuj SECRET_KEY ani haseł do JSON-a.
Przekaż pełną treść oryginalnego szablonu DragonLife. Importer przeniesie
tekst, komendy i dane liczbowe do edytowalnej strony; wygląd nada nowy CMS.

## Import na kopii

```bash
python manage.py migrate --noinput
python manage.py import_olocraft /prywatna/sciezka/metadata.json
```

Ponowne uruchomienie nie nadpisuje już przeniesionych treści. Wpisy i poradniki
zachowują daty i publikację; kolizje slugów otrzymują osobne adresy.
Stare `/blog/.../`, `/poradniki/.../` oraz `/dragonlife/` przekierowują
do przeniesionych materiałów. Szkice i przyszłe publikacje nadal są ukryte.

Dotychczasowe uprawnienia do wpisów i poradników są mapowane na materiały
nowego CMS-a. Opcjonalne `--community-editors` pozwala grupie „Redakcja
OloCraft” dodawać i zmieniać wizytówki serwerów oraz zmieniać ustawienia strony.
Nie przyznaje zarządzania kontami ani usuwania serwerów.

Przed przełączeniem sprawdź stare linki, pełną treść pluginu, statusy,
logowanie i uprawnienia dotychczasowego konta. Zachowaj oryginalny kontener,
kod i bazę do powrotu. Przy końcowym przełączeniu zatrzymaj zapis w starej
aplikacji, wykonaj świeżą kopię bazy i powtórz migrację na tej kopii.
Zmian opublikowanych już w nowym CMS-ie nie ma w starej bazie.

W instalacji z systemem plików tylko do odczytu ustaw `STATIC_ROOT` na
zapisywalny katalog w wolumenie danych. Obraz nadal działa jako użytkownik
nieuprzywilejowany. Zachowaj dotychczasowe reguły HTTPS i zaufania do proxy.
