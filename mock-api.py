from flask import Flask, jsonify, request
import threading
import psutil
import requests

app = Flask(__name__)
cpu_usage = 0


def update_value():
    global cpu_usage
    while True:
        cpu_p = psutil.cpu_percent(interval=1)
        cpu_usage = cpu_p


@app.route("/cpu", methods=["GET"])
def get_cpu():
    return jsonify({"cpu_usage": cpu_usage})

@app.route("/pod-num", methods=["GET"])
def get_pod_num():
    return jsonify({"pod_num": 3})

@app.route('/pod', methods=['POST'])
def handle_post():
    # Parse JSON payload
    data = request.json

    # Extract job description from the payload
    job_description = data.get('job')
    print(job_description)

    # Return the pod_num as part of the JSON response
    return jsonify({"success": True, "msg": ""})

if __name__ == "__main__":
    update_thread = threading.Thread(target=update_value)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5001)
