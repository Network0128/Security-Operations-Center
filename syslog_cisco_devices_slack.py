# HTTP 통신을 위해 사전에 설치한 requests 라이브러리를 불러온다.
import requests
# 시스템 명령어 실행 및 파이프라인 제어를 위한 리눅스 내장 모듈을 불러온다.
import subprocess

# 발급받은 슬랙 웹훅 URL 주소를 변수에 저장한다. (본인의 실제 주소로 변경 필수)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/본인의/웹훅/주소/전체"

# 슬랙으로 알림 메시지를 전송하는 사용자 정의 함수를 만든다.
def send_slack_alert(message):
    # 슬랙 API가 인식할 수 있도록 텍스트 데이터를 JSON 딕셔너리 형태로 구성한다.
    payload = {"text": message}
    # 외부 네트워크 통신 시 발생할 수 있는 장애를 처리하기 위해 try 구문을 사용한다.
    try:
        # requests 모듈의 post 메서드를 사용하여 슬랙 서버로 JSON 데이터를 쏘아 보낸다.
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        # HTTP 응답 코드가 200번대(정상)가 아닐 경우 강제로 에러를 발생시킨다.
        response.raise_for_status()
    # 네트워크 단절 등으로 통신에 실패하면 예외 내용을 e 변수에 담는다.
    except requests.exceptions.RequestException as e:
        # 프로그램이 멈추지 않도록 터미널에 실패 원인만 간략히 출력하고 넘어간다.
        print(f"[경보 전송 실패] 원인: {e}")

# 프로그램이 백그라운드에서 정상적으로 시작되었음을 터미널에 알린다.
print("Cisco 라우터/스위치 ACL 차단 로그 슬랙 모니터링 시작... (종료: Ctrl+C)")

# tail 명령어를 통해 우분투 서버에 분리 저장된 cisco_devices.log 파일의 실시간 변경을 추적한다.
process = subprocess.Popen(['tail', '-F', '/var/log/cisco_devices.log'], stdout=subprocess.PIPE, text=True)

# 파이프라인을 통해 새롭게 추가되는 로그 데이터를 한 줄씩 무한 반복하며 읽어 들인다.
for line in process.stdout:
    
    # Cisco 장비의 명시적 ACL 정책 위반(차단)을 의미하는 고유 메시지 ID를 확인한다.
    if "%SEC-6-IPACCESSLOG" in line:
        
        # 원본 로그 문자열 양끝의 공백과 줄바꿈 문자를 깔끔하게 제거한다.
        clean_line = line.strip()
        
        # 슬랙과 터미널에 출력할 때 시각적으로 구분하기 쉽도록 라벨을 덧붙여 최종 문자열을 만든다.
        alert_message = f"[IOS 라우터 방어] {clean_line}"
        
        # 먼저 관제 모니터(터미널) 화면에 가공된 경보 메시지를 출력한다.
        print(alert_message)
        
        # 미리 정의해둔 슬랙 전송 함수를 호출하여 스마트폰으로 즉각적인 알림을 발송한다.
        send_slack_alert(alert_message)
