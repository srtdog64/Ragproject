# RAG System Configuration Update

## 새로운 기능

### 1. 실시간 청킹 전략 변경
- 서버 재시작 없이 청킹 전략을 변경할 수 있습니다
- 5가지 청킹 전략 지원: sentence, paragraph, sliding_window, adaptive, simple_overlap

### 2. YAML 설정 파일 지원
- `config.yaml` 파일로 모든 설정을 관리합니다
- 하드코딩된 값들이 설정 파일로 외부화되었습니다
- 환경 변수로 설정을 오버라이드할 수 있습니다

### 3. REST API 엔드포인트
- `/api/chunkers/strategies` - 모든 전략 목록
- `/api/chunkers/strategy` - 현재 전략 조회/변경
- `/api/chunkers/params` - 파라미터 조회/수정
- `/config/reload` - 설정 파일 재로드

## 설치

```bash
# 필요한 패키지 설치
pip install -r requirements.txt
```

## 서버 실행

```bash
# 기본 실행
python server.py

# 또는 uvicorn 직접 실행
uvicorn server:app --reload --port 8000
```

## 설정 파일 (config.yaml)

주요 설정 항목:

```yaml
# 정책 설정
policy:
  maxContextChars: 8000  # 최대 컨텍스트 문자 수
  defaulttopK: 5          # 기본 검색 결과 수

# 청킹 설정
chunker:
  default_strategy: "adaptive"  # 기본 전략
  default_params:
    maxTokens: 512
    windowSize: 1200
    overlap: 200
```

## 실시간 전략 변경

### CLI 도구 사용
```bash
python test_chunking.py
```

### API 직접 호출
```python
import requests

# 현재 전략 확인
resp = requests.get("http://localhost:8000/api/chunkers/strategy")

# 전략 변경
requests.post(
    "http://localhost:8000/api/chunkers/strategy",
    json={"strategy": "paragraph"}
)
```

## 청킹 전략 가이드

| 전략 | 설명 | 적합한 문서 |
|-----|------|------------|
| sentence | 문장 단위 분할 | 짧은 QA, 대화 로그 |
| paragraph | 문단 단위 분할 | 기술 문서, 매뉴얼 |
| sliding_window | 겹침있는 고정 크기 | 긴 소설, 보고서 |
| adaptive | 자동 최적 선택 | 일반 문서 |
| simple_overlap | 단순 겹침 분할 | 코드, 로그 파일 |

## 환경 변수 오버라이드

설정을 환경 변수로 오버라이드할 수 있습니다:

```bash
# 예시
export RAG_POLICY_MAXCONTEXTCHARS=10000
export RAG_CHUNKER_DEFAULT_STRATEGY=paragraph
python server.py
```

## 상세 가이드

자세한 사용법은 `CHUNKING_GUIDE.md` 파일을 참조하세요.

## 문제 해결

### ModuleNotFoundError: No module named 'flask'
- Flask는 더 이상 필요하지 않습니다. FastAPI만 사용합니다.

### 서버가 시작되지 않음
- `config.yaml` 파일이 프로젝트 루트에 있는지 확인하세요
- `requirements.txt`의 모든 패키지가 설치되었는지 확인하세요

### 전략이 변경되지 않음
- `/config/reload` 엔드포인트를 호출하여 설정을 다시 로드하세요
- 서버 로그를 확인하여 에러가 없는지 확인하세요

## 성능 최적화 팁

1. **적절한 청킹 크기 선택**
   - 너무 작으면: 많은 청크 생성, 검색 성능 저하
   - 너무 크면: 정밀도 감소, 토큰 제한 초과 위험

2. **전략별 최적 파라미터**
   - sentence: `sentenceMinLen=10-20`
   - paragraph: `paragraphMinLen=50-100`
   - sliding_window: `overlap=windowSize*0.15-0.25`

3. **문서 유형별 전략**
   - 구조화된 문서 → paragraph
   - 대화형 콘텐츠 → sentence
   - 일반 텍스트 → adaptive

## 🔮 향후 계획

- [ ] 의미 기반 청킹 (Semantic Chunking)
- [ ] TextTiling 알고리즘 구현
- [ ] 청킹 품질 메트릭 추가
- [ ] 웹 UI 대시보드
- [ ] 벤치마킹 도구

---

최종 업데이트: 2025-09-05
