from hefajstos.services.models.commands import ClearFeed, CommandResult, CommandSource


class ClearCommand:
    name = "clear"
    description = "Clear the feed - the agent keeps its history"
    source = CommandSource.BUILT_IN

    async def run(self, arguments: str) -> CommandResult:
        return ClearFeed()
