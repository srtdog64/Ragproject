# RAG System Pipeline Architecture

## Overview
이 문서는 RAG (Retrieval-Augmented Generation) 시스템의 전체 파이프라인 구조와 처리 흐름을 설명합니다.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Qt6 GUI Application                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   Chat   │ │Documents │ │ Options  │ │   Logs   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server (Port 7001)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                          │   │
│  │  /ingest  /ask  /health  /api/chunkers/*                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
        ┌──────────────┐              ┌──────────────┐
        │   Ingestion  │              │   Retrieval  │
        │   Pipeline   │              │   Pipeline   │
        └──────────────┘              └──────────────┘
```

## Ingestion Pipeline (문서 처리)

### 1️⃣ Document Input
```python
Document {
    id: str
    title: str
    source: str
    text: str
}
```

### 2️⃣ Chunking (청킹)
문서를 작은 단위로 분할
- **Strategies**: 
  - `sentence`: 문장 단위 분할
  - `paragraph`: 단락 단위 분할
  - `sliding_window`: 고정 크기 윈도우
  - `adaptive`: 자동 선택
  - `simple_overlap`: 오버랩이 있는 고정 크기

### 3️⃣ Embedding (임베딩)
각 청크를 벡터로 변환
- **Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Dimension**: 384

### 4️⃣ Vector Store (벡터 저장소)
임베딩된 벡터를 저장
- **Options**:
  - `InMemoryVectorStore`: 휘발성 (서버 재시작시 소실)
  - `ChromaVectorStore`: 영속성 (./chroma_db에 저장)
  - `FAISS`: (구현 예정)

## Retrieval Pipeline (검색 및 답변)

### 1️⃣ Query Expansion
질문을 확장하여 검색 성능 향상
```
Original: "RAG란 무엇인가?"
Expanded: ["RAG란 무엇인가?", "RAG란 무엇인가? (alt 1)", ...]
```

### 2️⃣ Vector Retrieval
질문을 임베딩하고 유사한 청크 검색
- **Similarity**: Cosine similarity
- **Top-K**: 기본 5개

### 3️⃣ Reranking (재순위화)
검색된 결과를 재정렬
- **Options**:
  - `IdentityReranker`: 재순위화 없음
  - `SimpleScoreReranker`: 제목 매칭, 위치 기반
  - `CrossEncoderReranker`: Cross-Encoder 모델 사용

### 4️⃣ Context Compression
컨텍스트를 최대 문자수에 맞게 압축
- **Max Context**: 8000 characters

### 5️⃣ Prompt Building
LLM에 전달할 프롬프트 구성
```
시스템: 당신은 도움이 되는 어시스턴트입니다...
컨텍스트: [검색된 문서들]
질문: [사용자 질문]
답변:
```

### 6️⃣ Generation (생성)
LLM을 사용해 답변 생성
- **Models**: 
  - Gemini (gemini-2.5-flash, gemini-2.5-pro)
  - OpenAI (gpt-4o, gpt-3.5-turbo)
  - Claude (claude-3-opus, claude-3-sonnet)

### 7️⃣ Parsing (파싱)
LLM 응답을 파싱하여 최종 답변 추출

## Configuration Files

### `/config/config.yaml`
메인 설정 파일
```yaml
chunker:
  default_strategy: sentence
  default_params:
    maxTokens: 512
    overlap: 200
    
store:
  type: chroma  # memory, chroma, faiss
  persist_directory: ./chroma_db
  
reranker:
  type: simple  # identity, simple, cross-encoder
  
llm:
  type: gemini
  model: gemini-2.5-flash
  temperature: 0.9
```

### `/config/embeddings.yml`
임베딩 모델 설정
```yaml
embedders:
  semantic:
    type: sentence_transformers
    model: paraphrase-multilingual-MiniLM-L12-v2
```

## Project Structure

```
E:\Ragproject\
├── config/                 # 설정 파일들
│   ├── config.yaml
│   ├── embeddings.yml
│   └── qt_app_config.yaml
├── docs/                   # 문서들
│   ├── API_DOCUMENTATION.md
│   ├── PIPELINE.md
│   └── README.md
├── rag/                    # 핵심 RAG 모듈
│   ├── chunkers/          # 청킹 전략
│   ├── stores/            # 벡터 저장소
│   ├── retrievers/        # 검색기
│   ├── rerankers/         # 리랭커
│   ├── pipeline/          # 파이프라인
│   ├── llms/              # LLM 클라이언트
│   └── core/              # 핵심 타입/인터페이스
├── ui/                     # Qt GUI 컴포넌트
│   ├── chat_widget.py
│   ├── documents_widget.py
│   ├── options_widget.py
│   └── logs_widget.py
├── tests/                  # 테스트 파일들
│   ├── test_*.py
│   ├── check_*.py
│   └── diagnose_*.py
├── server.py              # FastAPI 서버
├── qt_app.py              # Qt 애플리케이션
└── start_server.py        # 서버 시작 스크립트
```

## Quick Start

### 1. 서버 시작
```bash
python start_server.py
```

### 2. Qt 앱 시작
```bash
python qt_app.py
```

### 3. 시스템 사용
1. **Documents 탭**: 문서 업로드
2. **Ingest 버튼**: 문서 인덱싱
3. **Chat 탭**: 질문하기
4. **Options 탭**: 전략 및 파라미터 조정

## Data Flow Example

```
User Question: "RAG란 무엇인가?"
    ↓
[Query Expansion]
    ↓
[Embedding: question → vector]
    ↓
[Vector Search: find similar chunks]
    ↓
[Reranking: reorder by relevance]
    ↓
[Context: top 5 chunks]
    ↓
[LLM Generation: context + question → answer]
    ↓
Answer: "RAG는 검색 증강 생성..."
```

## Key Components

### Chunkers (`/rag/chunkers/`)
- `ChunkerRegistry`: 전략 관리
- `SentenceChunker`: 문장 기반 청킹
- `ParagraphChunker`: 단락 기반 청킹
- `SlidingWindowChunker`: 슬라이딩 윈도우
- `AdaptiveChunker`: 자동 선택

### Vector Stores (`/rag/stores/`)
- `InMemoryVectorStore`: 메모리 기반
- `ChromaVectorStore`: ChromaDB 기반 영속 저장소

### Rerankers (`/rag/rerankers/`)
- `IdentityReranker`: 순서 유지
- `SimpleScoreReranker`: 휴리스틱 기반
- `CrossEncoderReranker`: ML 모델 기반

### LLM Clients (`/rag/llms/`)
- `GeminiClient`: Google Gemini API
- `OpenAIClient`: OpenAI API
- `ClaudeClient`: Anthropic Claude API

## 📈 Performance Considerations

1. **Chunking Strategy**: 문서 타입에 맞는 전략 선택
2. **Chunk Size**: 너무 크면 정확도 감소, 너무 작으면 컨텍스트 부족
3. **Embedding Model**: 다국어 지원 vs 성능 트레이드오프
4. **Vector Store**: 영속성 필요시 ChromaDB 사용
5. **Reranking**: 정확도 향상을 위해 활성화 권장

## Troubleshooting

### 서버가 시작되지 않을 때
```bash
python tests/diagnose_server.py
```

### 벡터 저장소 문제
```bash
python tests/check_vector_store.py
```

### RAG 파이프라인 테스트
```bash
python tests/test_rag_retrieval.py
```

## Notes

- 기본 포트: 7001
- API 문서: http://localhost:7001/docs
- 로그 레벨: config.yaml에서 조정 가능
- 데이터 영속성: ChromaDB 사용 권장
