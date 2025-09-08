# Qt6 앱 성능 최적화 추가 제안

## 1. health check 타이머 간격 조정
현재 3초마다 health check를 하는 것을 10초로 늘리기:
```python
# qt_app.py의 __init__ 메서드에서
self.healthTimer.start(10000)  # 3000 -> 10000 (10초)
```

## 2. 디버그 프린트 제거
실제 운영 시에는 모든 print() 문을 제거하거나 주석 처리:
```python
# print(f"[Worker] ...") -> # print(f"[Worker] ...")
```

## 3. 로그 표시 개수 제한
LogsWidget에서 화면에 표시되는 로그를 200개로 제한 (이미 적용됨)

## 4. 채팅 히스토리 제한
ChatDisplay에서 메시지가 너무 많아지면 오래된 메시지 제거:
```python
def add_message(self, role: str, content: str):
    # 메시지가 100개 이상이면 오래된 것 제거
    if self.document().blockCount() > 100:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 10)
        cursor.removeSelectedText()
```

## 5. 문서 목록 가상화
DocumentsWidget에서 많은 문서가 있을 때 QListView 대신 QTableView with lazy loading 사용

## 6. 메모리 누수 방지
Worker thread가 완료되면 명시적으로 정리:
```python
def handleResult(self, data: Dict):
    # ... 처리 후
    if self.worker.isFinished():
        self.worker.deleteLater()
        self.worker = RagWorkerThread(self.config)
        self.worker.finished.connect(self.handleResult)
        # ... 재연결
```

## 7. 이벤트 루프 최적화
장시간 실행되는 작업에 QApplication.processEvents() 추가:
```python
# 긴 반복문 안에서
if i % 10 == 0:  # 10번마다
    QApplication.processEvents()
```

## 최종 권장사항
- **즉시 적용**: updateVectorCount 비동기화 (완료)
- **필수**: health check 간격 늘리기
- **권장**: 디버그 프린트 제거
- **선택**: 나머지 최적화는 성능 문제가 지속될 경우 적용
