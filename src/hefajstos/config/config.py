from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Logging(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class Agent(BaseModel):
    engine: Literal["copilot", "stub"] = Field(
        "copilot",
        description="'stub' runs the whole UI on synthetic data, without GitHub.",
    )
    model: str = Field(
        "auto",
        description="Model for the session. 'auto' lets Copilot pick one.",
    )
    auto_approve: bool = Field(
        False,
        description="Approve every tool the agent asks for, without a modal.",
    )
    permission_timeout_seconds: int = Field(
        600,
        ge=1,
        description="How long a permission request waits for an answer.",
    )
    working_directory: str = Field(
        "",
        # validate_default, or the validator below never runs for the empty default
        # and everything downstream gets "" instead of a real path.
        validate_default=True,
        description="Directory the agent works in. Empty means the current one.",
    )

    @field_validator("working_directory", mode="before")
    @classmethod
    def default_to_the_current_directory(cls, value: Any) -> Any:
        if not value:
            return str(Path.cwd())
        return str(Path(str(value)).expanduser().resolve())


class AppConfig(BaseSettings):
    logging: Logging = Logging()
    agent: Agent = Agent()

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")
