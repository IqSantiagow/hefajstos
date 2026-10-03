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
                               UseCase -> CommandsProtocol <- CommandsService
                                          CommandProtocol <- ModelCommand, ClearCommand
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

One slash command — it never enters the prompt queue, so it also works mid-turn:

```
WidgetPromptInput (text starts with "/") -> CommandSubmitted -> ChatScreen.run_command_worker
repository.run_command(text) -> RunCommandUseCase -> CommandsService.run(text)
    -> command.run(arguments) -> CommandResult       # data: notice / clear feed / open picker
ChatScreen: isinstance on the view model; a picker goes into WidgetPanelSlot and is awaited
```

- `protocols/` — `typing.Protocol`, one per file, bodies are `...`.
- `adapters/copilot_event_mapper.py` — pure functions, one `if isinstance` after
  another; together with `copilot_agent_adapter.py` the only files importing `copilot`.
- `adapters/stub_agent_adapter.py` — a scripted agent for working on the UI.
- `services/agent_service.py` — prompt queue, auto-approve, token sum.
- `services/models/agent_events.py` — domain dataclasses and `AgentStatus`.
- `services/commands_service.py` — every slash command in one place; a later
  command never takes an existing name (extensions cannot replace built-ins).
- `services/commands/` — one class per built-in command, built in the container.
- `services/models/model_choice.py` — what `/model` offers, as data. A provider's
  knobs (Copilot: reasoning effort, long context) are `ModelSetting`s, so a new
  provider brings new data, not a new picker. The first choice is always
  `PROVIDER_DEFAULT` — "send nothing".
- `services/models/agent_sdk_error.py` — the only error `list_models`/`set_model`
  raise. Adapters wrap SDK exceptions in it; nothing above sees SDK types.
- `use_cases/chat/`, `use_cases/commands/` — thin callable classes, the only
  public method is `__call__`. They turn domain results into view models.
- `presentation/` — the repository and view models. **Outside `ui/` on purpose**:
  otherwise the container and use cases would import from the UI and the
  dependency direction would flip.
- `ui/` — one global `ui/css.tcss`, no `DEFAULT_CSS`. **Only `ui/` knows CSS
  classes.** A view model gives data (`is_error: bool`) and the widget picks
  the class for it.
- `ui/widgets/widget_panel_slot.py` + `widget_panel.py` — the place above the
  prompt where pickers show up, one at a time. A panel ends with `finish(result)`
  or `cancel()` (= `None`); the caller awaits `slot.show(panel)`. Extensions
  will subclass `WidgetPanel` too.

There is deliberately **no** `EventBus` (one producer, one consumer), no second
stream for the footer state and no state reducer (the status travels in the
same stream as the answers), no `config.yaml` and no `SettingsService` (there is
no settings screen). Add them only once a second consumer or a settings screen
appears.

## Places that are easy to break

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

4. **Keys of the command list.** The `Input` keeps the focus while the list is
   open. `Input` binds `enter` itself, so enter is handled in `Input.Submitted`
   (an open list runs the highlighted command, even for `/mo`). ↑↓, tab and esc
   are bindings on `WidgetPromptInput`; `check_action` turns them off while the
   list is closed, and Textual then passes the key on — tab moves the focus
   again. No `priority` needed.

## Adding a new SDK event type

1. a dataclass in `services/models/agent_events.py` + an entry in the `AgentEvent` union,
2. a branch in `map_session_event`,
3. handling in `build_chat_item` (feed) or in `StreamAgentResponsesUseCase`,
4. a builder in `tests/agent_event_fixtures.py` and a test in `tests/adapters/`.

A new `PermissionRequest` variant is one `if isinstance` in
`describe_permission_request`. An unknown variant does not crash the app — it
gets the title `unknown action` and the type name.

## Adding a slash command

1. a class in `services/commands/` with `name`, `description`, `source` and
   `async run(arguments) -> CommandResult` (it implements `CommandProtocol`),
2. a provider in the container and an entry in `commands_service`'s `providers.List`,
3. a new kind of result: a dataclass in `services/models/commands.py` + the
   `CommandResult` union, a view model in `build_command_outcome`, and an
   `isinstance` branch in `ChatScreen.run_command_worker`,
4. a test in `tests/services/commands/`.

Errors from the SDK reach a command only as `AgentSdkError`; the use case turns
it into an error notice in the feed.

## Tests

Stdlib `unittest` + `coverage`, mirrored tree, `IsolatedAsyncioTestCase`,
hand-written Fakes for protocols (not `Mock`), `make_x(**overrides)` builders.
**Widgets are not tested** — the convention pushes every testable decision into
a view model or a module-level function; the only exception under `ui/` are
the pure module-level functions (`feed_ids.py`, `shorten_home`,
`format_token_count`, `preview_tool_output`, `forge_part`, `is_command_prefix`,
`describe_command`, `describe_model_row`, `describe_settings`) - they stay next
to the widget that uses them. `ui/` is excluded from coverage; `scripts/smoke_stub.py`
covers it instead.

## Constraints

- No `tkinter` and no direct `rich` imports — ruff enforces it.
- All `__init__.py` files are empty; import by the full module path.
- Everything in English: code, tests and UI text. No translation dictionaries —
  tools are shown under the name the SDK gives (`bash`, `read`, …).
- Names an ape can understand: descriptive, no clever abstractions.
