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
    if 'io' not in args:
        args['io'] = 0
    if 'vm' not in args:
        args['vm'] = 0
    if 'vm-bytes' not in args:
        args['vm-bytes'] = 0
    return args

def spin_up_pod(args):
    base_pod_name = "stress-ng-pod"
    unique_suffix = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    pod_name = f"{base_pod_name}-{unique_suffix}"
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
            "args": [
                "stress-ng", 
                "--io", args["io"],
                "--vm", args["vm"],
                "--vm-bytes", args["vm-bytes"], 
                "--timeout", args["timeout"]
            ]
        }],
        "restartPolicy": "Never"
    }
}
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

    api = client.CustomObjectsApi()
    k8s_nodes = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")


    for stats in k8s_nodes['items']:
        print("Node Name: %s\tCPU: %s\tMemory: %s" % (stats['metadata']['name'], stats['usage']['cpu'], stats['usage']['memory']))

    return jsonify({"cpu_usage": 1})

@app.route("/delete-pods", methods=["GET"])
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
            
    return jsonify({"deleted_pod": deleted_pod})


@app.route("/pod-num", methods=["GET"])
def get_pod_num():
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod("default")
    for pod in pod_list.items:
        # print(pod)
        print("%s\t%s\t%s" % (pod.metadata.name,
                              pod.status.phase,
                              pod.status.pod_ip))
    return jsonify({"pod_num": len(pod_list.items)})

@app.route('/pod', methods=['POST'])
def handle_post():
    # Parse JSON payload
    data = request.json
    # print(data)
    # Extract job description from the payload
    job_description = data.get('job')
    args = parse_input(job_description)
    print(args)
    res = spin_up_pod(args)
    # print(job_description)

    # Return the pod_num as part of the JSON response
    return jsonify({"success": True, "msg": res})

if __name__ == "__main__":
    update_thread = threading.Thread(target=update_value)
    update_thread.daemon = True
    update_thread.start()

    app.run(debug=True, port=5001)