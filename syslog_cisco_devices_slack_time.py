# HTTP 웹 통신을 수행하기 위해 사전에 설치된 requests 라이브러리를 불러온다.
import requests
# 우분투 운영체제의 쉘 명령어를 파이썬 내부에서 실행하기 위한 모듈을 불러온다.
import subprocess
# 타임스탬프 정규화를 위해 파이썬 내장 날짜시간 처리 모듈을 불러온다.
from datetime import datetime

# 슬랙 워크스페이스에서 발급받은 전용 웹훅 주소를 문자열 변수로 지정한다.
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/여기에/본인의/웹훅/주소"

# 탐지된 위협 텍스트를 매개변수로 받아 슬랙 채널에 게시하는 함수를 정의한다.
def send_slack_alert(message):
    # 슬랙 API 스펙에 맞추어 전송할 데이터를 딕셔너리 구조로 포장한다.
    payload = {"text": message}
    # 네트워크 단절 등으로 인한 스크립트 중단을 막기 위해 예외 처리 구문을 시작한다.
    try:
        # 타겟 URL을 향해 구성된 JSON 페이로드를 POST 메서드로 전송한다.
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        # 전송 성공 여부를 검증하고 실패 시 예외 처리 블록으로 넘긴다.
        response.raise_for_status()
    # requests 통신 도중 발생한 모든 에러를 e 변수에 담아 잡는다.
    except requests.exceptions.RequestException as e:
        # 에러 내용을 터미널에만 표시하고 다음 로그 모니터링을 계속 진행한다.
        print(f"[경보 전송 실패] 원인: {e}")

# 백그라운드 모니터링이 가동되었음을 알리는 메시지를 화면에 뿌려준다.
print("Cisco IOS 장비 슬랙 연동 모니터링(시간 정규화 적용) 시작... (종료: Ctrl+C)")

# 분리 수집된 cisco_devices.log 파일의 실시간 업데이트 내역을 tail로 낚아챈다.
process = subprocess.Popen(['tail', '-F', '/var/log/cisco_devices.log'], stdout=subprocess.PIPE, text=True)

# 버퍼를 통해 실시간으로 들어오는 터미널 출력값을 한 줄씩 순환하며 검사한다.
for line in process.stdout:
    # 라우터 인터페이스에 적용된 ACL 통과 거부(deny) 메시지가 포함되어 있는지 확인한다.
    if "%SEC-6-IPACCESSLOG" in line:
        # 알림 발생 시점의 정확한 서버 시간을 읽어와 가독성 높은 포맷으로 변환한다.
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 원시 로그에 섞인 라우터 자체 시간과 Syslog 수신 시간을 모두 날려버린다.
        core_log = "%SEC" + line.split("%SEC")[1].strip()
        # 정규화된 현재 시간 및 IOS 전용 라벨을 붙여 깔끔한 경보 텍스트를 생성한다.
        alert_message = f"[{current_time}] [IOS 라우터 방어] {core_log}"
        # 즉각적인 시각적 관제를 위해 터미널 표준 출력으로 경보를 표시한다.
        print(alert_message)
        # 슬랙 연동 함수에 최종 텍스트를 던져 실무자 알림을 발생시킨다.
        send_slack_alert(alert_message)
