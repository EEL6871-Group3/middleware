import requests
r = requests.post('http://127.0.0.1:5000/pod', json={"job": "stress-ng --io 2 --timeout 1m", "name": 'test', 'node':'k8s-worker2'},timeout=2.50)
# r = requests.post('http://127.0.0.1:5000/pod-num')
# r = requests.get('http://127.0.0.1:5000/cpu')
# r = requests.get('http://127.0.0.1:5000/delete-pods')
print(r.content)
print(r.status_code)