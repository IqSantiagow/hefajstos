"""Checks that the Copilot SDK can actually start here.

Starts the client, reports the auth status and the available models, then stops.
It does not run an agent turn, so it costs no quota. The first run downloads the
Copilot runtime, which takes a while.

    uv run python scripts/probe_copilot.py
"""

import asyncio
import sys

from copilot import CopilotClient

START_TIMEOUT_SECONDS = 300


async def main() -> int:
    client = CopilotClient(working_directory=".")
    try:
        await asyncio.wait_for(client.start(), timeout=START_TIMEOUT_SECONDS)
    except Exception as e:
        print(f"Could not start the client: {type(e).__name__}: {e}")
        return 1

    try:
        status = await client.get_auth_status()
        print("auth:", status)
        models = await client.list_models()
        print("models:", [getattr(m, "id", getattr(m, "name", m)) for m in models])
    except Exception as e:
        print(f"The client started, but the request failed: {type(e).__name__}: {e}")
        return 1
    finally:
        await client.stop()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
