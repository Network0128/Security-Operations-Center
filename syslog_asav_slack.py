# HTTP 통신을 위해 사전에 설치한 requests 라이브러리를 임포트한다.
import requests
# 시스템 명령어 실행 및 파이프라인 제어를 위한 리눅스 내장 모듈 임포트
import subprocess

# 슬랙 웹훅 URL을 변수에 저장한다. (반드시 본인이 발급받은 실제 주소로 변경해야 한다)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/본인의/웹훅/주소/전체"

# 슬랙으로 메시지를 전송하는 사용자 정의 함수를 선언한다.
def send_slack_alert(message):
    # 슬랙 서버가 이해할 수 있도록 JSON 형태로 데이터 구조를 만든다.
    payload = {"text": message}
    # try 구문을 사용하여 외부 통신 중 발생할 수 있는 오류를 안전하게 처리한다.
    try:
        # requests 모듈을 사용하여 슬랙 URL로 POST 방식의 HTTP 요청을 보낸다.
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        # 서버 응답 코드가 200번대(성공)가 아닐 경우 에러를 발생시킨다.
        response.raise_for_status()
    # 통신 실패 시 발생하는 예외를 e 변수에 담는다.
    except requests.exceptions.RequestException as e:
        # 에러 발생 시 관제 프로그램이 종료되지 않도록 터미널 화면에 원인만 출력한다.
        print(f"[경보 전송 실패] 원인: {e}")

# 프로그램이 시작되었음을 작업자 터미널에 알리는 메시지 출력
print("ASAv 장비 보호(To-the-box) 실시간 슬랙 알림 모니터링 시작... (종료: Ctrl+C)")

# tail 명령어로 우분투에 분리 적재된 asav.log 파일의 끝부분만 실시간 추적 시작
process = subprocess.Popen(['tail', '-F', '/var/log/asav.log'], stdout=subprocess.PIPE, text=True)

# 파이프를 통해 들어오는 터미널 출력 데이터를 한 줄씩 무한 반복하며 읽어들임
for line in process.stdout:
    
    # 방화벽 장비 자체를 향한 스캔(To-the-box) 차단 로그 식별 (레벨 3)
    if "%ASA-3-313" in line:
        
        # 로그의 줄바꿈 문자를 제거하여 깔끔한 문자열로 만든다.
        clean_line = line.strip()
        
        # 터미널 화면 출력 및 슬랙 전송을 위해 라벨을 붙인 최종 메시지 문자열을 구성한다.
        alert_message = f"[ASAv 자체 방어] {clean_line}"
        
        # 구성된 메시지를 관제 터미널 화면에 먼저 출력한다.
        print(alert_message)
        
        # 방금 만든 슬랙 전송 함수를 호출하여 스마트폰과 PC 슬랙 채널로 경보를 보낸다.
        send_slack_alert(alert_message)
