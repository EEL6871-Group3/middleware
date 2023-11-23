import datetime
from kubernetes import client, config


config.load_kube_config()

# Generate a unique pod name
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
                "--io", "1",
                "--vm", "1",
                "--vm-bytes", "1G",
                "--timeout", "1m"
            ]
        }]
    }
}

api_instance = client.CoreV1Api()
namespace = 'default'

try:
    api_response = api_instance.create_namespaced_pod(namespace, pod_manifest)
    print(f"Pod {pod_name} created. Status: {api_response.status}")
except client.ApiException as e:
    print(f"Exception when calling CoreV1Api->create_namespaced_pod: {e}")
