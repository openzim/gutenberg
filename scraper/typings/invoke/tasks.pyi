from collections.abc import Callable
from typing import TypeVar

TaskFunction = TypeVar("TaskFunction", bound=Callable[..., object])

def task(*args: object, **kwargs: object) -> Callable[[TaskFunction], TaskFunction]: ...
