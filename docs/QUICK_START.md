# 빠른 시작 가이드 (Quick Start Guide)

## 5분 만에 RAG 시스템 실행하기

### Windows 사용자
1. **E:\Ragproject** 폴더로 이동
2. **start_rag.bat** 더블클릭
3. 자동으로 서버와 UI가 실행됩니다!

### 수동 실행 (모든 OS)
```bash
# 1. 프로젝트 폴더로 이동
cd E:\Ragproject

# 2. 시스템 체크
python check_system.py

# 3. 서버 시작 (터미널 1)
python run_server.py

# 4. UI 실행 (터미널 2)
python qt_app_styled.py
```

---

## 첫 번째 RAG 테스트

### 1단계: 샘플 문서 로드
1. Qt UI 실행 후 **Documents** 탭 클릭
2. **Import JSON** 버튼 클릭
3. **sample_docs.json** 파일 선택
4. 5개 문서가 테이블에 표시됨

### 2단계: 문서 인덱싱
1. 메뉴바 → **Server** → **Ingest Documents** 클릭
2. 확인 대화상자에서 **Yes** 클릭
3. "Successfully ingested" 메시지 확인

### 3단계: 질문하기
1. **Chat** 탭으로 이동
2. 아래 예시 질문 중 하나 입력:
   - "What is RAG?"
   - "How do vector databases work?"
   - "Explain chunking strategies"
3. **Enter** 키 또는 **Send** 버튼 클릭
4. 답변과 메타데이터 확인

---

## UI 기능

### Chat 탭
- 실시간 대화 인터페이스
- Top K 조정 (1-20)
- 응답 시간 표시
- 🔗 컨텍스트 ID 표시

### Documents 탭
- 문서 추가/편집/삭제
- JSON 가져오기/내보내기
- 테이블 뷰로 관리

### Logs 탭
- 시스템 로그
- 오류 추적
- 🕐 타임스탬프

---

## 환경 설정

### 포트 변경
`run_server.py` 수정:
```python
uvicorn.run("server:app", port=8000)  # 7001 → 8000
```

### UI 테마
- 기본: 다크 테마
- 라이트 테마: `qt_app.py` 사용

---

## 문제 해결

### "Server not running" 오류
```bash
# 서버 수동 시작
python run_server.py
```

### "Module not found" 오류
```bash
# 패키지 재설치
pip install -r requirements.txt
```

### 시스템 체크
```bash
python check_system.py
```

---

## 다음 단계

1. **실제 LLM 연결**
   - OpenAI API 키 설정
   - `adapters/llm_client.py` 수정

2. **벡터 DB 업그레이드**
   - FAISS 설치: `pip install faiss-cpu`
   - ChromaDB: `pip install chromadb`

3. **문서 추가**
   - PDF 지원 추가
   - 웹 크롤링 기능

---

## 💡 팁

- **빠른 테스트**: 샘플 문서로 시작
- **커스텀 문서**: JSON 형식 준수
- **성능**: Top K를 낮추면 속도 향상
- **정확도**: Top K를 높이면 더 많은 컨텍스트

---

## 📞 지원

- 로그 확인: **Logs** 탭
- 서버 상태: 우측 하단 상태바
- 시스템 체크: `python check_system.py`

---

**Enjoy RAG! 🎉**
