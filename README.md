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

## 📝 License

MIT License
