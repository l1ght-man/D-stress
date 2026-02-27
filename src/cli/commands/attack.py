#!/usr/bin/env python3
"""
Attack command - validates target and starts Docker containers
"""

import os
import sys
import subprocess
import time
import json
import socket
import threading
import re
from urllib.parse import urlparse


def is_private_ip(hostname):
    """checks if IP is private"""
    try:
        ip = socket.gethostbyname(hostname)
        octets =  ip.split('.')
        if octets[0] == '10':
            return True
        if octets[0] == '192' and octets[1] == '168':
            return True
        if octets[0] == '172' and 16 <= int(octets[1]) <= 31:
            return True
        if ip == '127.0.0.1' or hostname ==  'localhost':
            return True
        return False
    except socket.gaierror :
        return False
    

def load_profile(profile_name):
    """Load attack profile from JSONs"""
    profile_dir  = os.path.join(os.path.dirname(__file__),'..','profiles')
    profile_path =  os.path.join(profile_dir , f'{profile_name}.json')

    try:
        with open(profile_path , 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[!] Profile not found : {profile_name}")
        return None


def is_distributed_attack(target_url):
    """Check if target is remote (distributed attack)"""
    return not any(x in target_url for x in ['localhost', '127.0.0.1', 'http://target'])


def show_attack_stats(docker_compose_file, target_url, stop_event, attack_type='get_flood'):
    """Show live stats during attack"""
    import psutil

    is_distributed = is_distributed_attack(target_url)
    start_time = time.time()
    last_total = 0

    while not stop_event.is_set():
        try:
            # Count attacker containers
            result = subprocess.run(
                ['docker-compose', '-f', docker_compose_file, 'ps', '-q'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            container_ids = [c for c in result.stdout.strip().split('\n') if c]
            active_attackers = len(container_ids)

            # Get stats from attacker logs based on attack type
            total_requests = 0
            extra_stats = {}  # For attack-type-specific metrics
            
            for container_id in container_ids:
                try:
                    log_result = subprocess.run(
                        ['docker', 'logs', container_id],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=2
                    )
                    log_output = log_result.stdout + log_result.stderr

                    # Parse based on attack type
                    for line in log_output.split('\n'):
                        if attack_type in ['syn_flood', 'udp_flood']:
                            # Look for packet-based attack stats (may be multi-line)
                            if 'packets' in line.lower():
                                try:
                                    match = re.search(r'([\d,]+)\s*packets', line)
                                    if match:
                                        pkt_count = int(match.group(1).replace(',', ''))
                                        total_requests += pkt_count
                                except:
                                    pass
                                break
                        elif attack_type == 'slowloris':
                            # Parse Slowloris stats
                            if '[Slowloris] STATS:' in line:
                                try:
                                    held_match = re.search(r'(\d+)\s*held', line)
                                    if held_match:
                                        total_requests += int(held_match.group(1))
                                        extra_stats['connections'] = int(held_match.group(1))
                                except:
                                    pass
                                break
                        else:
                            # Parse HTTP flood (requests)
                            if '[STATS]' in line and 'requests' in line:
                                try:
                                    match = re.search(r'\[STATS\]\s+(\d+)\s+requests', line)
                                    if match:
                                        req_count = int(match.group(1))
                                        total_requests += req_count
                                except:
                                    pass
                                break
                except:
                    pass

            # Keep last known value if parsing fails
            if total_requests == 0 and last_total > 0:
                total_requests = last_total
            last_total = max(total_requests, last_total)

            # Local machine stats
            local_cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            uptime = int(time.time() - start_time)

            if is_distributed:
                # Build attack-type-specific dashboard
                if attack_type in ['syn_flood', 'udp_flood']:
                    dashboard = f"""
+{'='*60}+
|  D-stress Live Dashboard (Distributed Mode)
+{'='*60}+
|  Attack Type: {attack_type.replace('_', ' ').upper()}
|  Active Attackers: {active_attackers}
|  Total Packets: {total_requests:,}
|  Local CPU: {local_cpu:.1f}%
|  Local Memory: {mem.percent:.1f}%
|  Uptime: {uptime}s
|  Target: {target_url}
+{'='*60}+
|  Press Ctrl+C to exit
+{'='*60}+"""
                elif attack_type == 'slowloris':
                    dashboard = f"""
+{'='*60}+
|  D-stress Live Dashboard (Distributed Mode)
+{'='*60}+
|  Attack Type: {attack_type.upper()}
|  Active Attackers: {active_attackers}
|  Held Connections: {total_requests:,}
|  Local CPU: {local_cpu:.1f}%
|  Local Memory: {mem.percent:.1f}%
|  Uptime: {uptime}s
|  Target: {target_url}
+{'='*60}+
|  Press Ctrl+C to exit
+{'='*60}+"""
                else:
                    dashboard = f"""
+{'='*60}+
|  D-stress Live Dashboard (Distributed Mode)
+{'='*60}+
|  Attack Type: {attack_type.replace('_', ' ').upper()}
|  Active Attackers: {active_attackers}
|  Total Requests: {total_requests:,}
|  Local CPU: {local_cpu:.1f}%
|  Local Memory: {mem.percent:.1f}%
|  Uptime: {uptime}s
|  Target: {target_url}
+{'='*60}+
|  Press Ctrl+C to exit
+{'='*60}+"""
            else:
                # Try to fetch from target for local attacks
                try:
                    import requests as req
                    response = req.get(f"{target_url}/metrics", timeout=2)
                    if response.status_code == 200:
                        metrics = response.json()
                        total_requests = metrics.get('total_requests', 0)
                        target_cpu = metrics.get('cpu_percent', 0)
                        uptime = int(metrics.get('uptime_seconds', 0))
                    else:
                        total_requests = 0
                        target_cpu = 0
                except Exception:
                    total_requests = 0
                    target_cpu = 0
                
                dashboard = f"""
+{'='*60}+
|  D-stress Live Dashboard
+{'='*60}+
|  Total Requests: {total_requests:,}
|  Active Attackers: {active_attackers}
|  Target CPU: {target_cpu:.1f}%
|  Uptime: {uptime}s
+{'='*60}+
|  Press Ctrl+C to exit
+{'='*60}+"""
            
            print('\033[2J\033[H', end='')
            print(dashboard)
        except Exception:
            time.sleep(1)


def attack_command(args):
    """main attack command handler"""

    if args.profile:
        profile =  load_profile(args.profile)
        if profile:
            print(f"[*] Loaded profile: {profile['name']}")
            args.type = profile.get('attack_type', args.type)
            args.attacker = profile.get('attackers', args.attacker)

    # Parse target URL
    parsed = urlparse(args.target)
    if not parsed.scheme or not parsed.netloc:
        print(f"[!] Invalid URL: {args.target}")
        print("Use format: http://host:port")
        sys.exit(1)
    
    hostname = parsed.hostname

    if not args.allow_public and not is_private_ip(hostname):
        print(f"[!] SAFETY WARNING: Target appears to be a public IP!")
        print(f"    Resolved IP: {socket.gethostbyname(hostname)}")
        print(f"    D-stress is for EDUCATIONAL USE ONLY on systems you own.")
        print(f"    ")
        print(f"    To bypass this check (NOT RECOMMENDED), use --allow-public")
        sys.exit(1)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..'))
    docker_compose_file =  os.path.join(project_root, 'docker-compose.yml')
    print(f"[*] D-stress Attack Starting...")
    print(f"    Target: {args.target}")
    print(f"    Attack Type: {args.type}")
    print(f"    Attackers: {args.attacker}")
    print(f"    Duration: {'infinite' if args.duration == 0 else f'{args.duration}s'}")
    print()


    cmd = [
        'docker-compose',
        '-f' , docker_compose_file,
        'up',
        '--build',
        '--scale',f'attacker={args.attacker}',
        '--abort-on-container-exit'
    ]

    env = os.environ.copy()
    env['ATTACK_TYPE'] = args.type
    
    # For Docker containers, use internal Docker network name for local targets
    docker_target_url = args.target
    if 'localhost' in args.target or '127.0.0.1' in args.target:
        docker_target_url = args.target.replace('localhost', 'target').replace('127.0.0.1', 'target')
    env['TARGET_URL'] = docker_target_url
    
    env['PAYLOAD_SIZE_KB'] = str(args.payload_size)
    env['TARGET_ENDPOINT'] = parsed.path or '/api/data'

    # Save target URL and attack type for status command
    state_file = os.path.join(project_root, '.d-stress-state.json')
    try:
        with open(state_file, 'w') as f:
            json.dump({
                'target_url': args.target,
                'attack_type': args.type,
                'start_time': time.time()
            }, f)
    except:
        pass

    if args.stats:
        env['STATS_ENABLED'] = 'true'

    if args.save:
        env['STATS_SAVE'] = 'true'
        
    print(f"[*] Starting Docker containers...")
    print(f"    Press Ctrl+C to stop the attack")
    print()

    # Stats viewer for distributed attacks
    stats_thread = None
    stop_stats = threading.Event()
    
    if args.stats and is_distributed_attack(args.target):
        # Start stats viewer in separate thread
        stop_stats.clear()
        stats_thread = threading.Thread(
            target=show_attack_stats,
            args=(docker_compose_file, args.target, stop_stats, args.type),
            daemon=True
        )
        stats_thread.start()

    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n[*] Stopping attack...")
        stop_stats.set()
        if stats_thread:
            stats_thread.join(timeout=2)
        subprocess.run([
            'docker-compose','-f', docker_compose_file , 'down'
        ], cwd=project_root)
    except subprocess.CalledProcessError as e :
        print(f"[!] Docker error: {e}")
        stop_stats.set()
        sys.exit(1)
    
    stop_stats.set()
    print("\n[*] Attack stopped. Cleaning up...")
    subprocess.run([
        'docker-compose','-f', docker_compose_file, 'down'
    ], cwd=project_root)