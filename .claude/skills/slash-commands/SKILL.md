---
name: slash-commands
description: How slash commands work in hefajstos - CommandsService, built-in commands, command results, the command list above the prompt, the panel slot and the /model picker with provider settings. Use when adding or changing a slash command, a picker/panel above the prompt, WidgetPromptInput keys, or model switching (list_models, set_model, ModelSetting).
---

## Flow

```
WidgetPromptInput (text starts with "/") -> CommandSubmitted -> ChatScreen.run_command_worker
repository.run_command(text) -> RunCommandUseCase -> CommandsService.run(text)
    -> command.run(arguments) -> CommandResult       # data: notice / clear feed / open picker
ChatScreen: isinstance on the view model; a picker goes into WidgetPanelSlot and is awaited
```

- A command never enters the prompt queue, so it also works mid-turn.
- A command returns data; only `ChatScreen` decides what to draw.
- `CommandsService.add` refuses a name that is already taken - an extension cannot replace a built-in.
- Sources: `built-in`, `provider` (none yet), `extension` (later, through an ExtensionApi).

## Adding a command

1. a class in `services/commands/` with `name`, `description`, `source` and `async run(arguments) -> CommandResult` (`CommandProtocol`),
2. a provider in the container + an entry in `commands_service`'s `providers.List`,
3. a new kind of result: a dataclass in `services/models/commands.py` + the `CommandResult` union, a view model in `build_command_outcome`, an `isinstance` branch in `ChatScreen.run_command_worker`,
4. a test in `tests/services/commands/`.

SDK errors reach a command only as `AgentSdkError` (the adapter wraps them); the use case turns it into an error notice.

## Panels above the prompt

- `WidgetPanelSlot.show(panel)` mounts one panel at a time and awaits it.
- A `WidgetPanel` ends with `finish(result)` or `cancel()` (= `None`).
- `ChatScreen` locks the prompt while a panel is open and unlocks it after - no try/finally, the worker is only cancelled when the app closes.

## Keys of the command list

- The `Input` keeps the focus while the list is open.
- `Input` binds enter itself, so enter is handled in `Input.Submitted`: an open list runs the highlighted command, even for `/mo`.
- ↑↓, tab and esc are bindings on `WidgetPromptInput`; `check_action` turns them off while the list is closed and Textual passes the key on. No `priority`.
- `ctrl+x` (abort) on `ChatScreen` does need `priority=True`: `Input` takes it as "cut".

## /new

- Opens a fresh SDK session with the current model and settings, then closes the old one - a failed start keeps the old session.
- Refused while `AgentService.is_turn_running`: the running turn streams from the old session, so swapping it under the turn would hang it.
- Resets the token count; `/clear` only clears the feed and keeps the history.

## /model

- Provider knobs are data: `ModelChoice.settings` is a list of `ModelSetting(key, label, choices)`. A new provider brings new data, not a new picker.
- The first choice of every setting is `PROVIDER_DEFAULT` ("default") = send nothing; Copilot reports no default effort.
- Copilot: `reasoning_effort` from `supported_reasoning_efforts`; `context_tier` (`long_context`) when `billing.token_prices.long_context` is set.
- `session.set_model` keeps the history and applies from the next prompt.
- The choice lasts for the session only; settings on disk are a separate, later piece.
