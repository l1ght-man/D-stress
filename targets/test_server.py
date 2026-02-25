from flask import Flask, request, jsonify
import logging
import datetime
import os
import threading
import time
import psutil

os.makedirs('logs', exist_ok=True)

# LOGS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/target.log'),
        logging.StreamHandler()
    ]
)
request_count = 0

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)

metrics = {
    'total_requests': 0,
    'total_errors': 0,
    'response_time': [],
    'current_interval_requests': 0,
    'attackers': {},
    'start_time': time.time(),
}
metrics_lock = threading.Lock()

def get_cpu_percent():
    """Get current CPU usage percentage"""
    return psutil.cpu_percent(interval=1)


@app.route('/')
def home():
    """handle incoming requests"""
    global request_count
    request_count += 1
    with metrics_lock:
        metrics['total_requests'] += 1
        metrics['current_interval_requests'] += 1

    return "WELCOME TO TEST SERVER! ", 200


@app.route('/report', methods=['POST'])
def report():
    """receive metrics from attackers"""
    data = request.json
    attacker_id = data.get('attacker_id', 'unknown')
    requests_sent = data.get('requests_sent', 0)
    errors = data.get('errors', 0)
    avg_response_time = data.get('avg_response_time_ms', 0)
    
    with metrics_lock:
        metrics['attackers'][attacker_id] = {
            'requests_sent': requests_sent,
            'errors': errors,
            'last_report': time.time()
        }
        metrics['total_errors'] += errors
        if avg_response_time > 0:
            metrics['response_time'].append(avg_response_time)
    
    return jsonify({'status': 'ok'}), 200


@app.route('/metrics')
def get_metrics():
    """return current metrics for CLI report"""
    with metrics_lock:
        return jsonify({
            'total_requests': metrics['total_requests'],
            'total_errors': metrics['total_errors'],
            'active_attackers': len(metrics['attackers']),
            'uptime_seconds': time.time() - metrics['start_time'],
            'cpu_percent': get_cpu_percent()
        })


@app.route('/api/data', methods=['POST'])
def post_data():
    """accepts POST requests for POST flood testing"""
    global request_count
    request_count += 1
    with metrics_lock:
        metrics['total_requests'] += 1
        metrics['current_interval_requests'] += 1

    return jsonify({'status': 'received', 'size': len(request.data)}), 200


if __name__ == '__main__':
    logging.info("Target server starting...")
    app.run(host='0.0.0.0', port=80)
