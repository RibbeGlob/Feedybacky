# Feedybacky Export

Eksporter zgłoszeń i komentarzy z [Feedybacky](https://feedybacky.com). Loguje się
w oknie Chromium (ręcznie), przechwytuje sesję i pobiera dane **wyłącznie żądaniami
GET** (nic nie modyfikuje po stronie Feedybacky).

Wynik zapisywany jest lokalnie do plików JSON, z checkpointami i wznawianiem.

---

## 1. Wymagania

- Python 3.11+
- System: Windows (dołączony `URUCHOM_EKSPORT.bat`); działa też na macOS/Linux
  — patrz uwaga o ścieżce interpretera niżej.

---

## 2. Instalacja (po sklonowaniu repo)


```bash
git clone <adres-repo>
cd feedybacky_bot
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
```

> **macOS / Linux:** zamiast `.\.venv\Scripts\python.exe` używaj `.venv/bin/python`.
> Ostatnia komenda (`playwright install chromium`) pobiera przeglądarkę używaną przez
> program — jest wymagana także przy odtwarzaniu środowiska.

---

## 3. Konfiguracja projektu

Symbol projektu Feedybacky i adresy API są w [`feedybacky/config.py`](feedybacky/config.py):

```python
PROJECT_SYMBOL = "MondiPolska-gbKWcpiIsK"
```

Aby eksportować inny projekt, zmień `PROJECT_SYMBOL` na symbol swojego projektu
(widoczny w adresie URL na Feedybacky: `.../project/<PROJECT_SYMBOL>`).

---

## 4. Szybki start

Z katalogu projektu:

```bash
.\.venv\Scripts\python.exe feedybacky_export.py
```

Na Windowsie można też uruchomić dwuklikiem **`URUCHOM_EKSPORT.bat`** (używa `.venv`
i przekazuje argumenty).

Po uruchomieniu:

1. Otworzy się okno Chromium.
2. Zaloguj się do Feedybacky (jeśli pojawi się ekran logowania).
3. Otwórz listę zgłoszeń albo odśwież stronę.
4. Program wykryje zalogowane żądanie API i sam pobierze listę oraz szczegóły.
5. **Nie zamykaj okna Chromium**, dopóki w konsoli nie zobaczysz `Eksport zakończony`.

Przerwanie `Ctrl+C` jest bezpieczne — checkpointy zostają, a kolejne uruchomienie
wznowi od miejsca, w którym skończył.

---

## 5. Uruchamianie parametryczne

Ogólna postać:

```bash
.\.venv\Scripts\python.exe feedybacky_export.py [OPCJE]
```

Przez `.bat` (argumenty przekazują się tak samo):

```bash
URUCHOM_EKSPORT.bat --incremental
```

### Dostępne parametry

| Parametr | Domyślnie | Opis |
|---|---|---|
| `--output-dir <folder>` | `feedybacky_export` | Folder wynikowy. |
| `--start-page <n>` | `1` | Pierwszy numer strony API. |
| `--max-pages <n>` | `500` | Maksymalna liczba stron listy do pobrania. |
| `--delay <sekundy>` | `2.0` | Przerwa między żądaniami GET (minimum wymuszone: `0.2`). |
| `--no-resume` | wyłączone | Nie wznawiaj z checkpointu — pobierz wszystko od nowa. |
| `--incremental` | wyłączone | Doładuj tylko nowe zgłoszenia do istniejącego zbioru. |
| `-h`, `--help` | — | Wyświetl pomoc. |

### Przykłady

Pełny pierwszy eksport (domyślnie):

```bash
.\.venv\Scripts\python.exe feedybacky_export.py
```

Doładowanie tylko nowych zgłoszeń (codzienne/tygodniowe):

```bash
.\.venv\Scripts\python.exe feedybacky_export.py --incremental
```

Szybszy bieg (mniejsza przerwa między żądaniami):

```bash
.\.venv\Scripts\python.exe feedybacky_export.py --delay 0.5
```

Pełne odświeżenie od zera (ostrożnie — pobiera wszystko ponownie):

```bash
.\.venv\Scripts\python.exe feedybacky_export.py --no-resume
```

Zapis do innego folderu (np. próbny bieg bez ruszania głównego zbioru):

```bash
.\.venv\Scripts\python.exe feedybacky_export.py --output-dir feedybacky_probny --max-pages 3
```

Kombinacja — szybkie doładowanie:

```bash
.\.venv\Scripts\python.exe feedybacky_export.py --incremental --delay 1.0
```

---

## 6. Tryby pracy

| Sytuacja | Komenda |
|---|---|
| Pierwszy pełny eksport | `feedybacky_export.py` |
| Bieg przerwał się w połowie → dokończ | `feedybacky_export.py` (wznawia się sam) |
| Doładuj nowe zgłoszenia | `feedybacky_export.py --incremental` |
| Pełne odświeżenie od zera | `feedybacky_export.py --no-resume` |

- **Wznawianie (domyślne)** dokańcza przerwany bieg: pomija już pobrane zgłoszenia
  i kontynuuje zbieranie listy od zapisanej strony.
- **`--incremental`** skanuje listę od początku, dokłada tylko nowe ID i kończy po
  2 kolejnych stronach bez nowych ID (szybkie).
- **`--no-resume`** przebudowuje zbiór od zera (długie; użyj tylko świadomie).

---

## 7. Pliki wynikowe

W folderze wyjściowym (domyślnie `feedybacky_export/`):

| Plik / folder | Zawartość |
|---|---|
| `processed/tickets.json` | Zgłoszenia z komentarzami (wynik końcowy). |
| `processed/comments.json` | Jeden rekord na komentarz (lista spłaszczona). |
| `raw_sanitized/<id>.json` | Surowy (odfiltrowany) rekord każdego zgłoszenia. |
| `tickets_checkpoint2.json` | Checkpoint zgłoszeń (do wznawiania). |
| `comments_checkpoint2.json` | Checkpoint komentarzy. |
| `issue_list_checkpoint2.json` | Checkpoint listy ID. |
| `issue_list_progress2.json` | Marker ostatniej ukończonej strony listy. |
| `errors.json` | Zgłoszenia, których nie udało się pobrać. |

Zapis jest atomowy — przerwanie nie uszkodzi poprzedniej wersji plików.

Foldery wyjściowe oraz profil przeglądarki są w `.gitignore` — nie trafiają do repo.

---

## 8. Uwagi

- **Dane osobowe.** Wyniki zawierają imiona i nazwiska oraz treści zgłoszeń/komentarzy.
  Traktuj folder wynikowy jako dane wrażliwe i nie commituj go.
- **Sesja.** Zalogowana sesja żyje w `.feedybacky_browser_profile/`. Usunięcie tego
  folderu = wylogowanie (przy następnym uruchomieniu logujesz się od nowa).
- **Token.** Nagłówek autoryzacyjny trzymany jest tylko w pamięci — nie trafia do
  plików eksportu.
- **Limit zapytań (HTTP 429).** Program sam czeka i ponawia; zbyt agresywny `--delay`
  i tak wpadnie w limit, więc rozsądny zakres to `0.5`–`2.0` s.
- **Uprawnienia.** Uruchamiaj wyłącznie na koncie i danych, do których masz dostęp.

---

## 9. Struktura kodu

```
feedybacky_export.py     punkt wejścia
feedybacky/
├── config.py            stałe + specyfikacje pól
├── storage.py           I/O JSON i operacje na rekordach
├── paths.py             układ plików wyjściowych
├── api.py               URL-e, nagłówki, GET + retry/backoff
├── session.py           logowanie i weryfikacja sesji
├── transform.py         mapowanie danych API na rekordy
├── scraper.py           pętle pobierania (lista + szczegóły)
└── cli.py               argumenty, run(), main()
```
