# Paper i Forge w Dockerze

Paper rozszerza podstawowy serwer Java o pluginy. Forge obsługuje mody;
klient musi mieć zgodną wersję Minecrafta, Forge i wymagane mody.
Plugin Paper nie staje się modem Forge po skopiowaniu pliku.

Przykład jest inspirowany dwoma oddzielnymi kontenerami autora OloCraft:
Paper na porcie hosta 25565 oraz Forge na 25566. Nie zawiera produkcyjnych
światów, DragonLife, list graczy ani prywatnej konfiguracji.
Parametry wersji są przykładowe i trzeba dobrać je do własnej paczki.

## Uruchom pierwszy serwer

Z katalogu repozytorium:

```bash
cd examples/minecraft
cp .env.example .env
chmod 600 .env
```

Przeczytaj [Minecraft EULA](https://www.minecraft.net/en-us/eula).
Jeśli ją akceptujesz, ustaw lokalnie `MC_EULA=TRUE`.
Wpisz swój prawdziwy nick do `MC_WHITELIST`. Nie wyłączaj uwierzytelniania
`ONLINE_MODE`. Dobierz `MC_VERSION` i `JAVA_TAG`; przykład używa
Minecraft 1.21.1 i Java 21, a nie aktualnych wersji serwera autora.

```bash
docker compose up -d paper
docker compose logs --tail=100 paper
```

Poczekaj na zakończenie pobierania i uruchamiania. Port domyślnie jest
związany z `127.0.0.1`. Aby połączyć się z innego urządzenia w domu,
wpisz w `MC_BIND_ADDRESS` adres LAN serwera i ponów uruchomienie.
W Minecraft Java dodaj serwer pod `ADRES_LAN:25565`.

Forge jest opcjonalny:

```bash
docker compose --profile forge up -d forge
docker compose logs --tail=100 forge
```

Adres dla gracza to `ADRES_LAN:25566`, chociaż wewnątrz kontenera Forge
nasłuchuje na 25565. Dla wybranej wersji Minecrafta obraz dobiera zalecaną
wersję Forge. Przed użytkowaniem z modpackiem przypnij też konkretny
`FORGE_VERSION` w jego sekcji środowiska zgodnie z wymaganiami paczki.
Wolumeny `paper-data` i `forge-data` są oddzielne.
Pluginy Paper umieszczaj w katalogu `plugins` jego wolumenu;
mody Forge w `mods` jego wolumenu, zgodnie z dokumentacją obrazu.
Zatrzymaj usługę przed zmianą plików i wykonaj kopię.

## Powiąż CMS

Wróć do katalogu głównego repo. Sieć `minecraft-community` została już
utworzona przez stos Minecrafta.

```bash
cd ../..
docker compose -f compose.yaml -f examples/cms-with-minecraft.yaml up -d --build
```

W panelu dodaj Paper: host statusu `paper`, port `25565`.
Dodaj Forge: host `forge`, port `25565`. Zaznacz sprawdzanie statusu.
Przy uruchomionym profilu Forge adres `forge` rozwiąże się w sieci Dockera.
Jeśli Forge pozostaje wyłączony, CMS pokaże brak odpowiedzi.

Nie udostępniaj baz, paneli ani RCON. Publiczna gra potrzebuje świadomie
przekierowanych portów TCP 25565/25566 i reguł zapory; publiczna strona WWW
potrzebuje osobno HTTPS. Zwykłe HTTP proxy nie obsługuje protokołu Minecraft.
DNS SRV może uprościć adres dla gracza, ale CMS status odpytuje pod jawnym
hostem i portem — nie wyszukuje rekordów SRV.

## Oficjalne źródła

- [Obraz serwera Minecraft i konfiguracja](https://docker-minecraft-server.readthedocs.io/en/latest/)
- [Paper](https://docker-minecraft-server.readthedocs.io/en/latest/types-and-platforms/server-types/paper/)
- [Forge](https://docker-minecraft-server.readthedocs.io/en/latest/types-and-platforms/server-types/forge/)
- [Wersje Java](https://docker-minecraft-server.readthedocs.io/en/latest/versions/java/)
