import concurrent.futures
import threading
import time

# --- 1. 주의해서 쓰면 된다는 '가변 싱글톤' ---
# (예시로 든 'dict'처럼 '가변 상태(counter)'를 가짐)

class NaiveMutableSingleton:
    _instance = None
    
    def __new__(cls):
        # 고전적인 싱글톤 구현
        if cls._instance is None:
            time.sleep(0.0001) # 스레드 충돌을 유도하기 위한 약간의 딜레이
            cls._instance = super().__new__(cls)
            cls._instance.counter = 0 # <-- 이것이 '공유된 가변 상태'
        return cls._instance

    def increment(self):
        """
        이 함수는 '스레드 안전(Thread-Safe)'하지 않는다
        """
        current_val = self.counter  # 1. 값 읽기 (Read)
        
        # --- 위험 구간 (Critical Section) ---
        # 이 시점에 다른 스레드가 끼어들어 'current_val'을 동시에 읽을 수 있음!
        time.sleep(0.0001) # 다른 스레드가 끼어들 시간을 강제로 만듦
        # --- 위험 구간 끝 ---
        
        self.counter = current_val + 1 # 2. 값 쓰기 (Write)

# --- 2. '에이도비'의 테스트(asyncio)가 아닌, '진짜 병렬' 테스트 ---
# 멀티 스레드 (ThreadPoolExecutor)를 사용

NUM_THREADS = 10     # 10개의 스레드 (병렬 에이전트)
NUM_TASKS_PER_THREAD = 100 # 각 스레드가 100번씩 작업
TOTAL_TASKS = NUM_THREADS * NUM_TASKS_PER_THREAD # 총 예상 값 = 10 * 100 = 1000

print(f"--- '가변 싱글톤' 병렬 안정성 테스트 ---")
print(f"{NUM_THREADS}개의 병렬 스레드(에이전트)가 싱글톤의 counter를 {NUM_TASKS_PER_THREAD}번씩 총 {TOTAL_TASKS}번 증가시킵니다.")
#print("('내' 주장: '가변 싱글톤'은 병렬 환경에서 데이터 경쟁을 일으킨다)\n")

def run_task(task_id):
    s = NaiveMutableSingleton()
    for _ in range(NUM_TASKS_PER_THREAD):
        s.increment()
    # print(f"스레드 {task_id} 완료...") # 주석 해제 시 더 복잡하게 얽힘

# 진짜 병렬 실행
with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
    futures = [executor.submit(run_task, i) for i in range(NUM_THREADS)]
    concurrent.futures.wait(futures)

# --- 3. 결과 ---
final_counter = NaiveMutableSingleton().counter

print("\n--- 테스트 결과 ---")
print(f"예상 최종 값 (기대 값): {TOTAL_TASKS}")
print(f"실제 최종 값 (측정 값): {final_counter}")

if final_counter == TOTAL_TASKS:
    print("\n결과: ✅ 성공 (이론상 거의 불가능한 확률)")
else:
    print(f"\n결과: ❌ 대실패! (값이 깨짐)")
    print(f"이유: {TOTAL_TASKS - final_counter}번의 쓰기(write) 작업이 '데이터 경쟁'으로 인해 유실됨.")
    print("이것이 '공유된 가변 상태'를 병렬로 접근할 때의 위.")

#print("\n--- 결론 ---")
#print("1. `asyncio.gather` 테스트는 '단일 스레드' 비동기라 이 문제를 발견조차 못함")
#print("2. '주의해서 쓴다'는 말은, 모든 'increment' 함수에 'Lock'을 걸어야 한다는 뜻이며, 이는 코드를 복잡하게 하고 성능을 저하시킴.")
#print("3. 내 방식(DI + Lifespan)은 애초에 이런 '가변 상태'를 공유하지 않고,")
#print("   '스레드 세이프'하거나 '불변'한 객체의 '참조'를 주입하므로, 아키텍처 수준에서 이 위험이 없음.")