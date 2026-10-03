---
name: test-conventions
description: How tests are written in hefajstos - unittest layout, Fakes, builders, what is and is not tested, and the headless smoke run. Use when writing, fixing or reviewing tests in tests/ or scripts/smoke_stub.py.
---

- Stdlib `unittest` + `coverage`; the tree mirrors `src/hefajstos`; async code uses `IsolatedAsyncioTestCase`.
- Hand-written Fakes for protocols, not `Mock`. `make_x(**overrides)` builders; SDK objects come from `tests/agent_event_fixtures.py`.
- **Widgets are not tested.** Testable decisions go into a view model or a pure module-level function. Pure functions under `ui/` are tested and stay next to their widget (`feed_ids.py`, `shorten_home`, `format_token_count`, `preview_tool_output`, `forge_part`, `is_command_prefix`, `describe_command`, `describe_model_row`, `describe_settings`).
- `ui/` is excluded from coverage; `scripts/smoke_stub.py` drives the real UI on the stub instead. On Windows run it with `PYTHONIOENCODING=utf-8`.
- Known failure on Windows: `TestShortenHome.test_replaces_the_home_directory_with_a_tilde` (path separator).
