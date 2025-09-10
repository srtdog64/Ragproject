# RAG (Retrieval-Augmented Generation) System

A production-ready RAG system with Qt-based UI for document indexing and intelligent question answering.

## 🚀 Features

- **Multi-Provider LLM Support**: Gemini, OpenAI, Claude
- **Advanced Document Processing**: Multiple chunking strategies (adaptive, semantic, fixed, sentence-based)
- **Intelligent Retrieval**: Vector search with BM25 reranking
- **Real-time UI**: Qt-based desktop application with progress tracking
- **Asynchronous Processing**: Background document ingestion
- **Configurable Pipeline**: Modular architecture with dependency injection

## 📋 Prerequisites

- Python 3.8+
- Qt/PySide6
- ChromaDB for vector storage

## 🔧 Installation

1. **Clone the repository**
```bash
git clone [your-repo-url]
cd Ragproject
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env and add your API keys
# At minimum, you need to set:
# GEMINI_API_KEY=your_actual_api_key_here
```

## 🔑 API Keys Setup

### Gemini (Required)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`: `GEMINI_API_KEY=your_key_here`

### OpenAI (Optional)
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### Claude (Optional)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

## 🎯 Quick Start

### Cross-Platform Launch (Recommended)

**Windows:**
```cmd
start_system.bat
```

**Linux/Mac:**
```bash
chmod +x start_system.sh
./start_system.sh
```

**Or directly with Python:**
```bash
python main.py
```

### Advanced Options

**Run server only:**
```bash
python main.py --server
```

**Run UI only (server must be running):**
```bash
python main.py --ui
```

**Specify custom port:**
```bash
python main.py --port 8000
```

## 📁 Project Structure

```
Ragproject/
├── main.py                # Main entry point
├── run_server.py         # Server launcher
├── qt_app.py            # Qt UI application
├── rag/                 # Core RAG system
│   ├── core/           # Core components
│   ├── pipeline/       # Pipeline steps
│   └── chunkers/       # Document chunking
├── server/             # FastAPI server
│   ├── routers/       # API endpoints
│   └── dependencies.py # Dependency injection
├── ui/                 # Qt UI components
│   ├── chat_widget.py # Main chat interface
│   └── options/       # Settings tabs
├── config/            # Configuration files
│   └── config.yaml   # Server configuration
└── chroma_db/        # Vector database storage
```

## ⚙️ Configuration

### Retrieval Settings
- `retrieve_k`: Number of documents to retrieve from vector store (default: 20)
- `rerank_k`: Number of documents after reranking (default: 5)
- `max_context_chars`: Maximum context size in characters (default: 12000)

### Chunking Strategies
- **Adaptive**: Smart chunking based on document structure
- **Semantic**: Meaning-based chunking using embeddings
- **Fixed**: Fixed-size chunks with overlap
- **Sentence**: Sentence-based chunking

## 🛠️ Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black .

# Check linting
pylint rag/
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

RAG 기능 끄고 켜기 추가해서, RAG 없이 단순 채팅용 LLM으로도 쓸수있게

## 📝 License

[Your License]

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Important Security Notes

- **NEVER** commit your `.env` file with actual API keys
- Always use `.env.sample` as a template
- Keep your API keys secure and rotate them regularly
- Review `.gitignore` before committing

## 🐛 Troubleshooting

### Server won't start
- Check if port 7001 is already in use
- Verify all dependencies are installed
- Ensure `.env` file exists with valid API keys

### Document ingestion fails
- Check file permissions
- Verify supported file formats (.txt, .md, .pdf)
- Check available disk space for vector database

### UI not responding
- Restart both server and Qt application
- Check server logs for errors
- Verify network connectivity to localhost:7001

## 📧 Contact

[Your Contact Information]
