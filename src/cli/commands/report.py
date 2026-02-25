#!/usr/bin/env python3
"""
Report command - generates attack reports
"""

import json
import csv
import sys
import os
import requests
from datetime import datetime
import glob

def fetch_metrics(target_url='http://localhost:80'):
    """Fetch metrics from target server"""
    try:
        response =  requests.get(f"{target_url}/metrics" , timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None
    
def read_attacker_logs():
    """Read attacker stats from log files"""

    log_dir =  os.path.join(os.path.dirname(__file__), '..','..','..','logs')
    attacker_files = glob.glob(os.path.join(log_dir, 'attacker_*.json'))
    
    all_stats = []

    for filepath in attacker_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                all_stats.append(data)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return all_stats


def report_command(args):
    """generate attack report""" 

    metrics = fetch_metrics()
    
    if metrics:
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'active',
            'source': 'target_server',
            'total_requests': metrics.get('total_requests', 0),
            'total_errors': metrics.get('total_errors', 0),
            'active_attackers': metrics.get('active_attackers', 0),
            'uptime_seconds': metrics.get('uptime_seconds', 0),
            'cpu_percent': metrics.get('cpu_percent', 0)
        }
    else:
        attacker_stats = read_attacker_logs()

        if attacker_stats:
            total_requests = sum(s.get('requests_sent',0) for s in attacker_stats)
            total_errors = sum(s.get('errors',0) for s in attacker_stats)
            report_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'source':'attacker_logs',
            'total_requests':total_requests,
            'total_errors':total_errors,
            'attackers_count': len(attacker_stats),
            'details':attacker_stats,
            }
        else:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'status': 'no_data',
                'message': 'No attack metrics available. Start an attack with --stats --save first.',
                'hint': 'Usage: d-stress attack http://target --stats --save',
                 }
    if args.format == 'csv' :
        if report_data['status'] in ['active',"completed"]:
            output ="timestamp,status,total_requests,total_errors\n"
            output += f"{report_data['timestamp']},{report_data['status']},{report_data['total_requests']},{report_data['total_errors']}"
        else:
            output = "timestamp,status,message\n"
            output += f"{report_data['timestamp']},{report_data['status']},{report_data['message']}"
    elif args.format == 'json':
        output = json.dumps(report_data, indent=2)
    else:  # text
        output = f"""
+{'='*60}+
|  D-stress Attack Report
+{'='*60}+
|  Timestamp: {report_data['timestamp']}
|  Status: {report_data['status']}
|  Source: {report_data.get('source', 'N/A')}
"""
        if report_data['status'] in ['active', 'completed']:
            output += f"""|  Total Requests: {report_data['total_requests']:,}
|  Total Errors: {report_data['total_errors']:,}
"""
            if 'active_attackers' in report_data:
                output += f"|  Active Attackers: {report_data['active_attackers']}\n"
            if 'cpu_percent' in report_data:
                output += f"|  Target CPU: {report_data['cpu_percent']:.1f}%\n"
            if 'attackers_count' in report_data:
                output += f"|  Attackers Count: {report_data['attackers_count']}\n"
        else:
            output += f"|  Message: {report_data['message']}\n"
        output += f"+{'='*60}+\n"

    # output to file or stdout
    if args.output:
        with open(args.output, 'w' , encoding='utf-8') as f:
            f.write(output)
        print(f"[*] Report saved to: {args.output}")
    else:
        print(output)
       
       