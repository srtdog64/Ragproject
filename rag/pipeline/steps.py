# pipeline/steps.py
from __future__ import annotations
from typing import List
from core.result import Result
from core.types import RagContext, Retrieved, Answer
from core.interfaces import Step, Retriever, Reranker, OutputParser, LlmClient
from core.policy import Policy

class QueryExpansionStep:
    def __init__(self, expansions: int = 0):
        self._exp = max(0, expansions)

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        if self._exp <= 0:
            return Result.ok(ctx.withExpanded([ctx.question]))
        qs: List[str] = [ctx.question]
        for i in range(self._exp):
            qs.append(f"{ctx.question} (alt {i+1})")
        return Result.ok(ctx.withExpanded(qs))

class RetrieveStep:
    def __init__(self, retriever: Retriever, policy: Policy):
        self._retriever = retriever
        self._policy = policy

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        allRetrieved: List[Retrieved] = []
        for q in ctx.expandedQueries:
            items = await self._retriever.retrieve(q, ctx.k or self._policy.getDefaultTopK())
            allRetrieved.extend(items)
        
        # Check if no results were retrieved
        if not allRetrieved:
            # Return empty retrieved list - pipeline will handle it
            return Result.ok(ctx.withRetrieved([]))
        
        # Simple deduplication based on Chunk.id
        seen = set()
        uniq: List[Retrieved] = []
        for r in sorted(allRetrieved, key=lambda x: x.score, reverse=True):
            if r.chunk.id in seen:
                continue
            seen.add(r.chunk.id)
            uniq.append(r)
        return Result.ok(ctx.withRetrieved(uniq))

class RerankStep:
    def __init__(self, reranker: Reranker, topK: int):
        self._reranker = reranker
        self._topK = max(1, topK)

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        if not ctx.retrieved:
            # No items to rerank
            return Result.ok(ctx.withReranked([]))
        ranked = self._reranker.rerank(ctx.retrieved)
        return Result.ok(ctx.withReranked(ranked[: self._topK]))

class ContextCompressionStep:
    def __init__(self, policy: Policy):
        self._policy = policy

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        buf = []
        remain = self._policy.getMaxContextChars()
        for r in ctx.reranked:
            t = r.chunk.text
            if len(t) <= remain:
                buf.append(t)
                remain -= len(t)
            else:
                if remain > 0:
                    buf.append(t[:remain])
                    remain = 0
                break
        return Result.ok(ctx.withCompressed("\n\n".join(buf)))

class BuildPromptStep:
    def __init__(self, systemHint: str = "You are a helpful RAG assistant."):
        self._sys = systemHint

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        # If no context is retrieved, provide a clear message
        if not ctx.compressedCtx or ctx.compressedCtx.strip() == "":
            prompt = f"""질문에 대한 답변을 찾을 수 있는 관련 문서가 없습니다.

질문: {ctx.question}

답변: 제공된 문서에서 이 질문에 대한 답변을 찾을 수 없습니다."""
        else:
            prompt = f"""당신은 도움이 되는 어시스턴트입니다. 다음 컨텍스트만을 사용하여 질문에 답변하세요.
컨텍스트에서 답을 찾을 수 없다면 "제공된 컨텍스트에서 이 정보를 찾을 수 없습니다"라고 답하세요.
컨텍스트를 기반으로 구체적이고 정확하게 답변하세요.

컨텍스트:
{ctx.compressedCtx}

질문: {ctx.question}

답변:"""
        return Result.ok(ctx.withPrompt(prompt))

class GenerateStep:
    def __init__(self, llm: LlmClient, system: str = None):
        self._llm = llm
        self._system = system

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        # IO boundary: LLM call
        res = await self._llm.generate(ctx.prompt, system=self._system)
        if res.isErr():
            return Result.err(res.getError())
        return Result.ok(ctx.withRawLlm(res.getValue()))

class ParseStep:
    def __init__(self, parser: OutputParser):
        self._parser = parser

    async def run(self, ctx: RagContext) -> Result[RagContext]:
        obj = self._parser.parse(ctx.rawLlm)
        ans = Answer(text=obj.get("answer", ctx.rawLlm), metadata={"ctxIds": [r.chunk.id for r in ctx.reranked]})
        return Result.ok(ctx.withParsed(ans))
