# 시스템 명령어 실행 및 파이프라인 제어를 위한 리눅스 내장 모듈 임포트
import subprocess

# 프로그램이 시작되었음을 작업자 터미널에 알리는 메시지 출력
print("Cisco 라우터/스위치 ACL 차단 로그 모니터링을 시작한다... (종료: Ctrl+C)")

# tail 명령어로 우분투에 분리 적재된 cisco_devices.log 파일만 실시간 추적 시작
process = subprocess.Popen(['tail', '-F', '/var/log/cisco_devices.log'], stdout=subprocess.PIPE, text=True)

# 파이프를 통해 들어오는 터미널 출력 데이터를 한 줄씩 무한 반복하며 읽어들임
for line in process.stdout:
    
    # 라우터/스위치의 명시적 ACL 정책 위반(차단)을 의미하는 고유 키워드 확인
    if "%SEC-6-IPACCESSLOG" in line:
        
        # 줄바꿈 문자를 제거하고 해당 차단 내역을 터미널에 출력
        print(f"[IOS 라우터 방어] {line.strip()}")
