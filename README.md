# Hefajstos

Minimalne TUI do agentowego kodowania — Textual na wierzchu, oficjalny
[GitHub Copilot SDK](https://github.com/github/copilot-sdk) pod spodem.
Jeden ekran, bez MCP, bez subagentów, bez trybów pracy.

```
┌ HEFAJSTOS  auto  ~/Projects/foo  ↑ 18 764 / ↓ 92           ready ┐
│ YOU                                                              │
│ List the files in this directory.                                │
│ AGENT                                                            │
│ I will start by checking what is in the directory…               │
│ bash  ls -1A .                                                   │
│   alfa.txt                                                       │
│   beta.txt                                                       │
├──────────────────────────────────────────────────────────────────┤
│ › _                                                              │
└──────────────────────────────────────────────────────────────────┘
  ^c Quit   ^x Abort turn
```

## Wymagania

- Python ≥ 3.12 i [uv](https://docs.astral.sh/uv/)
- konto z aktywnym GitHub Copilotem

Autoryzacji nie konfigurujesz w aplikacji — SDK samo bierze
`COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` albo zalogowanego
użytkownika (`gh auth login`, ewentualnie jednorazowo interaktywne `copilot`).

## Uruchomienie

```bash
uv sync --extra test --extra dev
uv run hefajstos
```

Aplikacja pracuje w katalogu, z którego ją odpalisz. **Pierwsze uruchomienie
pobiera runtime Copilota (kilkadziesiąt MB)** — do tego czasu header pokazuje
`starting`, a pole promptu jest zablokowane.

Sprawdzenie, czy w ogóle się połączy (nie zużywa limitu):

```bash
uv run python scripts/probe_copilot.py
```

Wypisze też **realne nazwy modeli** — zmieniają się często, a zły model
zatrzymuje start z czytelnym komunikatem i listą dostępnych.

## Konfiguracja

Wszystko w `.env` (skopiuj z `.env-example`); każda wartość ma sensowny
domyślny, więc `.env` jest opcjonalny.

| Zmienna | Domyślnie | Znaczenie |
|---|---|---|
| `LOGGING__LEVEL` | `INFO` | poziom logów |
| `AGENT__ENGINE` | `copilot` | `stub` uruchamia całe UI na danych syntetycznych |
| `AGENT__MODEL` | `auto` | `auto` = wybiera Copilot |
| `AGENT__AUTO_APPROVE` | `false` | zatwierdza narzędzia bez pytania |
| `AGENT__PERMISSION_TIMEOUT_SECONDS` | `600` | ile żądanie zgody czeka na odpowiedź |
| `AGENT__WORKING_DIRECTORY` | bieżący katalog | katalog pracy agenta |

Token GitHuba **nie** trafia do `.env` aplikacji — czyta go samo SDK.

## Zatwierdzanie narzędzi

Zanim agent uruchomi komendę, zapisze plik albo sięgnie do sieci, dostajesz
modal z konkretną treścią operacji: `y` zgoda, `n` / `esc` odmowa. Odmowa wraca
do agenta jako informacja zwrotna, więc może spróbować inaczej zamiast się
wysypać. `^x` przerywa turę; przy otwartym modalu najpierw odmów (`n` / `esc`).

`AGENT__AUTO_APPROVE=true` wyłącza modal, ale **nie** ukrywa operacji: każde
auto-zatwierdzenie zostaje w feedzie. Żądania oznaczone przez organizację jako
`managed_approval_required` nigdy nie są zatwierdzane automatycznie.

## Praca nad UI bez Copilota

```bash
AGENT__ENGINE=stub uv run hefajstos
```

Skryptowany agent (`adapters/stub_agent_adapter.py`) odgrywa pełną turę —
streaming, wywołanie narzędzia, modal zgody — bez GitHuba, bez limitu i bez
pobierania runtime'u. Podmienia tylko adapter Copilota, więc przechodzi przez
ten sam `AgentService` co produkcja. Ten sam przebieg headless:

```bash
uv run python scripts/smoke_stub.py
```

## Rozwój

```bash
ruff check && ruff format --diff
coverage run -m unittest discover && coverage report -m
uv run python -m unittest tests.adapters.test_copilot_event_mapper   # jeden moduł
```

Architektura i konwencje: `.claude/CLAUDE.md`.
