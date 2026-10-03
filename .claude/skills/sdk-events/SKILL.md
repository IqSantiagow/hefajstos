---
name: sdk-events
description: How agent events flow from the Copilot SDK to the chat feed in hefajstos - the adapter's event queue, ending a turn, streaming text into the feed, and adding a new SDK event type. Use when touching copilot_agent_adapter.py, copilot_event_mapper.py, agent_events.py, AgentService.consume_prompt_queue, StreamAgentResponsesUseCase or WidgetChatFeed.
---

## One turn

```
WidgetPromptInput -> ChatScreen: echo to the feed, then repository.send_message
AgentService.add_prompt_to_queue(prompt)
AgentService.consume_prompt_queue():      # the only consumer: ChatScreen's worker
    yield THINKING
    async for event in adapter.send_and_stream(prompt): (auto-approve, token sum) yield event
    yield IDLE
```

There is no EventBus and no second stream: the status travels in the same stream as the answers.

## The event queue in the adapter

- `session.on()` is a sync callback. Everything goes through `loop.call_soon_threadsafe(queue.put_nowait, ...)`, permission requests too. Mixing it with a plain `put_nowait` scrambles the order.
- `send_and_stream` ends the turn on `session.idle` or `session.error` (the SDK's `send_and_wait` does the same).
- It clears leftovers of the previous turn before sending, otherwise a late idle ends the next turn.

## Streaming into the feed

- With `streaming=True` there are chunks and then a final `assistant.message` (`AgentText.is_final`) that **replaces** the text.
- The feed looks a message up by id and mounts a new one only when it is missing.
- Widgets keep their text themselves: the first chunk can arrive before `compose()` built the children.
- `Static(markup=False)` everywhere - an `ls` output or a diff contains `[`.

## Adding a new SDK event type

1. a dataclass in `services/models/agent_events.py` + an entry in the `AgentEvent` union,
2. a branch in `map_session_event`,
3. handling in `build_chat_item` (feed) or in `StreamAgentResponsesUseCase`,
4. a builder in `tests/agent_event_fixtures.py` and a test in `tests/adapters/`.
