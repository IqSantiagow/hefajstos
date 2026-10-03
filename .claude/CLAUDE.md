# CLAUDE.md

## Commands

```bash
uv sync --extra test --extra dev
uv run hefajstos                      # the app (current directory = agent's directory)
AGENT__ENGINE=stub uv run hefajstos   # same UI, synthetic agent

ruff check
ruff format --diff                    # check only; drop --diff to fix

coverage run -m unittest discover && coverage report -m
uv run python scripts/probe_copilot.py   # does the SDK start + real models and their settings
uv run python scripts/smoke_stub.py      # the real UI, headless, on the stub
```

The project is pinned to a **uv-managed** CPython (`python-preference = "only-managed"`):
the python.org interpreter here has no CA certificates, so the SDK cannot download its runtime.

## Architecture

```
Widget/Screen -> Repository -> UseCase -> AgentProtocol <- AgentService
                                          AgentSdkProtocol <- CopilotAgentAdapter
                                                           <- StubAgentAdapter
                               UseCase -> CommandsProtocol <- CommandsService
                                          CommandProtocol <- ModelCommand, ClearCommand
```

Every arrow points one way. `containers/main_container.py` is the only place where
concrete classes meet. `AGENT__ENGINE` only picks the adapter.

- `protocols/` - one `typing.Protocol` per file.
- `adapters/` - the only code importing `copilot`; SDK exceptions are wrapped in `AgentSdkError`.
- `services/` - agent service, commands, domain dataclasses in `services/models/`.
- `use_cases/` - callable classes; they turn domain results into view models.
- `presentation/` - repository and view models, outside `ui/` so nothing imports the UI.
- `ui/` - one global `ui/css.tcss`, no `DEFAULT_CSS`; only `ui/` knows CSS classes.

Details live in skills: `sdk-events`, `permissions`, `slash-commands`, `test-conventions`.

## Constraints

- No `tkinter` and no direct `rich` imports - ruff enforces it.
- All `__init__.py` files are empty; import by the full module path.
- Everything in English: code, tests and UI text.
- Names an ape can understand: descriptive, no clever abstractions.
- No comments or docstrings unless something is truly non-obvious.
