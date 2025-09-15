# 서버 시작 가이드

## 서버 시작 옵션

### 1. 개발 모드 (Auto-reload 포함)
```bash
# 옵션 1: start_server.py 사용 (권장)
python start_server.py

# 옵션 2: run_server.py 사용
python run_server.py
```

**특징:**
- 파일 변경 시 자동으로 서버 재시작
- tests/ 폴더와 문서 파일은 제외 (reload 트리거 안 함)
- 디버깅에 유용

### 2. 프로덕션 모드 (Auto-reload 없음)
```bash
python start_server_prod.py
```

**특징:**
- Auto-reload 비활성화로 안정성 향상
- 프로덕션 환경에 적합
- 더 나은 성능

### 3. 직접 실행
```bash
# 기본 설정으로 실행
uvicorn server:app --host 127.0.0.1 --port 7001

# 프로덕션 설정
uvicorn server:app --host 0.0.0.0 --port 7001 --workers 4
```

## 문제 해결

### Reload 관련 에러 발생 시

**증상:**
- `WARNING: WatchFiles detected changes...` 메시지 후 서버 충돌
- `asyncio.exceptions.CancelledError` 에러

**해결 방법:**

1. **프로덕션 모드 사용:**
   ```bash
   python start_server_prod.py
   ```

2. **특정 폴더 제외:**
   이미 설정되어 있지만, 추가 제외가 필요하면 `start_server.py`의 `reload_excludes` 수정

3. **완전 재시작:**
   ```bash
   # 프로세스 확인 및 종료
   tasklist | findstr python
   taskkill /F /PID [PID번호]
   
   # 다시 시작
   python start_server.py
   ```

## 서버 스크립트 비교

| 스크립트 | Auto-reload | 용도 | 포트 |
|---------|------------|------|------|
| start_server.py | (tests 제외) | 개발 | config.yaml |
| run_server.py | (tests 제외) | 개발 | 7001 |
| start_server_prod.py | | 프로덕션 | config.yaml |

## 서버 상태 확인

서버가 정상 작동 중인지 확인:

```bash
# 헬스 체크
curl http://localhost:7001/health

# 또는 브라우저에서
http://localhost:7001/docs
```

## 권장 사항

- **개발 중**: `start_server.py` 사용 (config 기반, reload 포함)
- **테스트 중**: `start_server_prod.py` 사용 (안정성)
- **배포 시**: Docker 또는 systemd 서비스로 실행

## 임베더 매니저 확인

서버 시작 시 다음 메시지가 표시되면 정상:
```
Embedder manager initialized successfully
```

실패 시:
```
Warning: Failed to load embedder manager: ...
Using legacy embedder factory
```

이 경우 `config/embeddings.yml` 파일을 확인하세요.
