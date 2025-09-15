# Embedder Manager Migration Guide

## 새로운 임베더 시스템 개요

기존의 하드코딩된 임베더 시스템을 **"전략 선택 + 정책 + 매니저" 3단 구조**로 완전히 재설계했습니다.

### 주요 개선사항

1. **완전한 YAML 외부화**: 모든 모델 설정이 `config/embeddings.yml`에서 관리됨
2. **정책 기반 자동 선택**: 텍스트 특성(언어 비율 등)에 따라 최적 모델 자동 선택
3. **네임스페이스 버전 관리**: 모델 변경 시 자동으로 다른 네임스페이스 사용
4. **스레드 세이프 캐싱**: 동시성 문제 없이 안전한 모델 로딩
5. **명시적 실패 처리**: Result 타입으로 예측 가능한 에러 처리

## 파일 구조

```
rag/adapters/embedders/
├── __init__.py           # 패키지 초기화
├── base.py              # 기본 인터페이스와 유틸리티
├── sentence_transformers_embedder.py  # Sentence Transformers 구현
├── manager.py           # 정책과 매니저 로직
└── adapter.py           # 기존 코드 호환성 어댑터

config/
└── embeddings.yml       # 임베더 설정 파일
```

## 설정 파일 (embeddings.yml)

```yaml
embedders:
  default: "auto"  # auto = 정책으로 자동 결정
  registry:
    multilingual_minilm:  # 다국어 지원 (한국어 포함)
      kind: "sentence-transformers"
      model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
      dim: 384
      normalize: true
      device: "auto"
      batchSize: 64
    
    all_minilm:  # 영어 특화
      kind: "sentence-transformers"
      model: "all-MiniLM-L6-v2"
      dim: 384
      # ... 

policy:
  koThreshold: 0.30  # 한국어 비율 임계값
  preferGpu: true
  order: ["multilingual_minilm", "all_minilm", "fallback_384"]
```

## 사용 방법

### 1. 기본 사용 (자동 선택)

```python
from adapters.embedders.manager import EmbedderManager

# 매니저 생성
manager = EmbedderManager.fromYaml("config/embeddings.yml")

# 텍스트에 따라 자동으로 최적 모델 선택
texts = ["한국어 문서입니다", "English document"]
embedder, signature = manager.resolve("auto", texts)

# 임베딩 수행
embeddings = embedder.embedTexts(texts)

# 네임스페이스 생성 (벡터 DB용)
namespace = manager.namespaceFor(signature)
```

### 2. 특정 프로필 사용

```python
# 특정 모델 강제 지정
embedder, sig = manager.resolve("multilingual_minilm", [])
```

### 3. 차원 검증

```python
# 인덱스와 임베더의 차원이 일치하는지 확인
result = manager.ensureDim(expected_dim, embedder)
if not result.ok:
    print(f"차원 불일치: {result.error}")
```

## 마이그레이션 체크리스트

- [x] `config/embeddings.yml` 생성
- [x] `rag/adapters/embedders/` 모듈 구조 생성
- [x] `server.py`에서 EmbedderManager 사용하도록 수정
- [x] 기존 코드 호환성 유지 (adapter.py)
- [x] 테스트 스크립트 작성 (test_embedder_manager.py)

## 테스트

```bash
# 임베더 매니저 테스트
python test_embedder_manager.py

# 전체 시스템 테스트
python health_check.py
```

## 향후 확장 가능성

1. **OpenAI 임베딩 추가**
   - `kind: "openai"` 프로필 추가
   - API 키 관리 로직 통합

2. **비용 기반 정책**
   - costTier 활용한 모델 선택
   - 사용량 추적 및 제한

3. **성능 모니터링**
   - 각 모델별 latency 추적
   - 자동 성능 기반 선택

## 주의사항

- 모델 변경 시 자동으로 새 네임스페이스가 생성되므로 기존 인덱스와 분리됨
- sentence-transformers가 설치되지 않은 경우 fallback 모드로 동작
- YAML 파일이 없으면 최소 구성으로 자동 폴백

## Article 원칙 준수

- **Error Handling**: IO 경계에서만 예외 처리
- **Method Length**: 모든 메서드 25줄 이하
- **Guard Clauses**: 조기 반환 패턴 적용
- **Result Type**: 예측 가능한 실패 모델링
- **No Debug Code**: 프로덕션 빌드에 디버그 코드 없음
