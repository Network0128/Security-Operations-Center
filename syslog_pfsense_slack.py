# HTTP 외부 통신을 위해 사전에 설치한 requests 라이브러리를 임포트한다.
import requests
# 시스템 명령어 실행 및 파이프라인 제어를 위한 리눅스 내장 모듈 임포트
import subprocess

# 발급받은 슬랙 웹훅 URL 주소를 변수에 저장한다. (본인의 실제 주소로 변경 필수)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/여기에/본인의/웹훅/주소"

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

# 프로그램이 시작되었음을 터미널에 알리는 메시지 출력
print("pfSense 방화벽 통합 로그 및 슬랙 모니터링을 시작한다... (종료: Ctrl+C)")

# tail 명령어를 사용하여 분리 저장된 pfsense.log 파일의 실시간 추적 시작
process = subprocess.Popen(['tail', '-F', '/var/log/pfsense.log'], stdout=subprocess.PIPE, text=True)

# 파이프를 통해 들어오는 터미널 출력 데이터를 한 줄씩 무한 반복하며 읽어들임
for line in process.stdout:
    
    # 해당 문자열 라인에 방화벽 정책 처리 데몬인 'filterlog' 단어가 포함되어 있는지 확인
    if "filterlog" in line:
        
        # 문자열 양끝의 공백을 제거하고, 쉼표(,)를 기준으로 잘라 리스트(배열) 생성
        fields = line.strip().split(',')
        
        # 리스트의 길이가 최소 20개 이상인지 확인하여 불완전한 로그 에러 방지
        if len(fields) > 20:
            
            # 파이썬 리스트 인덱스를 활용하여 인터페이스, 처리 결과, IP 버전을 추출
            interface = fields[4]
            action = fields[6]
            ip_version = fields[8]

            # IPv4 통신 로그일 경우에만 상세 추출 로직 수행
            if ip_version == "4":
                
                # 17번째 필드인 L4 프로토콜 이름과 출발지, 목적지 IP 추출
                protocol = fields[16]
                src_ip = fields[18]
                dst_ip = fields[19]

                # 출력할 최종 메시지를 담을 빈 문자열 변수를 초기화한다.
                alert_message = ""

                # 프로토콜이 TCP 이거나 UDP 인 경우의 데이터 구조 처리
                if protocol == "tcp" or protocol == "udp":
                    # 21번째 필드를 출발지 포트로, 22번째 필드를 목적지 포트로 추출
                    src_port = fields[20]
                    dst_port = fields[21]
                    # 포트 번호를 포함하여 관제 요원이 읽기 쉬운 라벨 형태로 문자열 생성
                    alert_message = f"[pfSense 탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip}:{src_port} -> {dst_ip}:{dst_port}"
                
                # 프로토콜이 ICMP 인 경우의 데이터 구조 처리 (포트 번호가 없음)
                elif protocol == "icmp":
                    # 21번째 필드를 ICMP 통신 유형(예: request, reply)으로 추출
                    icmp_type = fields[20]
                    # 포트 대신 ICMP 유형을 괄호에 넣어 직관적인 라벨 형태의 문자열 생성
                    alert_message = f"[pfSense 탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip} -> {dst_ip} (유형:{icmp_type})"

                # 알림 메시지 문자열이 정상적으로 생성되었는지 확인한다.
                if alert_message:
                    # 모든 트래픽(허용/차단) 내역을 관제 터미널 화면에 실시간으로 출력한다.
                    print(alert_message)
                    
                    # 실무 적용 포인트: 트래픽 처리 결과가 '차단(block)'인 경우에만 한정한다.
                    if action == "block":
                        # 조건이 만족되면 웹훅 전송 함수를 호출하여 스마트폰으로 경보를 발송한다.
                        send_slack_alert(alert_message)
