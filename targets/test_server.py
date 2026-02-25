from flask import Flask , request  , jsonify
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
    return psutil.cpu_percent(interval=1)

def log_metrics():
    """system logs every 10 seconds """
    while True:
        time.sleep(10)
        with metrics_lock:
            req_per_second = metrics['current_interval_requests'] / 10.0
            avg_response = sum(metrics['response_time']) / len(metrics['response_time']) if metrics['response_time'] else 0
            cpu = get_cpu_percent()
            error_rate = (metrics['total_errors'] / metrics['total_requests'] *100) if metrics['total_requests'] > 0 else 0
            logging.info( "╔" + "═"*50 + "╗")
            logging.info( "║  + Attack Summary")
            logging.info(f"║  ├─ Total Requests: {metrics['total_requests']:,}")
            logging.info(f"║  ├─ Rate: {req_per_second:,.0f} req/s")
            logging.info(f"║  ├─ Active Attackers: {len(metrics['attackers'])}")
            logging.info(f"║  ├─ Avg Response Time: {avg_response:.0f}ms")
            logging.info(f"║  ├─ Error Rate: {error_rate:.2f}%")
            logging.info(f"║  └─ Target CPU: {cpu:.1f}%")
            logging.info( "╚" + "═"*50 + "╝")
            if metrics['total_requests'] >= 10000 and metrics['total_requests'] % 10000 == 0 :
                logging.info(f" MILESTONE: {metrics['total_requests']:,} total requests!")
            metrics['current_interval_requests'] = 0
            metrics['response_time'] = []

threading.Thread(target=log_metrics,daemon=True).start()


@app.route('/')

def home():
    """handle incoming requests logs retursn response"""
    global request_count 
    request_count += 1
    with metrics_lock:
        metrics['total_requests'] +=1
        metrics['current_interval_requests'] += 1
        
    
    if request_count % 5000 == 0 :
        requester_ip = request.remote_addr  
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message= f"Processed {request_count} requests; total:{request_count}. Last request from {requester_ip} at {current_time}"
        logging.info(log_message)

    return "WELCOME TO TEST SERVER! ", 200

@app.route('/report', methods =['POST'])
def report():
    data = request.json
    attacker_id = data.get('attacker_id', 'unknown')
    requests_sent = data.get('requests_sent',0)
    errors = data.get('errors', 0)
    avg_response_time = data.get('avg_response_time_ms',0)
    with metrics_lock:
        metrics['attackers'][attacker_id]={
            'requests_sent': requests_sent,
            'errors': errors,
            'last_report': time.time()
        }
        metrics['total_errors'] += errors
        if avg_response_time > 0:
            metrics['response_time'].append(avg_response_time)
    return jsonify({'status':'ok'}) , 200


@app.route('/metrics')
def get_metrics():
    with metrics_lock:
        return jsonify({
            'total_requests': metrics['total_requests'],
            'total_errors': metrics['total_errors'],
            'active_attackers': len(metrics['attackers']),
            'uptime_seconds': time.time() - metrics['start_time']
        })

@app.route('/api/data', methods=['POST'])
def post_data():
    """accepts post requests json type"""
    global request_count
    request_count += 1
    with metrics_lock:
        metrics['total_requests'] += 1
        metrics['current_interval_requests'] += 1

    return jsonify({'status': 'received', 'size': len(request.data)}) , 200



if __name__ == '__main__':
    """flask app run"""

    logging.info("target server starting with coordinator...")
    app.run(host='0.0.0.0' , port=80)