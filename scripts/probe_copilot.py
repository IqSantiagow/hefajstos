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
        print("models:")
        for model in models:
            print_model(model)
    except Exception as e:
        print(f"The client started, but the request failed: {type(e).__name__}: {e}")
        return 1
    finally:
        await client.stop()
    return 0


def print_model(model) -> None:
    limits = model.capabilities.limits
    prices = model.billing.token_prices if model.billing else None
    long_context = prices.long_context if prices else None
    print(
        f"  {model.id:<28} effort={model.supported_reasoning_efforts} "
        f"default={model.default_reasoning_effort} "
        f"context={limits.max_context_window_tokens if limits else None} "
        f"long_context={long_context.max_prompt_tokens if long_context else None}"
    )


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
