# app.py
import asyncio
from di.container import Container
from core.policy import Policy
from core.types import Document, RagContext
from adapters.llm_client import OpenAiLlm
from adapters.hash_embedder import HashEmbedder
from chunkers.overlap_chunker import SimpleOverlapChunker
from stores.memory_store import InMemoryVectorStore
from retrievers.vector_retriever import VectorRetrieverImpl
from rerankers.identity_reranker import IdentityReranker
from parsers.parser_builder import ParserBuilder
from ingest.ingester import Ingester
from pipeline.steps import (
    QueryExpansionStep, RetrieveStep, RerankStep,
    ContextCompressionStep, BuildPromptStep, GenerateStep, ParseStep
)
from pipeline.builder import PipelineBuilder

def buildContainer() -> Container:
    c = Container()
    c.register("policy", lambda _: Policy(maxContextChars=8000, defaultTopK=5))
    c.register("embedder", lambda _: HashEmbedder(dim=96))
    c.register("store", lambda _: InMemoryVectorStore())
    c.register("chunker800", lambda _: SimpleOverlapChunker(size=800, overlap=120))
    c.register("chunker1200", lambda _: SimpleOverlapChunker(size=1200, overlap=160))
    c.register("llm", lambda _: OpenAiLlm(apiKey="DUMMY"))
    c.register("reranker", lambda _: IdentityReranker())
    return c

async def main() -> None:
    c = buildContainer()
    policy = c.resolve("policy")
    embedder = c.resolve("embedder")
    store = c.resolve("store")
    llm = c.resolve("llm")

    # --- Ingest with chunker800 ---
    ingesterA = Ingester(chunker=c.resolve("chunker800"), embedder=embedder, store=store, maxParallel=8)
    docs = [
        Document(id="d1", title="Guide", source="api://guide", text="RAG retrieves, reranks, compresses, generates, and parses."),
        Document(id="d2", title="LLM", source="api://llm", text="OpenAI and Claude are common LLM providers."),
    ]
    await ingesterA.ingest(docs)

    # --- Pipeline A: topK=5, chunker800 indexed data ---
    retrieverA = VectorRetrieverImpl(store=store, embedder=embedder, metaFilter=None)
    parser = ParserBuilder().setFormat("json").withJsonSchema({"type": "object", "required": ["answer"]}).build()
    pipelineA = (
        PipelineBuilder()
        .add(QueryExpansionStep(expansions=1))
        .add(RetrieveStep(retriever=retrieverA, policy=policy))
        .add(RerankStep(reranker=c.resolve("reranker"), topK=5))
        .add(ContextCompressionStep(policy=policy))
        .add(BuildPromptStep(systemHint="You are a helpful assistant."))
        .add(GenerateStep(llm=llm, system="You are concise."))
        .add(ParseStep(parser=parser))
        .build()
    )

    ctxA = RagContext(question="What is RAG?", k=5, expandedQueries=[], retrieved=[], reranked=[],
                      compressedCtx="", prompt="", rawLlm="", parsed=None)  # type: ignore
    resA = await pipelineA.run(ctxA)
    print("A:", resA.getValue().text if resA.isOk() else resA.getError())

    # --- Pipeline B: Different configuration (e.g., topK=8) ---
    ingesterB = Ingester(chunker=c.resolve("chunker1200"), embedder=embedder, store=store, maxParallel=8)
    await ingesterB.ingest([Document(id="d3", title="Deep", source="api://deep", text="Context compression keeps token within budget.")])

    retrieverB = VectorRetrieverImpl(store=store, embedder=embedder)
    pipelineB = (
        PipelineBuilder()
        .add(QueryExpansionStep(expansions=0))
        .add(RetrieveStep(retriever=retrieverB, policy=policy))
        .add(RerankStep(reranker=c.resolve("reranker"), topK=8))
        .add(ContextCompressionStep(policy=policy))
        .add(BuildPromptStep(systemHint="You are a helpful assistant."))
        .add(GenerateStep(llm=llm, system="Be precise."))
        .add(ParseStep(parser=parser))
        .build()
    )

    ctxB = RagContext(question="Explain context compression.", k=8, expandedQueries=[], retrieved=[], reranked=[],
                      compressedCtx="", prompt="", rawLlm="", parsed=None)  # type: ignore
    resB = await pipelineB.run(ctxB)
    print("B:", resB.getValue().text if resB.isOk() else resB.getError())

if __name__ == "__main__":
    asyncio.run(main())
