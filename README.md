# RAG System with Qt6 Interface

A Retrieval-Augmented Generation (RAG) system with modular architecture and Qt6 GUI.

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Start Server
```bash
python start_server.py
```

### Start Qt Application
```bash
python qt_app.py
```

## 📚 Documentation

- [System Pipeline Architecture](docs/PIPELINE.md) - Complete system overview
- [API Documentation](docs/API_DOCUMENTATION.md) - REST API reference
- [Full README](docs/README.md) - Detailed documentation

## 📁 Project Structure

```
├── config/     # Configuration files
├── docs/       # Documentation
├── rag/        # Core RAG modules
├── ui/         # Qt GUI components
├── tests/      # Test files
├── server.py   # FastAPI server
└── qt_app.py   # Qt application
```

## 🔧 Configuration

Edit `config/config.yaml` to customize:
- Chunking strategies
- Vector store (memory/persistent)
- LLM provider and model
- Reranking options

## 🧪 Testing

```bash
# Check server status
python tests/check_server.py

# Test RAG pipeline
python tests/test_rag_retrieval.py

# Test persistence
python tests/test_persistence_reranking.py
```

## TODO

제미니 API에 최적화된 부분 LLM Client, 래핑해서 모두에게 맞게 하기
평가 단계 추가

AdaptiveChunker 개선: 단순 휴리스틱을 넘어, langdetect와 같은 라이브러리를 사용하여 콘텐츠의 언어와 유형(산문, 코드, 표 등)을 명시적으로 탐지하는 단계를 추가. 
이를 통해 각 유형에 맞는 전문 청커(e.g., CodeChunker)로 작업을 위임하는 **전략 라우팅(Strategy Routing)**을 구현

EmbedderManager 정책 고도화: koRatio 대신, 토큰화된 결과물을 분석하여 한국어 형태소의 비율을 측정하는 등 더 정교한 언어 감지 로직을 도입 또한, 사용자가 특정 문서 그룹에 대해 임베딩 프로필을 수동으로 오버라이드할 수 있는 기능을 제공하여 정책의 실패를 보완

BM25Reranker 교체: **형태소 분석기(e.g., mecab-ko, okt)**를 사용하여 텍스트를 토큰화하는 BM25Reranker를 구현. rank_bm25 라이브러리는 커스텀 토크나이저 함수를 지원하므로 쉽게 통합할 수 있음

deleteByDoc 최적화: collection.get()과 collection.delete(ids=...)의 2단계 프로세스를 collection.delete(where={"docId": docId})의 단일 API 호출로 변경

프로덕션 배포 스크립트 분리: run_server.py (개발용, reload=True)와 별도로, Gunicorn과 uvicorn 워커를 사용하는 프로덕션용 실행 스크립트(run_prod.sh 등)와 Dockerfile을 작성하여 배포 환경을 표준화

현재 모든 파이프라인을 Unit화해서 단계를 노드로 해서 그래프화 할것

## 📝 License

MIT License
