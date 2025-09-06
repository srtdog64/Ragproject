# RAG System Qt6 사용 가이드

## 목차
1. [시작하기](#시작하기)
2. [UI 구성](#ui-구성)
3. [사용 방법](#사용-방법)
4. [문제 해결](#문제-해결)

---

## 시작하기

### 간편 실행 (Windows)
```batch
start_rag.bat
```
이 배치 파일이 자동으로:
- 가상환경 생성
- 필요 패키지 설치
- 서버 시작
- Qt6 UI 실행

### 수동 실행

#### 1. 가상환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (Linux/Mac)
source venv/bin/activate
```

#### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

#### 3. 서버 시작
```bash
python run_server.py
```

#### 4. Qt6 UI 실행 (새 터미널)
```bash
python qt_app_styled.py
```

---

## UI 구성

### 메인 인터페이스

#### 1. Chat 탭
- **질문 입력**: 하단 입력창에 질문 입력 후 Enter 또는 Send 클릭
- **Top K 설정**: 검색할 문서 청크 개수 조정 (1-20)
- **대화 기록**: 질문과 답변이 시간순으로 표시
- **Clear Chat**: 대화 내용 초기화

#### 2. Documents 탭
- **문서 관리**: 추가, 편집, 삭제 기능
- **Import/Export**: JSON 파일로 문서 가져오기/내보내기
- **테이블 뷰**: 문서 목록과 미리보기

#### 3. Logs 탭
- 시스템 로그와 오류 메시지 확인

### 메뉴바

#### File 메뉴
- Import Documents: JSON 파일에서 문서 가져오기
- Export Documents: 현재 문서를 JSON으로 저장
- Exit: 프로그램 종료

#### Server 메뉴
- Check Status: 서버 상태 확인
- Ingest Documents: 문서를 RAG 시스템에 인덱싱

#### Help 메뉴
- About: 프로그램 정보

---

## 사용 방법

### 1. 문서 준비

#### 방법 A: 샘플 문서 사용
1. Documents 탭 → Import JSON 클릭
2. `sample_docs.json` 파일 선택
3. 5개 샘플 문서가 로드됨

#### 방법 B: 직접 입력
1. Documents 탭 → Add 버튼 클릭
2. 문서 정보 입력:
   - ID: 고유 식별자 (예: doc_1)
   - Title: 문서 제목
   - Source: 출처 URL 또는 설명
   - Text: 문서 내용
3. Save Document 클릭

#### 방법 C: 외부 JSON 가져오기
JSON 형식:
```json
{
  "documents": [
    {
      "id": "doc1",
      "title": "제목",
      "source": "출처",
      "text": "내용..."
    }
  ]
}
```

### 2. 문서 인제스트 (색인)

1. Server 메뉴 → Ingest Documents 클릭
2. 확인 대화상자에서 Yes 클릭
3. 상태바에서 진행 상황 확인
4. 성공 시 청크 개수 표시

### 3. 질문하기

1. Chat 탭으로 이동
2. Top K 값 설정 (기본: 5)
3. 하단 입력창에 질문 입력
4. Enter 키 또는 Send 버튼 클릭
5. 답변과 메타데이터 확인:
   - 답변 내용
   - 사용된 컨텍스트 ID
   - 응답 시간

### 4. 대화 관리

- **Clear Chat**: 대화 내용 삭제 (서버 데이터는 유지)
- **스크롤**: 자동으로 최신 메시지로 스크롤

---

## 문제 해결

### 서버 연결 오류
**증상**: "Cannot connect to server" 메시지

**해결책**:
1. 서버가 실행 중인지 확인
2. 터미널에서 `python run_server.py` 실행
3. http://localhost:7001/docs 접속 테스트

### 문서 인제스트 실패
**증상**: Ingest 시 오류 메시지

**해결책**:
1. 문서 형식 확인 (모든 필드 필수)
2. 문서 ID 중복 확인
3. 서버 로그 확인

### Qt6 UI 시작 안 됨
**증상**: UI 창이 열리지 않음

**해결책**:
```bash
pip install --upgrade PySide6
```

### 한글 인코딩 문제
**증상**: 한글 텍스트 깨짐

**해결책**:
- JSON 파일을 UTF-8 인코딩으로 저장
- 텍스트 에디터에서 인코딩 확인

---

## 고급 기능

### 서버 설정 변경
`server.py` 수정:
```python
# 포트 변경
uvicorn.run("server:app", port=8000)

# 최대 컨텍스트 크기 조정
Policy(maxContextChars=12000)
```

### UI 테마 변경
`qt_app_styled.py`의 `DARK_STYLE` 수정하여 색상과 스타일 커스터마이징

### 실제 LLM 연결
1. `adapters/llm_client.py` 수정
2. OpenAI 또는 Claude API 키 설정
3. 실제 API 호출 코드 구현

---

## 키보드 단축키

- **Enter**: 질문 전송
- **Ctrl+O**: 문서 가져오기
- **Ctrl+S**: 문서 내보내기
- **Ctrl+Q**: 프로그램 종료

---

## 시스템 요구사항

- Python 3.8+
- Windows/Linux/macOS
- RAM 4GB 이상
- 디스크 공간 1GB 이상

---

## 라이선스
MIT License

## 지원
문제 발생 시 Logs 탭의 내용을 확인하고 서버 콘솔 로그를 참조하세요.
