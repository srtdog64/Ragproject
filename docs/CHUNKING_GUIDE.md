# RAG Chunking Strategy System - 사용 가이드

## 개요
이제 RAG 시스템에서 청킹 전략을 실시간으로 변경할 수 있습니다. 문서의 특성에 따라 최적의 청킹 방법을 선택하여 검색 품질을 향상시킬 수 있습니다.

## 지원하는 청킹 전략

### 1. **sentence** (문장 단위)
- 문장 경계로 텍스트를 분할
- 각 청크가 완전한 문장을 포함
- 짧은 QA나 대화 로그에 적합

### 2. **paragraph** (문단 단위)
- 문단 경계로 텍스트를 분할
- 구조화된 문서(매뉴얼, 논문)에 적합
- 긴 문단은 자동으로 하위 분할

### 3. **sliding_window** (슬라이딩 윈도우)
- 고정 크기 청크에 overlap 적용
- 문맥 연속성 보장
- 긴 문서나 소설에 적합

### 4. **adaptive** (적응형)
- 문서 특성을 자동 분석
- 최적 전략을 동적 선택
- 대부분의 일반 문서에 권장

### 5. **simple_overlap** (단순 겹침)
- 기존 SimpleOverlapChunker
- 고정 크기와 겹침으로 간단한 분할

## 실시간 전략 변경 방법

### 1. CLI 테스트 도구 사용
```bash
python test_chunking.py
```

메뉴에서 선택:
- 1: 모든 전략 목록 보기
- 2: 현재 파라미터 확인
- 3: 전략 변경
- 4: 파라미터 수정

### 2. REST API 직접 호출

**현재 전략 확인:**
```bash
curl http://localhost:8000/api/chunkers/strategy
```

**전략 변경:**
```bash
curl -X POST http://localhost:8000/api/chunkers/strategy \
  -H "Content-Type: application/json" \
  -d '{"strategy": "paragraph"}'
```

**파라미터 수정:**
```bash
curl -X POST http://localhost:8000/api/chunkers/params \
  -H "Content-Type: application/json" \
  -d '{"windowSize": 1000, "overlap": 150}'
```

## 파라미터 설명

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| maxTokens | 512 | 최대 토큰 수 |
| windowSize | 1200 | 슬라이딩 윈도우 크기 |
| overlap | 200 | 청크 간 겹침 크기 |
| semanticThreshold | 0.82 | 의미 유사도 임계값 |
| language | "ko" | 언어 설정 (ko/en) |
| sentenceMinLen | 10 | 최소 문장 길이 |
| paragraphMinLen | 50 | 최소 문단 길이 |

## 전략 선택 가이드

### 문서 유형별 권장 전략

1. **기술 문서/매뉴얼**: `paragraph`
   - 명확한 구조와 섹션 구분
   - 각 문단이 하나의 주제

2. **대화/채팅 로그**: `sentence`
   - 짧은 발화 단위
   - 문맥 독립적 내용

3. **긴 소설/보고서**: `sliding_window`
   - 연속적인 내러티브
   - 문맥 연결 중요

4. **혼합/일반 문서**: `adaptive`
   - 자동으로 최적 전략 선택
   - 기본 권장 설정

5. **코드/로그 파일**: `simple_overlap`
   - 고정 크기 분할 필요
   - 단순한 구조

## 설정 파일

설정은 자동으로 저장됩니다:
```
E:\Ragproject\rag\chunkers\config.json
```

예시:
```json
{
  "strategy": "adaptive",
  "params": {
    "maxTokens": 512,
    "windowSize": 1200,
    "overlap": 200,
    "semanticThreshold": 0.82,
    "language": "ko",
    "sentenceMinLen": 10,
    "paragraphMinLen": 50
  }
}
```

## 주의사항

1. **전략 변경 시 재인덱싱 필요**
   - 기존 문서는 이전 전략으로 청킹됨
   - 새 전략은 새로 추가되는 문서에만 적용

2. **성능 고려사항**
   - `adaptive`: 분석 오버헤드 있음
   - `sliding_window`: 중복으로 저장 공간 증가
   - `sentence`: 많은 작은 청크 생성 가능

3. **언어별 최적화**
   - 한국어: 문장 경계 감지 특별 처리
   - 영어: 표준 구두점 기반 분할

## 문제 해결

**서버가 응답하지 않음:**
```bash
python server.py  # 서버 시작
```

**전략이 변경되지 않음:**
- config.json 파일 권한 확인
- 서버 재시작 시도

**청킹 결과가 예상과 다름:**
- 파라미터 조정 필요
- 다른 전략 시도

## 다음 단계

1. 벡터 임베딩 품질 향상
2. 의미 기반 청킹 강화
3. 멀티모달 문서 지원
4. 실시간 성능 모니터링

---
작성일: 2025-09-05
버전: 1.0
