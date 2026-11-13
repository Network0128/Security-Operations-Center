# 외부 서버(슬랙)로 HTTP 요청을 보내기 위한 통신 모듈을 가져온다.
import requests
# 리눅스 시스템 명령어(tail)를 실행하고 파이프를 제어하기 위한 모듈을 가져온다.
import subprocess
# 현재 서버 시간을 추출하고 형식을 지정하기 위해 datetime 모듈을 가져온다.
from datetime import datetime

# 본인이 발급받은 슬랙 웹훅 URL 전체 주소를 변수에 할당한다. (수정 필수)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/여기에/본인의/웹훅/주소"

# 알림 메시지를 슬랙으로 전송하는 사용자 정의 함수를 선언한다.
def send_slack_alert(message):
    # 전송할 텍스트 데이터를 슬랙 서버가 인식할 수 있는 JSON 사전 형태로 구성한다.
    payload = {"text": message}
    # 외부 네트워크 통신 과정에서 발생할 수 있는 장애를 대비해 try 구문을 사용한다.
    try:
        # POST 방식을 사용하여 슬랙 서버 목적지로 JSON 데이터를 쏘아 보낸다.
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        # 통신 결과 코드가 정상(200번대)이 아닐 경우 강제로 예외를 발생시킨다.
        response.raise_for_status()
    # 통신 예외가 발생했을 경우 멈추지 않고 except 구문으로 진입한다.
    except requests.exceptions.RequestException as e:
        # 관제 프로그램이 종료되지 않도록 터미널에 실패 원인만 짧게 출력한다.
        print(f"[경보 전송 실패] 원인: {e}")

# 프로그램 시작을 훈련생들이 인지할 수 있도록 터미널에 안내 메시지를 띄운다.
print("ASAv 장비 슬랙 연동 모니터링(시간 정규화 적용) 시작... (종료: Ctrl+C)")

# tail 명령어의 -F 옵션을 사용하여 asav.log 파일의 꼬리 부분을 실시간으로 추적한다.
process = subprocess.Popen(['tail', '-F', '/var/log/asav.log'], stdout=subprocess.PIPE, text=True)

# 파이프라인을 통해 새롭게 유입되는 로그 텍스트를 한 줄씩 무한 반복하며 읽는다.
for line in process.stdout:
    # 방화벽 장비 자기 자신을 향한 공격(To-the-box)을 뜻하는 고유 식별자를 찾는다.
    if "%ASA-3-313" in line:
        # 현재 시간을 연-월-일 시:분:초 형태의 깔끔한 문자열로 가공한다.
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 원본 로그 문자열을 %ASA 기준으로 쪼갠 뒤, 앞의 지저분한 시간을 버리고 핵심만 취한다.
        core_log = "%ASA" + line.split("%ASA")[1].strip()
        # 서버 시간, 장비 라벨, 가공된 핵심 로그를 묶어 최종 슬랙 알림 메시지를 조립한다.
        alert_message = f"[{current_time}] [ASAv 자체 방어] {core_log}"
        # 조립이 완료된 메시지를 먼저 우분투 관제 터미널 화면에 출력한다.
        print(alert_message)
        # 작성해둔 슬랙 전송 함수를 호출하여 스마트폰과 PC 메신저로 경보를 전달한다.
        send_slack_alert(alert_message)
