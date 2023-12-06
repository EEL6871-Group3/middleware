from flask import Flask, jsonify, request
import threading
import psutil
import requests

app = Flask(__name__)
cpu_usage = 0
cpu = {"k8s-master": 82, "k8s-worker1": 3}
running_nodes = ["k8s-master"]


def update_value():
    global cpu_usage
    while True:
        cpu_p = psutil.cpu_percent(interval=1)
        cpu_usage = cpu_p


@app.route("/cpu", methods=["GET"])
def get_cpu():
    return jsonify(cpu)


@app.route("/pod-num", methods=["GET"])
def get_pod_num():
    return jsonify({"pod_num": 3})


@app.route("/pod", methods=["POST"])
def handle_post():
    # Parse JSON payload
    data = request.json

    # Extract job description from the payload
    job_description = data.get("job")
    print(job_description)

    # Return the pod_num as part of the JSON response
    return jsonify({"success": True, "msg": ""})


@app.route("/start-node", methods=["POST"])
def start_node():
    global cpu
    # Parse JSON payload
    data = request.json

    # Extract job description from the payload

    print(f"starting {data['node']}")
    cpu[data["node"]] = 3
    running_nodes.append(data["node"])
    print(cpu)

    # Return the pod_num as part of the JSON response
    return jsonify({"success": True, "msg": ""})


@app.route("/nodes", methods=["GET"])
def get_nodes():
    """return the list of nodes that is currently running.
    if error occurs, return "success" = False, and "msg" with the error message
    curl localhost:5001/nodes
    """
    global running_nodes
    return {"success": True, "msg": "", "nodes": running_nodes}
    # return {"success": True, "msg": "", "nodes": []}


@app.route("/lpod-num", methods=["GET"])
def get_lpod_podnum():
    """return the list of nodes that is currently running.
    if error occurs, return "success" = False, and "msg" with the error message
    curl localhost:5001/nodes
    """
    return {"success": True, "msg": "", "pod-num": 2}


if __name__ == "__main__":
    update_thread = threading.Thread(target=update_value)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5001)
