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
    logging.debug(f"Parsed input arguments: {args}")
    return args

def get_node_capacity(node_name):
    # Command to get node capacity
    command = ['kubectl', 'get', 'node', node_name, '-o', 'json']
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        node_info = json.loads(result.stdout)
        # Assuming the CPU capacity is provided in cores
        cpu_capacity_cores = int(node_info['status']['capacity']['cpu'])
        logging.info(f"Node {node_name} CPU capacity in cores: {cpu_capacity_cores}")
        # Convert cores to nanocores
        return cpu_capacity_cores * 1e9
    else:
        logging.debug(f"Error getting node capacity for {node_name}: {result.stderr}")
        return None

def spin_up_pod(args, pod_name, node_name):
    base_pod_name = "stress-ng-pod"
    unique_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    pod_name = f"{base_pod_name}-{unique_suffix}-{pod_name}"
    if 'io' in args and 'vm' in args and 'vm-bytes' in args:
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
        "nodeName": node_name,
        "tolerations":[{
            "key": "node-role.kubernetes.io/master",
            "operator": "Exists",
            "effect": "NoSchedule"
        }],
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
        logging.info(f"Pod {pod_name} successfully created with status: {api_response.status}")
        return f"Pod {pod_name} created. Status: {api_response.status}"
    except client.ApiException as e:
        logging.error(f"Exception in creating pod {pod_name}: {e}")
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
    logging.info("Initiating deletion of completed/failed pods")
    try:
        v1 = client.CoreV1Api()
        pod_list = v1.list_namespaced_pod("default")
        deleted_pod = []
        for pod in pod_list.items:
        # # print(pod)
        # print("%s\t%s\t%s" % (pod.metadata.name,
        #                       pod.status.phase,
        #                       pod.status.pod_ip))
            if pod.status.phase == 'Succeeded' or pod.status.phase == 'Failed':
                api_response = v1.delete_namespaced_pod(pod.metadata.name, 'default')
                deleted_pod.append(pod.metadata.name)

        logging.info(f"Deleted pods: {deleted_pod}")
        return deleted_pod
        # return jsonify({"deleted_pod": deleted_pod})
    except Exception as e:
        logging.error(f"Error in delete_pods: {e}")
        return []


@app.route("/pod-num", methods=["POST"])
def get_pod_num():
    logging.info("Received POST request to /pod-num endpoint")
    try:
        v1 = client.CoreV1Api()

        deleted_pods = delete_pods()
        data = request.json
        node_name = data.get('node')
        # pod_list = v1.list_namespaced_pod("default")
        field_selector = 'spec.nodeName='+node_name
        pod_list = v1.list_namespaced_pod(namespace = "default", watch=False, field_selector=field_selector)
        pod_count = len(pod_list.items)
        logging.info(f"Number of pods on node {node_name}: {pod_count}")
        # for pod in pod_list.items:
        #     print(pod)
        # print("%s\t%s\t%s" % (pod.metadata.name,
        #                       pod.status.phase,
        #                       pod.status.pod_ip))
        return jsonify({"pod_num": len(pod_list.items), "deleted_pods": deleted_pods})
    except Exception as e:
        logging.error(f"Error in get_pod_num: {e}")
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route('/pod', methods=['POST'])
def handle_post():
    logging.info("Received POST request to /pod endpoint")
    try:
        # Parse JSON payload
        data = request.json
        logging.debug(f"Request data: {data}")
        # print(data)
        # Extract job description from the payload
        job_description = data.get('job')
        pod_name = data.get('name')
        node_name = data.get('node')
        args = parse_input(job_description)   
        # print(args)
        res = spin_up_pod(args, pod_name, node_name)
        logging.info(f"Pod creation response: {res}")
        # print(job_description)

        # Return the pod_num as part of the JSON response
        return jsonify({"success": True, "msg": res})
    except Exception as e:
        logging.error(f"Error in handle_post: {e}")
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/nodes", methods=["GET"])
def get_nodes():
    """return the list of nodes that is currently running.
    if error occurs, return "success" = False, and "msg" with the error message
    curl localhost:5001/nodes
    """

    # implement the endpoint
    api_instance = client.CoreV1Api()
    try:
        # Retrieve the list of nodes
        nodes_all = api_instance.list_node()
        nodes_list = []
        for node in nodes_all.items:
            node_name = node.metadata.name
            if node_name != 'k8s-master':
                nodes_list.append(node_name)
        logging.info(f"Get nodes: {nodes_list}")
        return jsonify({"success": False, "msg": "error XXX occurred", "nodes": nodes_list})
        
    except Exception as e:
        logging.error(f"Error in get_nodes: {e}")
        return jsonify({"success": False, "msg": "error XXX occurred", "nodes": []})

@app.route('/delete-node', methods=['POST'])
def delete_node():
    """delete a node in the cluster for scaling down. Node name in the payload

    curl -X POST -H "Content-Type: application/json" -d '{"node": "k8s-worker1"}' http://localhost:5001/delete-node
    """
    # Parse JSON payload
    data = request.json
    node_name = data.get('node') 

    api_instance = client.CoreV1Api()

    try:
        # Delete the node
        api_instance.delete_node(node_name)
        logging.info(f"deleting node {node_name}")
        return jsonify({"success": True, "msg": ""})
    
    except Exception as e:
        logging.error(f"Error in delete_node: {e}")
        return jsonify({"success": False, "msg": "error occurred"})

@app.route('/start-node', methods=['POST'])
def start_node():
    """start a node in the cluster for scaling up. Node name in the payload

    curl -X POST -H "Content-Type: application/json" -d '{"node": "k8s-worker1"}' http://localhost:5001/start-node
    """
    # Parse JSON payload
    data = request.json
    node_name = data.get('node') 

    # start the node
    api_instance = client.CoreV1Api()
    metadata = client.V1ObjectMeta(name=node_name)
    node_spec = client.V1NodeSpec()

    node = client.V1Node(metadata=metadata, spec=node_spec)

    try:
        # Create the node
        api_instance.create_node(node)
        logging.info(f"starting node {node_name}")
        return jsonify({"success": True, "msg": ""})
    
    except Exception as e:
        logging.error(f"Error in start_node: {e}")
        return jsonify({"success": False, "msg": "error occurred"})

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info("Starting Flask application on port 5001")
    try:
        app.run(port=5001, host="0.0.0.0")
    except Exception as e:
        logging.critical(f"Flask application failed to start: {e}")
