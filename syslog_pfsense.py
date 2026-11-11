# 시스템 명령어 실행 및 파이프라인 제어를 위한 내장 모듈 임포트
import subprocess

# 프로그램이 시작되었음을 터미널에 알리는 메시지 출력
print("pfSense 방화벽 상세 로그 모니터링을 시작한다... (종료: Ctrl+C)")

# tail -F 명령어를 사용하여 /var/log/syslog 파일의 끝부분을 실시간으로 추적 시작
process = subprocess.Popen(['tail', '-F', '/var/log/syslog'], stdout=subprocess.PIPE, text=True)

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

                # 프로토콜이 TCP 이거나 UDP 인 경우의 데이터 구조 처리
                if protocol == "tcp" or protocol == "udp":
                    # 21번째 필드를 출발지 포트로, 22번째 필드를 목적지 포트로 추출
                    src_port = fields[20]
                    dst_port = fields[21]
                    # 포트 번호를 포함하여 관제 요원이 읽기 쉬운 형태로 화면에 출력
                    print(f"[탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
                
                # 프로토콜이 ICMP 인 경우의 데이터 구조 처리 (포트 번호가 없음)
                elif protocol == "icmp":
                    # 21번째 필드를 ICMP 통신 유형(예: request, reply)으로 추출
                    icmp_type = fields[20]
                    # 포트 대신 ICMP 유형을 괄호에 넣어 직관적으로 화면에 출력
                    print(f"[탐지] IF:{interface} | 처리:{action} | 통신:{protocol} | {src_ip} -> {dst_ip} (유형:{icmp_type})")
