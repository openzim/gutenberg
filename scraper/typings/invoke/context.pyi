from typing import Any

class Context:
    def run(self, command: str, *, pty: bool = False, warn: bool = False) -> Any: ...
