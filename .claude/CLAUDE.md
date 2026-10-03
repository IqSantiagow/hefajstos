# CLAUDE.md

## Commands

```bash
uv sync --extra test --extra dev
uv run hefajstos                      # the app (current directory = agent's directory)
AGENT__ENGINE=stub uv run hefajstos   # same UI, synthetic agent

ruff check
ruff format --diff                    # check only; drop --diff to fix

coverage run -m unittest discover && coverage report -m
uv run python -m unittest tests.adapters.test_copilot_event_mapper

uv run python scripts/probe_copilot.py   # does the SDK start + real model names
uv run python scripts/smoke_stub.py      # one full UI turn, headless, on the stub
```

The project is pinned to a **uv-managed** CPython
(`[tool.uv] python-preference = "only-managed"`). The python.org interpreter on
this machine has no CA certificates, so the SDK cannot download its runtime.

## Architecture

```
Widget/Screen -> Repository -> UseCase -> AgentProtocol <- AgentService
                                          AgentSdkProtocol <- CopilotAgentAdapter
                                                           <- StubAgentAdapter
```

Every arrow points one way. The DI container (`containers/main_container.py`)
is the only place where concrete classes meet. `AGENT__ENGINE` only picks the
adapter; the service is always the same.

One turn, top to bottom (modelled on `LLMService` in EDCeleste):

```
WidgetPromptInput -> ChatScreen: echo to the feed, then repository.send_message
AgentService.add_prompt_to_queue(prompt)
AgentService.consume_prompt_queue():      # the only consumer: ChatScreen's worker
    yield THINKING
    async for event in adapter.send_and_stream(prompt): (auto-approve, token sum) yield event
    yield IDLE
```

- `protocols/` — `typing.Protocol`, one per file, bodies are `...`.
- `adapters/copilot_event_mapper.py` — pure functions, one `if isinstance` after
  another; together with `copilot_agent_adapter.py` the only files importing `copilot`.
- `adapters/stub_agent_adapter.py` — a scripted agent for working on the UI.
- `services/agent_service.py` — prompt queue, auto-approve, token sum.
- `services/models/agent_events.py` — domain dataclasses and `AgentStatus`.
- `use_cases/chat/` — thin callable classes, the only public method is `__call__`.
- `presentation/` — the repository and view models. **Outside `ui/` on purpose**:
  otherwise the container and use cases would import from the UI and the
  dependency direction would flip.
- `ui/` — one global `ui/css.tcss`, no `DEFAULT_CSS`. **Only `ui/` knows CSS
  classes.** A view model gives data (`is_error: bool`) and the widget picks
  the class for it.

There is deliberately **no** `EventBus` (one producer, one consumer), no second
stream for the footer state and no state reducer (the status travels in the
same stream as the answers), no `config.yaml` and no `SettingsService` (there is
no settings screen). Add them only once a second consumer or a settings screen
appears.

## Three places that are easy to break

1. **The event queue in the adapter.** `session.on()` is a sync callback.
   Everything goes through `loop.call_soon_threadsafe(queue.put_nowait, ...)` —
   permission requests too. Mixing that with a plain `put_nowait` scrambles the
   order. `send_and_stream` ends the turn on `session.idle` or `session.error`
   (the SDK's own `send_and_wait` does the same) and clears leftovers of the
   previous turn before sending — otherwise a late idle would end the next one.

2. **Permissions.** The SDK awaits `on_permission_request` and its return value
   *is* the answer — the agent stands still until it returns. `abort()` and
   `stop()` in the adapter answer open permissions **first** and only then touch
   the session. The other way round, the CLI process hangs. `permission.requested`
   from the event stream is **ignored** in the mapper: the same request arrives
   through the callback and would show up in the feed twice. The screen's worker
   waits on the modal, and that is fine — the agent waits for the answer anyway.

3. **Streaming into the feed.** With `streaming=True` there are chunks *and* a
   final `assistant.message` (`AgentText.is_final`), which **replaces** the text.
   The feed looks a message up by id and mounts a new one only when it is not
   there. Widgets keep their text themselves, because the first chunk can arrive
   before `compose()` has built the children. `Static(markup=False)` everywhere —
   an `ls` output or a diff contains `[` and would break the render. `ctrl+x`
   has `priority=True`, because `Input` takes it as "cut".

## Adding a new SDK event type

1. a dataclass in `services/models/agent_events.py` + an entry in the `AgentEvent` union,
2. a branch in `map_session_event`,
3. handling in `build_chat_item` (feed) or in `StreamAgentResponsesUseCase`,
4. a builder in `tests/agent_event_fixtures.py` and a test in `tests/adapters/`.

A new `PermissionRequest` variant is one `if isinstance` in
`describe_permission_request`. An unknown variant does not crash the app — it
gets the title `unknown action` and the type name.

## Tests

Stdlib `unittest` + `coverage`, mirrored tree, `IsolatedAsyncioTestCase`,
hand-written Fakes for protocols (not `Mock`), `make_x(**overrides)` builders.
**Widgets are not tested** — the convention pushes every testable decision into
a view model or a module-level function; the only exception under `ui/` are
the pure module-level functions (`feed_ids.py`, `shorten_home`,
`format_token_count`, `preview_tool_output`, `forge_part`) - they stay next to the widget
that uses them. `ui/` is excluded from coverage; `scripts/smoke_stub.py`
covers it instead.

## Constraints

- No `tkinter` and no direct `rich` imports — ruff enforces it.
- All `__init__.py` files are empty; import by the full module path.
- Everything in English: code, tests and UI text. No translation dictionaries —
  tools are shown under the name the SDK gives (`bash`, `read`, …).
- Names an ape can understand: descriptive, no clever abstractions.
