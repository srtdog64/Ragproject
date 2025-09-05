# core/result.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Union

T = TypeVar("T")
E = TypeVar("E")

@dataclass(frozen=True)
class Result(Generic[T]):
    _value: Union[T, None]
    _error: Union[E, None]

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(_value=value, _error=None)

    @staticmethod
    def err(error: E) -> "Result[T]":
        return Result(_value=None, _error=error)

    def isOk(self) -> bool:
        return self._error is None

    def isErr(self) -> bool:
        return self._error is not None

    def getValue(self) -> T:
        if self._error is not None:
            raise ValueError("Tried to access value of an Err.")
        return self._value  # type: ignore

    def getError(self) -> E:
        if self._error is None:
            raise ValueError("Tried to access error of an Ok.")
        return self._error  # type: ignore

    def map(self, fn: Callable[[T], T]) -> "Result[T]":
        if self.isErr():
            return self
        return Result.ok(fn(self.getValue()))

    def mapError(self, fn: Callable[[E], E]) -> "Result[T]":
        if self.isOk():
            return self
        return Result.err(fn(self.getError()))
