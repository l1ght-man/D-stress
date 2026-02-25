# D-stress

DDoS Simulation and Educational Tool for learning about distributed denial of service attacks in a safe, controlled environment.

## What This Is

D-stress is a learning tool that helps you understand how DDoS attacks work by simulating them against your own test servers. It runs multiple attacker containers that generate traffic against a target, letting you observe the effects and learn about different attack methods.

**This is for educational use only.** Only use this on systems you own or have explicit permission to test.

## Features

- Multiple attack types (HTTP flood, POST flood, Slowloris, SYN flood, UDP flood, DNS amplification)
- Docker-based orchestration with scalable attacker containers
- Real-time metrics and reporting
- Safety features that block attacks on public IPs by default
- Simple command-line interface

## Requirements

- [Docker](https://www.docker.com/products/docker-desktop/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/) (usually included with Python)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/d-stress.git
cd d-stress
```

2. Install the CLI tool:
```bash
pip install -e .
```

3. Verify installation:
```bash
d-stress --help
```

### Windows PATH Note

If the `d-stress` command is not found after installation, you may need to add Python Scripts to your PATH:

```cmd
setx PATH "%PATH%;C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\Scripts"
```

The exact path depends on your Python version and installation location. Close and reopen your terminal after adding to PATH.

## Quick Start

Start an attack against your local test server:

```bash
# Start a light attack with 5 attackers
d-stress attack http://localhost:80 --profile light

# Start a medium attack with 15 attackers
d-stress attack http://localhost:80 --profile medium

# Custom attack with specific settings
d-stress attack http://localhost:80 --type post_flood --attacker 10
```

## Commands

### attack

Start an attack simulation against a target.

```bash
d-stress attack <target_url> [options]
```

Options:
- `--type, -t` - Attack type (get_flood, post_flood, slowloris, syn_flood, udp_flood, dns_amplification)
- `--attacker, -a` - Number of attacker containers (default: 5)
- `--profile, -p` - Predefined profile (light, medium, heavy)
- `--payload-size` - Payload size in KB for POST attacks (default: 10)
- `--stats, -s` - Show live attack statistics
- `--save` - Save stats to log files for later reports
- `--allow-public` - Allow attacking public IPs (NOT RECOMMENDED)
- `--duration, -d` - Attack duration in seconds (0 = infinite)

Examples:
```bash
# Light GET flood with 5 attackers
d-stress attack http://localhost:80 --profile light

# POST flood with custom settings
d-stress attack http://localhost:80 --type post_flood --attacker 15 --payload-size 50

# Slowloris attack
d-stress attack http://localhost:80 --type slowloris --attacker 10
```

### status

Show the status of running containers.

```bash
d-stress status [--live]
```

### report

Generate a report from an attack session.

```bash
d-stress report [--format json|csv|text] [--output filename]
```

## Attack Types

### HTTP GET Flood
Sends many GET requests to overwhelm the target server. Tests how well a server handles high request volumes.

### HTTP POST Flood
Sends POST requests with large payloads (default 10KB). Tests both request handling and memory usage.

### Slowloris
Opens many connections and keeps them open by sending partial headers slowly. Tests connection handling limits.

### SYN Flood
Sends TCP SYN packets without completing the handshake. Tests firewall and TCP stack resilience.

### UDP Flood
Sends random UDP packets to saturate bandwidth. Tests network capacity.

### DNS Amplification
Sends DNS queries with spoofed source addresses. Tests reflection attack resilience.

## Profiles

Predefined configurations for quick testing:

| Profile | Attackers | Attack Type | Description |
|---------|-----------|-------------|-------------|
| light | 5 | get_flood | Basic connectivity test |
| medium | 15 | post_flood | Moderate load testing |
| heavy | 30 | post_flood | Maximum stress test |

## Safety Features

- **Private IP validation**: By default, only private IP addresses are allowed (10.x.x.x, 172.16-31.x.x, 192.168.x.x, localhost)
- **Public IP warning**: Attacking public IPs requires explicit `--allow-public` flag
- **Local-only by default**: The tool is designed for local testing only

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   CLI Tool      │────▶│  docker-compose │
│  (d-stress)     │     │   orchestration │
└─────────────────┘     └────────┬────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
     ┌────────▼────────┐ ┌──────▼───────┐ ┌───────▼───────┐
     │   Target        │ │  Attacker 1  │ │  Attacker N   │
     │  (Flask +       │ │  (Python)    │ │  (Python)     │
     │   Gunicorn)     │ │              │ │               │
     └─────────────────┘ └──────────────┘ └───────────────┘
```

## Project Structure

```
d-stress/
├── src/
│   ├── attacker.py          # Attack implementations
│   └── cli/
│       ├── main.py          # CLI entry point
│       ├── commands/
│       │   ├── attack.py    # Attack command
│       │   ├── status.py    # Status command
│       │   └── report.py    # Report command
│       └── profiles/        # Attack profiles
├── targets/
│   └── test_server.py       # Test target server
├── docker-compose.yml       # Container orchestration
├── pyproject.toml          # Python package config
└── README.md               # This file
```

## Troubleshooting

### Command not found after installation
Add Python Scripts directory to your PATH (see Installation section).

### Permission denied for raw sockets
SYN flood requires elevated privileges. Run with:
```bash
sudo docker-compose up --build
```

### Docker containers fail to start
Make sure Docker Desktop is running and you have enough system resources.

### Target server not responding
Check that port 80 is not in use by another service.

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. The authors are not responsible for any misuse or damage caused by this software. Only use on systems you own or have explicit written permission to test. Unauthorized testing against third-party systems may violate laws in your jurisdiction.
