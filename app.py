from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import signal
import atexit
import time
from threading import Lock


app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'), static_folder=os.path.join(os.getcwd(), 'static'))


# Background wake detection subprocess (exits when wake word is heard)
jarvis_process = None
process_lock = Lock()


def terminate_child_process_tree():
    global jarvis_process
    with process_lock:
        if jarvis_process and jarvis_process.poll() is None:
            try:
                if os.name == 'nt':
                    # Kill the whole process tree on Windows
                    try:
                        creation_flag = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                        subprocess.run(
                            ['taskkill', '/PID', str(jarvis_process.pid), '/T', '/F'],
                            check=False,
                            creationflags=creation_flag,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT,
                        )
                    except Exception:
                        jarvis_process.kill()
                else:
                    jarvis_process.terminate()
            except Exception:
                pass
        jarvis_process = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/media/jarvis.mp3')
def media_jarvis_mp3():
    mp3_path = os.path.join(os.getcwd(), 'jarvis.mp3')
    return send_file(mp3_path, mimetype='audio/mpeg', as_attachment=False)


@app.route('/start', methods=['POST'])
def start_jarvis():
    global jarvis_process
    # Start background detector if not already running
    with process_lock:
        if not (jarvis_process and jarvis_process.poll() is None):
            python_exe = os.environ.get('PYTHON', 'python')
            jarvis_script = os.path.join(os.getcwd(), 'jarviswakeup.py')
            try:
                jarvis_process = subprocess.Popen(
                    [python_exe, jarvis_script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except Exception as exc:
                return jsonify({"status": "error", "message": str(exc)}), 500

    # Long-poll until detector exits (wake word detected) or timeout
    start_time = time.time()
    timeout_seconds = 10  # keep open for 10 seconds
    while True:
        with process_lock:
            if jarvis_process and jarvis_process.poll() is not None:
                exit_code = jarvis_process.returncode
                jarvis_process = None
                return jsonify({"wake": exit_code == 0}), 200
        if time.time() - start_time > timeout_seconds:
            # No wake detected within window; stop listener and return
            terminate_child_process_tree()
            return jsonify({"wake": False, "timeout": True}), 200
        time.sleep(0.25)


@app.route('/stop', methods=['POST'])
def stop_jarvis():
    terminate_child_process_tree()
    return jsonify({"status": "stopped"}), 200


    # No other routes required


if __name__ == '__main__':
    atexit.register(terminate_child_process_tree)
    app.run(host='127.0.0.1', port=5000, debug=True)



