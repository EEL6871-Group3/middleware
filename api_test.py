import requests
# r = requests.post('http://127.0.0.1:5000/pod', json={"job": "stress-ng --io 2 --vm 8 --vm-bytes 4G --timeout 2m"},timeout=2.50)
# r = requests.get('http://127.0.0.1:5000/pod-num')
# r = requests.get('http://127.0.0.1:5000/cpu')
r = requests.get('http://127.0.0.1:5000/delete-pods')
print(r.content)
print(r.status_code)