# Middleware for Kubernetes Node Scaling and Stress Testing
## Overview
This middleware is designed to facilitate dynamic scaling of nodes in a Kubernetes cluster and stress testing individual nodes, when instructed by the controller. The primary functionalities include:

1. Cluster Scaling:
    - Start Node: Add a new node to the cluster.
    - Delete Node: Remove an existing node from the cluster.
    - Node Count: Get the number of currently running nodes.

2. Node Scaling:
    - Spin Up Pods: Launch stress-ng pods on specific nodes with customizable stress parameters.
    - Retrieve CPU Usage: Obtain CPU usage percentage for each node.
    - Pod count: Return running pod count for a particular node.
    - Delete pods: Deletes completed or failed pods.

# Middleware Implementation and brief function description

Middleware is implemented as a REST API to bridge the gap between the controller and the cluster. Some of the functions that middleware implements are scaling up and scaling down via the spin_up_pod and delete_pod method.
In order to run the middleware just type the following command 
Python3 middleware_api.py
After this you can call the various endpoints using python requests -

## The brief description of all the task performed by the Middleware is provided below

1. parse_input(input_str):
    - Parses the input string containing stress-ng arguments
    - Extracts argument name-value pairs using regex
    - Returns a dict with the extracted arguments

2. get_node_capacity(node_name):
    - Gets the CPU capacity in nanocores for the given node
    - Runs kubectl command to get node info in JSON format
    - Parses CPU capacity from the node info
    - Returns CPU capacity in nanocores

3. spin_up_pod(args, pod_name, node_name):
    - Creates a Kubernetes Pod manifest
    - Configures the manifest with stress-ng container and arguments
    - Assigns a unique name and specifies node to schedule pod on
    - Calls Kubernetes API to create the Pod on the cluster
    - Returns a message with the pod creation status

4. delete_pods():
    - Lists all pods in "default" namespace
    - Deletes any completed pods (Succeeded or Failed phase)
    - Returns a list with names of deleted pods


5. @app.route("/cpu") / get_cpu():
    - Utilizes Metric server API endpoint to get CPU usage on nodes
    - Calls Kubernetes metrics API to get node usage stats
    - Loops through each node
    - Gets CPU usage in nanoseconds
    - Calculates CPU capacity of node in nanocores
    - Computes CPU usage percentage
    - Adds node and usage to dictionary
    - Returns JSON with dict mapping node name to CPU usage percentage

6. @app.route("/pod-num") / get_pod_num():
    - API endpoint that when called will:
    - Delete any completed pods
    - List remaining pods
    - Return total pod count and deleted pods

7. @app.route('/pod') / handle_post():
    - Endpoint to create a new stress pod
    - Parses input parameters
    - Calls spin_up_pod() to create pod
    - Returns JSON message with result

8. @app.route("/nodes") / get_nodes():

    - Returns a list of the names of nodes currently running in the cluster (excluding the master node)
    - Calls the Kubernetes API to get all nodes
    - Loops through nodes and appends the name to a list if not the master node
    - Returns success=True and list of node names
    - Handles any errors and returns success=False with error message

9. evict_pods(node_name, api_instance):
    - Helper function to evict all pods on a given node
    - Gets all pods and filters to only those scheduled on the node
    - Calls Kubernetes API to delete/evict each pod
    - Logs and handles errors for each eviction

10. @app.route('/delete-node') / delete_node():

    - Endpoint to delete a Kubernetes node for cluster scale down
    - Gets node name from request payload
    - Calls evict_pods() to evict all pods first
    - Calls Kubernetes API to delete the node
    - Returns success or error message

11. @app.route('/start-node') / start_node():

    - Endpoint to add/start a new Kubernetes node to scale up cluster
    - Gets node name from request payload
    - Creates Node API object with node name
    - Calls Kubernetes API to create the Node resource
    - Returns success or error message

# API endpoints and call to functions - 
1. Get CPU Usage
    - Endpoint: /cpu
    - Method: GET
    - Description: Retrieve CPU usage percentage for each node in the cluster.
    - Example API Call (Python Requests):
```py
import requests

response = requests.get('http://localhost:5001/cpu')
cpu_data = response.json()
print(cpu_data)
```

2. Spin Up Pods
    - Endpoint: /pod
    - Method: POST
    - Description: Launch stress-ng pods on a specific node with given stress parameters.
    - Example API Call (Python Requests):
```py
import requests

payload = {
    "job": "stress-ng --io 2 --vm 8 --vm-bytes 4G --timeout 2m",
    "name": "example-pod",
    "node": "node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us"
}

response = requests.post('http://localhost:5001/pod', json=payload)
result = response.json()
print(result)
```

3. Delete Pods
    - Endpoint: /delete-pods
    - Method: GET
    - Description: Initiate deletion of completed/failed pods.
    - Example API Call (Python Requests):
```py
import requests

response = requests.get('http://localhost:5001/delete-pods')
deleted_pods = response.json()
print(deleted_pods)
```

4. Get Pod Count on a Node
    - Endpoint: /pod-num
    - Method: POST
    - Description: Get the number of pods running on a specific node.
    - Example API Call (Python Requests):
```py
import requests

payload = {"node": "node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us"}

response = requests.post('http://localhost:5001/pod-num', json=payload)
pod_info = response.json()
print(pod_info)
```

5. Get Nodes
    - Endpoint: /nodes
    - Method: GET
    - Description: Retrieve the list of nodes currently running in the cluster.
    - Example API Call (Python Requests):
```py
import requests

response = requests.get('http://localhost:5001/nodes')
nodes_info = response.json()
print(nodes_info)
```

6. Delete Node
    - Endpoint: /delete-node
    - Method: POST
    - Description: Remove a node from the cluster for scaling down.
    - Example API Call (Python Requests):

```py
import requests

payload = {"node": "node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us"}

response = requests.post('http://localhost:5001/delete-node', json=payload)
result = response.json()
print(result)
```
7. Start Node
    - Endpoint: /start-node
    - Method: POST
    - Description: Add a new node to the cluster for scaling up.
    - Example API Call (Python Requests):
```py
import requests

payload = {"node": "node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us"}

response = requests.post('http://localhost:5001/start-node', json=payload)
result = response.json()
print(result)
```

# RUN
```bash
python3 middleware_api.py
```
This will make api go live on http://128.110.217.71:5001 and http://127.0.0.1:5001