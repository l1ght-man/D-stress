#!/usr/bin/env python3
"""
status command - shows running containers and metrics
"""

import subprocess
import json
import sys
import os
import time
import psutil
import re

def status_command(args):
    """show system status"""

    if args.live:
        print("[*] Live dashboard - Press Ctrl+C to exit")
        print()

        # Get project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        docker_compose_file = os.path.join(project_root, 'docker-compose.yml')
        
        # Read state file to get actual target URL and attack type from attack command
        state_file = os.path.join(project_root, '.d-stress-state.json')
        saved_target = None
        saved_attack_type = 'get_flood'  # default
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
                saved_target = state.get('target_url')
                saved_attack_type = state.get('attack_type', 'get_flood')
        except:
            pass

        # Check if local target container is running
        try:
            result = subprocess.run(
                ['docker-compose', '-f', docker_compose_file, 'ps'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output = result.stdout
            # Check if target container is in the output and running
            has_local_target = 'target' in output and ('running' in output.lower() or 'Up' in output)
        except Exception:
            has_local_target = False

        # Use saved target URL or environment default
        target_url = saved_target or os.getenv('TARGET_URL', 'http://localhost:80')
        
        # Use saved attack type or environment default
        attack_type = saved_attack_type or os.getenv('ATTACK_TYPE', 'get_flood')
        
        # Detect if this is a distributed attack (attacking remote, no local target needed)
        is_distributed = saved_target and not any(x in saved_target for x in ['localhost', '127.0.0.1', 'http://target'])

        # Track attack start time for uptime calculation
        attack_start_time = time.time()

        try:
            while True:
                # Re-read state file each iteration to detect new attacks
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        saved_target = state.get('target_url')
                        saved_attack_type = state.get('attack_type', 'get_flood')
                except:
                    pass
                
                # Update attack type from state
                attack_type = saved_attack_type or os.getenv('ATTACK_TYPE', 'get_flood')
                target_url = saved_target or os.getenv('TARGET_URL', 'http://localhost:80')
                is_distributed = saved_target and not any(x in saved_target for x in ['localhost', '127.0.0.1', 'http://target'])

                # Count attacker containers
                try:
                    result = subprocess.run(
                        ['docker-compose', '-f', docker_compose_file, 'ps', '-q'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    container_ids = [c for c in result.stdout.strip().split('\n') if c]
                    active_attackers = len(container_ids)
                except Exception:
                    active_attackers = 0

                if is_distributed:
                    # Distributed attack - show local stats
                    local_cpu = psutil.cpu_percent(interval=1)
                    mem = psutil.virtual_memory()
                    uptime = int(time.time() - attack_start_time)

                    # Get stats from attacker logs based on attack type
                    total_requests = 0
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
                            for i, line in enumerate(log_output.split('\n')):
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
                                    if '[Slowloris] STATS:' in line:
                                        try:
                                            match = re.search(r'(\d+)\s*held', line)
                                            if match:
                                                total_requests += int(match.group(1))
                                        except:
                                            pass
                                        break
                                else:
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
                    # Local attack - fetch from target
                    try:
                        import requests as req
                        response = req.get(f"{target_url}/metrics", timeout=2)
                        if response.status_code == 200:
                            metrics = response.json()
                            total_requests = metrics.get('total_requests', 0)
                            cpu = metrics.get('cpu_percent', 0)
                            uptime = metrics.get('uptime_seconds', 0)
                        else:
                            total_requests = 0
                            cpu = 0
                            uptime = 0
                    except Exception:
                        total_requests = 0
                        cpu = 0
                        uptime = 0

                    dashboard = f"""
+{'='*60}+
|  D-stress Live Dashboard
+{'='*60}+
|  Total Requests: {total_requests:,}
|  Active Attackers: {active_attackers}
|  Target CPU: {cpu:.1f}%
|  Uptime: {uptime:.0f}s
+{'='*60}+
|  Press Ctrl+C to exit
+{'='*60}+"""

                # Clear screen and move cursor to top
                print('\033[2J\033[H', end='')
                print(dashboard)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Exiting live view")

        return

    # Get project root directory (same as attack.py)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    docker_compose_file = os.path.join(project_root, 'docker-compose.yml')

    try:
        # Use stderr=STDOUT to capture warnings + output together
        result = subprocess.run(
            ['docker-compose', '-f', docker_compose_file, 'ps', '--format', 'json'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            # docker-compose outputs JSON lines (one per container), not array
            # Filter out non-JSON lines (warnings, etc.)
            containers = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line.startswith('{'):  # Only parse JSON lines
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            if containers:
                print("[*] Running Containers:")
                print("-" * 50)
                for container in containers:
                    name = container.get('Name', 'unknown')
                    state = container.get('State', 'unknown')
                    print(f"  {name}: {state}")
                print("-" * 50)
                print(f"  Total: {len(containers)} container(s)")
            else:
                print("[!] No containers running")
                print("  Run: d-stress attack http://localhost:80")
        else:
            print("[!] No containers running")
            print("  Run: d-stress attack http://localhost:80")

    except Exception as e:
        print(f"[!] Error getting status: {e}")
        
            
        