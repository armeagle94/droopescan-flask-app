from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import threading
import time
import os
import re

app = Flask(__name__)

scan_progress = {
    'status': 'idle',
    'output': [],
    'report_path': ''
}

def run_scan(url):
    scan_progress['status'] = 'running'
    scan_progress['output'] = []
    
    report_filename = f"report_{int(time.time())}.txt"
    report_path = os.path.join("reports", report_filename)
    scan_progress['report_path'] = report_path

    os.makedirs("reports", exist_ok=True)

    # Regex to detect progress bar lines
    progress_pattern = re.compile(r"\[ *[= ]+ *\] \d+/\d+ \(\d+%\)")

    process = subprocess.Popen(["droopescan", "scan", "drupal", "-u", url], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    with open(report_path, 'w') as f:
        for line in process.stdout:
            clean_line = line.strip()
            # Skip progress bar lines
            if progress_pattern.search(clean_line):
                continue
            scan_progress['output'].append(clean_line)
            f.write(line)

    process.wait()
    scan_progress['status'] = 'done'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scan', methods=['POST'])
def start_scan():
    url = request.form['url']
    if scan_progress['status'] == 'running':
        return "Scan already running.", 400
    threading.Thread(target=run_scan, args=(url,)).start()
    return "Scan started."

@app.route('/progress')
def progress():
    return jsonify({
        'status': scan_progress['status'],
        'output': scan_progress['output'][-20:]  # last 20 lines
    })

@app.route('/download')
def download():
    if scan_progress['status'] == 'done' and os.path.exists(scan_progress['report_path']):
        return send_file(scan_progress['report_path'], as_attachment=True)
    return "Report not ready yet.", 404

if __name__ == '__main__':
    app.run(debug=True)
