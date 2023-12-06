import requests
# r = requests.post('http://127.0.0.1:5001/pod', json={"job": "stress-ng --io 2 --timeout 4m", "name": 'test', 'node':'node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us'},timeout=2.50)
# r = requests.post('http://127.0.0.1:5001/pod', json={"job": "stress-ng --io 2 --timeout 4m", "name": 'test', 'node':'node2.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us'},timeout=2.50)

# r = requests.post('http://127.0.0.1:5001/pod-num',json={"node":'node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us'})
r = requests.get('http://127.0.0.1:5001/cpu')
# r = requests.get('http://127.0.0.1:5000/delete-pods')
# r = requests.post('http://127.0.0.1:5001/delete-node',json={'node':'node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us'})
# r = requests.post('http://127.0.0.1:5001/start-node',json={'node':'node1.group-3-project.ufl-eel6871-fa23-pg0.utah.cloudlab.us'})
# r = requests.get('http://127.0.0.1:5001/get-nodes')
print(r.content)
print(r.status_code)