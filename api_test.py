import requests
# r = requests.post('http://127.0.0.1:5000/pod', json={"job": "stress-ng --io 2 --timeout 2m", "name": 'test', 'node':'k8s-worker1'},timeout=2.50)
r = requests.post('http://127.0.0.1:5000/pod-num',json={"node":'k8s-worker2'})
# r = requests.get('http://127.0.0.1:5000/cpu')
# r = requests.get('http://127.0.0.1:5000/delete-pods')
print(r.content)
print(r.status_code)