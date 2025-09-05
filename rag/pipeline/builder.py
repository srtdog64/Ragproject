# pipeline/builder.py
from __future__ import annotations
from typing import List
from core.result import Result
from core.types import RagContext, Answer
from core.interfaces import Step

class Pipeline:
    def __init__(self, steps: List[Step]):
        self._steps = list(steps)

    async def run(self, ctx: RagContext) -> Result[Answer]:
        cur = ctx
        for s in self._steps:
            res = await s.run(cur)
            if res.isErr():
                return Result.err(res.getError())
            cur = res.getValue()
        return Result.ok(cur.parsed)

class PipelineBuilder:
    def __init__(self):
        self._steps: List[Step] = []

    def add(self, step: Step) -> "PipelineBuilder":
        self._steps.append(step)
        return self

    def build(self) -> Pipeline:
        return Pipeline(self._steps)
