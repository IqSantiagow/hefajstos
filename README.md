# Hefajstos

A minimal TUI for agentic coding — Textual on top, the official
[GitHub Copilot SDK](https://github.com/github/copilot-sdk) underneath.
One screen, no MCP, no subagents, no modes.

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

## Requirements

- Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/)
- an account with an active GitHub Copilot subscription

You do not set up authentication in the app — the SDK picks up
`COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` or the logged-in user
(`gh auth login`, or a one-time interactive `copilot`).

## Running

```bash
uv sync --extra test --extra dev
uv run hefajstos
```

The app works in the directory you start it from. **The first run downloads
the Copilot runtime (a few dozen MB)** — until then the header shows
`starting` and the prompt is locked.

To check that it can connect at all (uses no quota):

```bash
uv run python scripts/probe_copilot.py
```

It also prints the **real model names** — they change often, and a wrong model
stops the start with a clear message and the list of available ones.

## Configuration

Everything lives in `.env` (copy it from `.env-example`); every value has a
sensible default, so `.env` is optional.

| Variable | Default | Meaning |
|---|---|---|
| `LOGGING__LEVEL` | `INFO` | log level |
| `AGENT__ENGINE` | `copilot` | `stub` runs the whole UI on synthetic data |
| `AGENT__MODEL` | `auto` | `auto` = Copilot picks |
| `AGENT__AUTO_APPROVE` | `false` | approves tools without asking |
| `AGENT__PERMISSION_TIMEOUT_SECONDS` | `600` | how long a permission request waits for an answer |
| `AGENT__WORKING_DIRECTORY` | current directory | the agent's working directory |

The GitHub token does **not** go into the app's `.env` — the SDK reads it itself.

## Approving tools

Before the agent runs a command, writes a file or reaches the network, you get
a modal showing exactly what it wants to do: `y` approves, `n` / `esc` rejects.
A rejection goes back to the agent as feedback, so it can try another way
instead of failing. `^x` aborts the turn; with the modal open, reject first
(`n` / `esc`).

`AGENT__AUTO_APPROVE=true` turns the modal off but does **not** hide anything:
every auto-approval stays in the feed. Requests your organisation marks as
`managed_approval_required` are never approved automatically.

## Working on the UI without Copilot

```bash
AGENT__ENGINE=stub uv run hefajstos
```

A scripted agent (`adapters/stub_agent_adapter.py`) plays a full turn —
streaming, a tool call, the permission modal — with no GitHub, no quota and no
runtime download. It only replaces the Copilot adapter, so it goes through the
same `AgentService` as production. The same run, headless:

```bash
uv run python scripts/smoke_stub.py
```

## Development

```bash
ruff check && ruff format --diff
coverage run -m unittest discover && coverage report -m
uv run python -m unittest tests.adapters.test_copilot_event_mapper   # one module
```

Architecture and conventions: `.claude/CLAUDE.md`.
