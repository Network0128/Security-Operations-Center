# 시스템 명령어 실행 및 파이프라인 제어를 위한 리눅스 내장 모듈 임포트
import subprocess

# 프로그램이 시작되었음을 작업자 터미널에 알리는 메시지 출력
print("ASAv 방화벽 자체 방어(To-the-box) 로그 모니터링을 시작한다... (종료: Ctrl+C)")

# tail 명령어로 우분투에 분리 적재된 asav.log 파일의 끝부분만 실시간 추적 시작
process = subprocess.Popen(['tail', '-F', '/var/log/asav.log'], stdout=subprocess.PIPE, text=True)

# 파이프를 통해 들어오는 터미널 출력 데이터를 한 줄씩 무한 반복하며 읽어들임
for line in process.stdout:
    
    # 방화벽 장비 자체를 향한 스캔(To-the-box) 차단 로그 식별 (레벨 3)
    if "%ASA-3-313" in line:
        
        # 줄바꿈 문자를 제거하고, 라벨을 붙여 관제 터미널에 출력
        print(f"[ASAv 자체 방어] {line.strip()}")
