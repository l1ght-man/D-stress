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
    
def attack_command(args):
    """main attack command handler"""

    if args.profile:
        profile =  load_profile(args.profile)
        if profile:
            print(f"[*] Loaded profile: {profile['name']}")
            args.type = profile.get('attack_type', args.type)

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
    env['TARGET_URL'] = args.target
    env['PAYLOAD_SIZE_KB'] = str(args.payload_size) 
    
    
    if args.stats:
        env['STATS_ENABLED'] = 'true'
        
    if args.save:
        env['STATS_SAVE'] = 'true'
        
    print(f"[*] Starting Docker containers...")
    print(f"    Press Ctrl+C to stop the attack")
    print()

    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n[*] Stopping attack...")
        subprocess.run([
            'docker-compose','-f', docker_compose_file , 'down'
        ], cwd=project_root)
    except subprocess.CalledProcessError as e :
        print(f"[!] Docker error: {e}")
        sys.exit(1)
    print("\n[*] Attack stopped. Cleaning up...")
    subprocess.run([
        'docker-compose','-f', docker_compose_file, 'down'
    ], cwd=project_root)