#!/usr/bin/env python3
"""
status command - shows running containers and metrics
"""

import subprocess
import json
import sys

def status_command(args):
    """show system status"""

    if args.live:
        print("[*] Live dashboard - Press Ctrl+C to exit")
        print("(Full implementation coming with rich library)")
        print()

        try:
            subprocess.run([
                'docker-compose', 'logs' , '-f', '--tail=10'
            ])
        except KeyboardInterrupt:
            print("\n[*] Exiting live view")

        return
    
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0  and result.stdout.strip():
            containers = json.loads(result.stdout) if result.stdout.strip() else []
            print("[*] Running Containers:")
            print("-" *50 )
            for container in containers:
                name = container.get('Name', 'unknown')
                state = container.get('State','unknown')
                print(f"{name}: {state}")
            print("-"*50)
            print(f"Total : {len(containers)}")

        else:
            print(f"[!] No containers running")
            print(f"Run : d-stress attack http://localhost:80")

    except Exception as e:
        print(f"[!] Error getting status: {e}")
        
            
        