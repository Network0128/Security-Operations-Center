# 슬랙 서버로 알림 데이터를 밀어 넣기 위한 외부 통신 패키지를 임포트한다.
import requests
# 시스템 프로세스인 tail 명령을 구동하기 위해 서브프로세스 패키지를 임포트한다.
import subprocess
# 모든 장비의 알림 시간을 하나로 통일시키기 위해 datetime 패키지를 임포트한다.
from datetime import datetime

# 슬랙 웹훅 URL을 변수에 선언한다. (반드시 본인의 주소로 변경하여 저장해야 한다)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/여기에/본인의/웹훅/주소"

# 특정 이벤트가 탐지되었을 때 호출할 메신저 알림 전송 함수를 구성한다.
def send_slack_alert(message):
    # 텍스트 메시지를 슬랙이 요구하는 JSON 키-값 쌍 형태로 묶어준다.
    payload = {"text": message}
    # 외부 통신 딜레이나 장애에 대비해 스크립트를 보호하는 try 문을 연다.
    try:
        # 지정된 슬랙 주소로 메시지가 담긴 페이로드를 POST 요청으로 쏜다.
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        # 서버에서 200번대 성공 코드를 주지 않으면 에러 처리 루틴으로 던진다.
        response.raise_for_status()
    # HTTP 통신 간 발생한 예외 상황을 캐치한다.
    except requests.exceptions.RequestException as e:
        # 스크립트 작동을 유지하면서 에러 원인만 작업자에게 슬쩍 보여준다.
        print(f"[경보 전송 실패] 원인: {e}")

# 작업자에게 스크립트가 정상 루프에 진입했음을 알리는 시작 문구를 출력한다.
print("pfSense 방화벽 슬랙 연동 모니터링(시간 정규화 적용) 시작... (종료: Ctrl+C)")

# 분리 적재 설정으로 만들어진 pfsense.log 파일의 실시간 변경을 스트리밍한다.
process = subprocess.Popen(['tail', '-F', '/var/log/pfsense.log'], stdout=subprocess.PIPE, text=True)

# 텍스트 스트림으로 유입되는 방화벽 원본 로그를 라인 단위로 계속 읽어들인다.
for line in process.stdout:
    # pfSense의 트래픽 필터링 데몬인 filterlog 문자열이 존재하는지 검증한다.
    if "filterlog" in line:
        # 알림 메시지 맨 앞에 붙여줄 우분투 서버 기준의 현재 시간을 찍어둔다.
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 쉼표(,)를 구분자로 사용하여 긴 로그 라인을 여러 개의 필드 리스트로 나눈다.
        fields = line.strip().split(',')
        
        # 리스트 쪼개기 중 발생할 수 있는 인덱스 에러를 막기 위해 길이를 체크한다.
        if len(fields) > 20:
            # 인터페이스 이름, 허용/차단 여부, IP 프로토콜 버전 필드를 변수에 담는다.
            interface = fields[4]
            action = fields[6]
            ip_version = fields[8]

            # 구조가 복잡한 IPv6를 제외하고 IPv4 패킷에 대해서만 처리를 진행한다.
            if ip_version == "4":
                # L4 프로토콜 종류, 출발지 IP 주소, 목적지 IP 주소를 각각 추출한다.
                protocol = fields[16]
                src_ip = fields[18]
                dst_ip = fields[19]

                # 최종 조립될 알림 메시지를 임시로 담아둘 빈 문자열을 초기화한다.
                alert_message = ""

                # 추출된 프로토콜이 포트 번호를 가지는 TCP 또는 UDP인지 확인한다.
                if protocol == "tcp" or protocol == "udp":
                    # 출발지와 목적지의 통신 포트 번호를 변수로 가져온다.
                    src_port = fields[20]
                    dst_port = fields[21]
                    # 생성해둔 현재 시간 변수를 맨 앞에 배치하여 직관적인 알림 포맷을 만든다.
                    alert_message = f"[{current_time}] [pfSense 탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip}:{src_port} -> {dst_ip}:{dst_port}"
                
                # 프로토콜이 포트 개념이 없는 ICMP(Ping 등)인지 분기하여 확인한다.
                elif protocol == "icmp":
                    # 포트 대신 위치한 ICMP 메시지 유형(request 등)을 추출한다.
                    icmp_type = fields[20]
                    # 현재 시간을 포함하여 ICMP 전용 양식에 맞춘 알림 문자열을 생성한다.
                    alert_message = f"[{current_time}] [pfSense 탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip} -> {dst_ip} (유형:{icmp_type})"

                # 조건문을 거쳐 알림 메시지가 성공적으로 포장되었는지 검사한다.
                if alert_message:
                    # 허용(pass)과 차단(block)을 포함한 모든 로그를 일단 터미널에 찍는다.
                    print(alert_message)
                    
                    # 관제 효율을 위해 방화벽 정책에 의해 차단(block)된 로그만 골라낸다.
                    if action == "block":
                        # 선별된 위험 로그만 슬랙 웹훅 함수를 통해 외부로 전송한다.
                        send_slack_alert(alert_message)
