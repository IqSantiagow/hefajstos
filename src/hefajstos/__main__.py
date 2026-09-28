import logging

from textual.logging import TextualHandler

from hefajstos.containers.main_container import Container
from hefajstos.ui.app import HefajstosApp

logger = logging.getLogger(__name__)


def main() -> None:
    container = Container()
    container.wire(modules=["hefajstos.ui.app"])

    log_level = container.config.logging.level()
    logging.basicConfig(level=getattr(logging, log_level), handlers=[TextualHandler()])

    try:
        HefajstosApp().run()
    except Exception as e:
        logger.error("Raised an exception: %s", e)


if __name__ == "__main__":
    main()
