#!/usr/bin/env python3
"""
status command - shows running containers and metrics
"""

import subprocess
import json
import sys
import os
import time

def status_command(args):
    """show system status"""

    if args.live:
        print("[*] Live dashboard - Press Ctrl+C to exit")
        print()

        # Get project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        docker_compose_file = os.path.join(project_root, 'docker-compose.yml')

        # Try to fetch metrics from target
        target_url = os.getenv('TARGET_URL', 'http://localhost:80')
        
        last_display = ""
        
        try:
            while True:
                # Fetch metrics from target
                try:
                    import requests as req
                    response = req.get(f"{target_url}/metrics", timeout=2)
                    if response.status_code == 200:
                        metrics = response.json()
                        
                        # Build dashboard
                        total_requests = metrics.get('total_requests', 0)
                        active_attackers = metrics.get('active_attackers', 0)
                        uptime = metrics.get('uptime_seconds', 0)
                        cpu = metrics.get('cpu_percent', 0)
                        
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
                    else:
                        print("[!] Could not fetch metrics from target")
                        time.sleep(2)
                except Exception:
                    print("[!] Waiting for target...")
                    time.sleep(2)
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
        
            
        