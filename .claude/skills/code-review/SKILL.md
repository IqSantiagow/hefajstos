---
name: code-review-skill
description: Reviews changes in hefajstos against its own conventions - runs the checks, then looks at dependency direction, layering, error handling, async pitfalls and tests. Use when the user asks to review the current diff, a branch or specific files in this repo.
---

Review the changes (`git diff` plus untracked files, unless the user names a target). Report only what is real; if the code is good, say so plainly.

## 1. Does it run?

```bash
uv run ruff check
uv run ruff format --diff
uv run coverage run -m unittest discover && uv run coverage report -m
PYTHONIOENCODING=utf-8 uv run python scripts/smoke_stub.py
```

- Report failures with their output. `TestShortenHome.test_replaces_the_home_directory_with_a_tilde` fails on Windows already - not a finding.
- Changed UI is covered only by the smoke run. If the change adds UI behavior the smoke does not walk through, say so.

## 2. Architecture

- Arrows point one way: `Widget/Screen -> Repository -> UseCase -> Protocol <- Service/Adapter`. Nothing outside `ui/` imports from `ui/`.
- Concrete classes meet only in `containers/main_container.py`. A new dependency is a constructor argument typed with a protocol.
- One class per file, one `Protocol` per file in `protocols/`. No loose factory functions standing in for classes.
- Concrete project types in signatures (`Settings`, `ModelSelection`), not generic `BaseModel` or `dict`.
- Only `adapters/` imports `copilot`. SDK and library exceptions are caught there and wrapped in one project exception (`AgentSdkError`); use cases never see library exception types.
- Use cases are callable classes that return view models; widgets get data, never decide domain things.
- Nothing speculative: no layer, flag or abstraction without a current user.

## 3. Conventions

- No comments or docstrings unless something is truly non-obvious; `# type: ignore[...]` is fine.
- Descriptive names an ape can understand. Everything in English, including UI text.
- CSS only in `ui/css.tcss`, no `DEFAULT_CSS`; only `ui/` knows CSS class names. `Static(markup=False)` for any text that can contain `[`.
- No `rich` or `tkinter` imports; empty `__init__.py` files; full module paths in imports.
- Tests: `unittest`, mirrored tree, hand-written Fakes (not `Mock`), `make_x(**overrides)` builders. Widgets are not tested; pure functions under `ui/` are. New behavior without a test is a finding.

## 4. Bugs

Look hardest at:

- Events from the SDK callback that skip `loop.call_soon_threadsafe` (order gets scrambled), and a turn that can end on a stale `session.idle`.
- `abort()` / `stop()` that touch the session before answering open permissions (the CLI hangs).
- Permissions: anything that can approve a write, or a read outside the working directory, without the user; `managed_approval_required` must always reach the modal.
- Textual workers: code after an `await` that queries widgets which may be gone when the app closes; keys swallowed by `Input` (needs `priority=True` or a `check_action` binding).
- Futures that can be resolved twice, and edge cases like empty lists from the provider.

The topic skills `sdk-events`, `permissions`, `slash-commands` and `test-conventions` describe these areas in detail.

## 5. Report

- Findings ordered by severity, each with `file:line`, what goes wrong and when, and a concrete fix.
- Then smaller remarks, if any.
- If nothing is wrong, say the change is clean in one sentence. Don't invent findings.
