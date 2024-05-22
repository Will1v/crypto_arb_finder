from logger import get_logger

logger = get_logger(__name__)


class Exchange:
    def __init__(self, name: str) -> None:
        self.name = name
        self.ccseq = 0
