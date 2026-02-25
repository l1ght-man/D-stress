#!/usr/bin/env python3
"""
D-stress CLI - Main entry point
Usage: d-stress <command> [options]
"""

import argparse
import sys
import os

from .commands.attack import attack_command
from .commands.status import status_command
from .commands.report import report_command

def main():

    parser = argparse.ArgumentParser(
        prog='d-stress',
        description='DDos Simulation & Educational Tool'
    )

    subparser = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )

    attack_parser = subparser.add_parser('attack',help='Start attack simulation')
    attack_parser.add_argument('target',help='Target URL (e.g., http://localhost:80)')
    attack_parser.add_argument('--type' ,'-t', 
                               choices=['get_flood', 'post_flood','slowloris','syn_flood','udp_flood','dns_amplification'],
                               default='get_flood',
                               help='Attack type')
    attack_parser.add_argument('--attacker' , '-a',
                                type=int,
                                default=5,
                                help='Number of attacker containers'
                                )
    attack_parser.add_argument('--payload-size' ,
                                type=int,
                                default=10,
                                help='Payload size in KB (for POST attacks)'
                                )
    attack_parser.add_argument('--profile','-p',
                               choices=['light','medium','heavy'],
                               help='Use predefined attack profile')
    attack_parser.add_argument('--allow-public',action='store_true',
                               help='Allow attacking public IPs(NOT RECOMMENDED)')
    attack_parser.add_argument('--duration', '-d',
                               type=int,
                               default=0,
                               help='Attack duration in seconds (0 = infinite )')
    attack_parser.add_argument('--stats', '-s', 
                               action='store_true',
                               help='Show live attack statistics')
    attack_parser.add_argument('--save',
                               action='store_true',
                               help='Save stats to log files for later reports')
    attack_parser.set_defaults(func=attack_command)

    status_parser = subparser.add_parser('status', help='Show system status')

    status_parser.add_argument('--live', '-l', action='store_true', help='Show live updating dashboard')
    status_parser.set_defaults(func=status_command)

    # report command
    report_parser = subparser.add_parser('report', help='Generate attack report')

    report_parser.add_argument('--format', '-f',
                               choices=['json','csv','text'],
                               default='text',
                               help='Output format')
    report_parser.add_argument('--output', '-o',
                               help='Output file path')
    report_parser.set_defaults(func=report_command)

    
    args = parser.parse_args()

    # show help command
    if not args.command:
        parser.print_help()
        sys.exit(1)
    # run the command
    args.func(args)

if __name__ == '__main__':
    main()