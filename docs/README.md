# RAG System (Qt6-Ready)

중급 수준의 모듈형 RAG(Retrieval-Augmented Generation) 시스템입니다.
DI(Dependency Injection)와 빌더 패턴을 사용하여 교체 가능한 구조로 설계되었습니다.

## 특징

- **모듈형 설계**: DI Container를 통한 컴포넌트 교체 가능
- **단계 조립형 파이프라인**: 각 처리 단계를 독립적으로 조합 가능
- **Result<T> 패턴**: 명시적 에러 처리
- **비동기 처리**: 병렬 배치 처리 지원
- **Qt6 연동 준비**: FastAPI 기반 HTTP API 제공

## 디렉터리 구조

```
Ragproject/
├── rag/
│   ├── core/           # 핵심 타입, 인터페이스, 정책
│   ├── di/             # DI Container
│   ├── adapters/       # LLM, Embedder 어댑터
│   ├── chunkers/       # 문서 청킹 전략
│   ├── stores/         # 벡터 스토어
│   ├── retrievers/     # 검색 구현
│   ├── rerankers/      # 재순위화
│   ├── parsers/        # 출력 파서
│   ├── pipeline/       # 파이프라인 빌더
│   ├── ingest/         # 문서 인제스트
│   └── app.py          # 메인 애플리케이션
├── server.py           # FastAPI HTTP 서버
├── run_server.py       # 서버 실행 스크립트
├── test_client.py      # 테스트 클라이언트
├── sample_docs.json    # 샘플 문서
├── requirements.txt    # Python 의존성
└── README.md
```

## 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

## 실행

### 1. 서버 실행

```bash
python run_server.py
```

서버가 시작되면:
- API: http://localhost:7001
- 문서: http://localhost:7001/docs (Swagger UI)

### 2. 테스트

```bash
python test_client.py
```

### 3. API 사용

#### Health Check
```bash
curl http://localhost:7001/health
```

#### 문서 인제스트
```bash
curl -X POST http://localhost:7001/ingest \
  -H "Content-Type: application/json" \
  -d @sample_docs.json
```

#### 질문하기
```bash
curl -X POST http://localhost:7001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "k": 5}'
```

## Qt6 연동

Qt6 애플리케이션에서 RAG 서비스를 사용하는 방법:

### C++ Qt6
```cpp
QNetworkAccessManager *manager = new QNetworkAccessManager(this);
QNetworkRequest request(QUrl("http://localhost:7001/ask"));
request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

QJsonObject json;
json["question"] = "What is RAG?";
json["k"] = 5;

manager->post(request, QJsonDocument(json).toJson());
```

### PySide6
```python
import requests

def ask_rag(question: str, k: int = 5):
    response = requests.post(
        "http://localhost:7001/ask",
        json={"question": question, "k": k}
    )
    return response.json()
```

## 확장 포인트

1. **실제 Embedder 연결**
   - `adapters/hash_embedder.py`를 OpenAI/Sentence-Transformers로 교체

2. **실제 Vector Store 연결**
   - `stores/memory_store.py`를 FAISS/ChromaDB로 교체

3. **LLM 연결**
   - `adapters/llm_client.py`에서 실제 API 키와 SDK 연동

4. **Reranker 개선**
   - `rerankers/identity_reranker.py`를 Cross-Encoder로 교체

5. **파이프라인 단계 추가**
   - HybridRetriever (BM25 + Vector)
   - CitationStep (인용 추가)
   - VerificationStep (사실 검증)

## 주요 설계 원칙

- **Guard Clauses**: 모든 public 메서드 시작 시 입력 검증
- **Result<T> 패턴**: 예외 대신 명시적 Result 타입 사용
- **IO 경계에서만 try/except**: LLM 호출 등 외부 IO에서만 예외 처리
- **불변 데이터**: dataclass(frozen=True) 사용
- **25줄 제한**: 메서드는 25줄 이하로 유지

## 라이선스

MIT
