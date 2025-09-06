# Test Organization Update

## 📁 새로운 테스트 구조

모든 테스트 파일들이 `tests/` 폴더로 정리되었습니다.

```
E:\Ragproject\
├── tests/                      # 모든 테스트 파일
│   ├── __init__.py
│   ├── test_chunking.py        # 청킹 기능 테스트
│   ├── test_chunker_api.py     # 청커 API 테스트
│   ├── test_wrapper.py         # 래퍼 테스트
│   ├── test_embedder_manager.py # 새 임베더 매니저 테스트
│   ├── test_client.py          # 클라이언트 통합 테스트
│   ├── test_gemini.py          # Gemini API 테스트
│   ├── health_check.py         # 시스템 헬스 체크
│   ├── check_system.py         # 시스템 의존성 체크
│   └── debug_chunker.py        # 청커 디버깅 도구
│
└── run_tests.py                # 테스트 실행 도우미
```

## 🚀 테스트 실행 방법

### 방법 1: 테스트 러너 사용 (권장)
```bash
# 프로젝트 루트에서 실행
python run_tests.py

# 메뉴에서 선택:
# [1] Embedder Manager Tests
# [2] Chunking Tests
# [3] Client Tests
# [4] Gemini API Tests
# [5] System Health Check
# [6] System Dependencies Check
# [a] Run All Tests
```

### 방법 2: 개별 테스트 실행
```bash
# 프로젝트 루트에서 실행
python tests/test_embedder_manager.py
python tests/test_chunking.py
python tests/health_check.py
```

### 방법 3: Python 모듈로 실행
```bash
# 프로젝트 루트에서 실행
python -m tests.test_embedder_manager
python -m tests.test_chunking
python -m tests.health_check
```

## 📋 테스트 카테고리

### 단위 테스트 (Unit Tests)
- `test_chunking.py` - 다양한 청킹 전략 테스트
- `test_chunker_api.py` - 청커 API 엔드포인트 테스트
- `test_wrapper.py` - 청커 래퍼 기능 테스트
- `test_embedder_manager.py` - 임베더 매니저 테스트

### 통합 테스트 (Integration Tests)
- `test_client.py` - RAG 서버 클라이언트 테스트
- `test_gemini.py` - Gemini LLM 통합 테스트

### 시스템 체크 (System Checks)
- `health_check.py` - 전체 시스템 상태 확인
- `check_system.py` - 의존성 및 환경 확인
- `debug_chunker.py` - 청킹 디버그 도구

## 🔧 트러블슈팅

테스트 실행 시 import 에러가 발생하면:

1. 프로젝트 루트 디렉토리에서 실행하는지 확인
2. Python path 확인:
   ```python
   import sys
   print(sys.path)
   ```
3. 필요한 의존성 설치:
   ```bash
   pip install -r requirements.txt
   ```
