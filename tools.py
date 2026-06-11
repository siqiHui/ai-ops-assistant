from typing import Dict, Any


def get_pod_logs(namespace: str, pod_name: str, tail_lines: int = 100) -> Dict[str, Any]:
    """
    Mock tool: simulate fetching Kubernetes pod logs.
    Later this can be replaced by real kubectl logs or Kubernetes Python client.
    """
    return {
        "tool": "get_pod_logs",
        "namespace": namespace,
        "pod_name": pod_name,
        "tail_lines": tail_lines,
        "logs": (
            "Error: missing config file /app/config.yaml\n"
            "Application failed to start\n"
            "Container exited with code 1"
        )
    }


def describe_pod(namespace: str, pod_name: str) -> Dict[str, Any]:
    """
    Mock tool: simulate kubectl describe pod.
    """
    return {
        "tool": "describe_pod",
        "namespace": namespace,
        "pod_name": pod_name,
        "events": [
            "Back-off restarting failed container",
            "MountVolume.SetUp failed for volume config-volume: configmap app-config not found"
        ],
        "status": "CrashLoopBackOff",
        "restart_count": 12
    }


AVAILABLE_TOOLS = {
    "get_pod_logs": get_pod_logs,
    "describe_pod": describe_pod,
}