---
name: permissions
description: How tool permission requests work in hefajstos - the SDK callback, the modal, auto-approve, free reads inside the project, and the order of abort/stop. Use when touching on_permission_request, map_permission_request, describe_permission_request, describe_read_access, AgentService auto-approve, is_inside, ModalPermissionScreen, or when a permission prompt behaves unexpectedly.
---

## Flow

- The SDK awaits `on_permission_request`; its return value **is** the answer and the agent stands still until it returns.
- The adapter puts a `PermissionRequested` on the event queue and waits on a future; `answer_permission` resolves it. No answer within `permission_timeout_seconds` = `USER_NOT_AVAILABLE`.
- `permission.requested` from the event stream is **ignored** in the mapper: the same request comes through the callback and would show up twice.
- The screen's stream worker waits on the modal - fine, the agent waits anyway.

## Who answers

`AgentService.__auto_approve_if_allowed`, in this order:

1. `requires_manual_approval` (SDK `managed_approval_required`, set by organization policy) -> always the modal.
2. A read inside the project -> approved, shown in the feed as "Auto-approved: ...".
3. `agent.auto_approve` on -> approved.
4. Otherwise the modal.

## Reads inside the project

- `describe_read_access` uses the CLI's own judgement: `PermissionRequestRead` is a read; a shell line is a read when every `commands[].read_only` is true and `has_write_file_redirection` is false.
- Paths: `resolved_paths[p]` or `p` for every `possible_paths`, plus `resolved_working_directory` (so `cd /etc && ls` is outside).
- `is_inside`: a relative path counts from the working directory, `~` is expanded, symlinks are followed.
- A read-only command without paths (`git status`) passes.

## abort() and stop()

Answer open permissions **first**, then touch the session. The other way round the CLI process hangs.

## A new PermissionRequest variant

One `if isinstance` in `describe_permission_request` (title, summary, detail). An unknown variant gets `unknown action` and its type name instead of crashing.
