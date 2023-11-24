# stress-ng --io 2 --vm 8 --vm-bytes 4G --timeout 2m
# stress-ng --io 1 --vm 8 --vm-bytes 1G --timeout 3m
# stress-ng --io 2 --timeout 1m

from flask import Flask, jsonify, request
import threading
# import psutil
import requests
import datetime
from kubernetes import client, config
import re
import subprocess
import json
import logging
import ast


config.load_kube_config()
app = Flask(__name__)
cpu_usage = 0


def update_value():
    global cpu_usage
    while True:
        cpu_p = psutil.cpu_percent(interval=1)
        cpu_usage = cpu_p

def parse_input(input_str): 
    args = re.findall(r"--([a-zA-Z-]+)\s+([^\s]+)", input_str)
    # print(args)
    args = {arg[0]: arg[1] for arg in args}
    # if 'io' not in args:
    #     args['io'] = ' '
    # if 'vm' not in args:
    #     args['vm'] = ' '
    # if 'vm-bytes' not in args:
    #     args['vm-bytes'] = ' '
    return args

def get_node_capacity(node_name):
    # Command to get node capacity
    command = ['kubectl', 'get', 'node', node_name, '-o', 'json']
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        node_info = json.loads(result.stdout)
        # Assuming the CPU capacity is provided in cores
        cpu_capacity_cores = int(node_info['status']['capacity']['cpu'])
        # Convert cores to nanocores
        return cpu_capacity_cores * 1e9
    else:
        logging.debug(f"Error getting node capacity: {result.stderr}")
        return None

def spin_up_pod(args, pod_name):
    base_pod_name = "stress-ng-pod"
    unique_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    pod_name = f"{base_pod_name}-{unique_suffix}-{pod_name}"
    if 'io' in args and 'vm' in args:
        stress_values = [
                "stress-ng", 
                "--io", args["io"],
                "--vm", args["vm"],
                "--vm-bytes", args["vm-bytes"], 
                "--timeout", args["timeout"]
            ]
    elif 'io' in args:
        stress_values = [
                "stress-ng", 
                "--io", args["io"],
                "--timeout", args["timeout"]
            ]
    else:
        stress_values = [
                "stress-ng",
                "--vm", args["vm"],
                "--vm-bytes", args["vm-bytes"], 
                "--timeout", args["timeout"]
            ]
    pod_manifest = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": pod_name
    },
    "spec": {
        "containers": [{
            "name": "stress-ng-container",
            "image": "polinux/stress-ng:latest",
            "args": stress_values
        }],
        "restartPolicy": "Never"
    }
} 

    # print(pod_manifest)
    api_instance = client.CoreV1Api()
    namespace = 'default'
    try:
        api_response = api_instance.create_namespaced_pod(namespace, pod_manifest)
        return f"Pod {pod_name} created. Status: {api_response.status}"
    except client.ApiException as e:
        return f"Exception when calling CoreV1Api->create_namespaced_pod: {e}"

# def get_pods():
#     v1 = client.CoreV1Api()
#     pod_list = v1.list_namespaced_pod("example")
#     for pod in pod_list.items:
#         print("%s\t%s\t%s" % (pod.metadata.name,
#                               pod.status.phase,
#                               pod.status.pod_ip))

@app.route("/cpu", methods=["GET"])
def get_cpu():
    usage = {}
    api = client.CustomObjectsApi()
    k8s_nodes = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
    for stats in k8s_nodes['items']:
        node_name = stats['metadata']['name']
        cpu_usage_nanoseconds = int(stats['usage']['cpu'].rstrip('n'))
        cpu_capacity_nanocores = get_node_capacity(node_name)
        # print("Node Name: %s\tCPU: %s\tMemory: %s" % (stats['metadata']['name'], stats['usage']['cpu'], stats['usage']['memory']))
        if cpu_capacity_nanocores:
                usage[node_name] = (cpu_usage_nanoseconds / cpu_capacity_nanocores) * 100
                # print(f"Node: {node_name}, CPU Usage: {cpu_usage_percentage:.2f}%")
        else:
                logging.debug(f"Could not calculate CPU usage for node: {node_name}")

    return jsonify(usage)

# @app.route("/delete-pods", methods=["GET"])
def delete_pods():
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod("default")
    deleted_pod = []
    for pod in pod_list.items:
        # # print(pod)
        # print("%s\t%s\t%s" % (pod.metadata.name,
        #                       pod.status.phase,
        #                       pod.status.pod_ip))
        if pod.status.phase == 'Succeeded':
            api_response = v1.delete_namespaced_pod(pod.metadata.name, 'default')
            deleted_pod.append(pod.metadata.name)
            
    return deleted_pod
    # return jsonify({"deleted_pod": deleted_pod})


@app.route("/pod-num", methods=["POST"])
def get_pod_num():
    v1 = client.CoreV1Api()
    deleted_pods = delete_pods()
    pod_list = v1.list_namespaced_pod("default")
    
    # for pod in pod_list.items:
    #     # print(pod)
    #     print("%s\t%s\t%s" % (pod.metadata.name,
    #                           pod.status.phase,
    #                           pod.status.pod_ip))
    return jsonify({"pod_num": len(pod_list.items), "deleted_pods": deleted_pods})

@app.route('/pod', methods=['POST'])
def handle_post():
    # Parse JSON payload
    data = request.json
    # print(data)
    # Extract job description from the payload
    job_description = data.get('job')
    pod_name = data.get('name')
    args = parse_input(job_description)
    # print(args)
    res = spin_up_pod(args, pod_name)
    # print(job_description)

    # Return the pod_num as part of the JSON response
    return jsonify({"success": True, "msg": res})

if __name__ == "__main__":
    update_thread = threading.Thread(target=update_value)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5001)