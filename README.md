# Minecraft Community CMS

Uniwersalna strona społeczności Minecraft Java w Django, wyprowadzona z pomysłu
OloCraft. Zamiast edytować kod strony, administrator wpisuje własne serwery,
nazwę społeczności, zasady i materiały w panelu `/admin/`.

To pierwsza wersja projektu. CMS opisuje serwery i pokazuje status;
uruchamianiem oraz aktualizacją kontenerów zarządzasz przez Docker Compose.
CMS nie ma dostępu do Docker API, RCON ani plików światów.

## Co zawiera

- dowolną liczbę wizytówek serwerów Java: Vanilla, Paper, Forge, Fabric i inne;
- osobny adres dla graczy i wewnętrzny adres sprawdzania statusu;
- wymagania wersji, instrukcje dołączenia, regulaminy i link do paczki modów;
- aktualności, poradniki i własne strony, np. opis pluginu;
- szkice oraz daty publikacji; przyszłe materiały nie są jeszcze widoczne;
- nazwę, hasło strony i link społeczności zmieniane w panelu;
- osobny proces sprawdzania statusu z zapisanym wynikiem;
- polski, responsywny interfejs i pustą stronę gotową do własnych treści.

Nie importuje danych ani kont z produkcyjnego OloCraft. Nie obsługuje statusu
Bedrock, sklepów, płatności, rejestracji graczy ani sterowania serwerami gry.

## Szybki start: strona CMS

Wymagania: Linux z Docker Engine, Compose v2 i Git. Zaczynaj na hoście testowym.
Nie trzeba instalować Pythona na hoście, gdy używasz Dockera.

```bash
git clone https://github.com/mmalmon/minecraft-community-cms.git
cd minecraft-community-cms
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

Wklej wygenerowany ciąg do `DJANGO_SECRET_KEY` w lokalnym `.env`.
Nie używaj wartości `replace-...`; aplikacja odmówi startu. Następnie:

```bash
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
docker compose ps
```

Polecenia mogą wymagać `sudo`, zależnie od konfiguracji hosta.
Otwórz `http://localhost:8090/admin/` na hoście. Ze swojego komputera
zestaw tunel `ssh -L 8090:127.0.0.1:8090 UZYTKOWNIK@SERWER` i otwórz
ten sam adres lokalny. Zostaw sesję SSH otwartą.

1. Dodaj „ustawienia strony”: nazwę, hasło, powitanie i opcjonalny link społeczności.
2. Dodaj serwer: nazwę, typ, adres dla graczy, opis i instrukcje.
3. Zaznacz „opublikowany”. Włączanie statusu jest opcjonalne.
4. Dodaj aktualności i poradniki. Zwykły tekst jest wyświetlany z zachowaniem
   akapitów; HTML pozostaje tekstem.
5. Otwórz stronę główną i sprawdź ją jako niezalogowany użytkownik.

Nie twórz wspólnego konta redakcyjnego. W Django można dodawać konta personelu
i nadawać wybrane uprawnienia do serwerów, materiałów i ustawień.

Opcjonalne przykłady do obejrzenia wyglądu: `docker compose exec web python
manage.py seed_demo`. Zmień lub usuń je w panelu; example.org nie jest
adresem działającego serwera gry. Polecenie nie nadpisuje istniejących treści.

## Serwery Minecraft i status

[Przykład Paper i Forge](examples/minecraft/compose.yaml) jest osobnym stosem
Compose. Zobacz [poradnik uruchomienia](docs/minecraft.md).
Gdy oba stosy współdzielą sieć `minecraft-community`, włącz plik dodatkowy:

```bash
docker compose -f compose.yaml -f examples/cms-with-minecraft.yaml up -d --build
```

W panelu CMS wpisz `paper` jako host statusu, a `25565` jako port.
Dla Forge w tej samej sieci wpisz `forge:25565` jako dwa osobne pola.
Adres dla graczy może brzmieć `mc.example.org:25566` i jest niezależny.
Usługi ze swoich istniejących stosów możesz również podłączyć do tej sieci,
dobierając unikalne aliasy; nie trzeba przenosić światów.

Status odświeża `status-worker`. Publiczne żądania nie odpytują sieci.
„Brak aktualnego pomiaru” oznacza brak pomiaru lub wynik starszy niż 120 s.
„Brak odpowiedzi” nie musi oznaczać wyłączenia serwera — sprawdź trasę sieciową,
port i `enable-status=true`. Nie podawaj publicznym użytkownikom hosta statusu.

## Publikacja, kopie i rozwój

- [HTTPS, sieci i ograniczenia](docs/deployment.md)
- [Kopie i odtwarzanie](docs/backup.md)
- [Architektura i rozwój projektu](docs/architecture.md)
- [OloCraft jako inspiracja](https://master-homelab.pl/projekty/olocraft/)
- [Homelab Cloud Starter](https://github.com/mmalmon/homelab-cloud-starter)

Testy sprawdzają logikę Django i parsowanie odpowiedzi statusu.
Przykładowe serwery gier wymagają osobnego testu rozgrywki; nie uruchamiano
ich automatycznie ani nie akceptowano EULA w imieniu użytkownika.

Projekt fanowski; nie jest powiązany z Mojang ani Microsoft. Kod na licencji MIT.
