import requests


payload = {
    "task_id": "task_1",
    "schedule": "*/5 * * * *",
    "filename": "messages.txt",
    "filepath": "/usr/www/ncc/public/rg/trash/",
    "server_key": "unix",
    "retries": 3,
    "retry_delay": 60,
    "timeout": 3600,
    "dependency_server_key": "unix",
    "command": "echo Task Complete"
}

response = requests.get("http://127.0.0.1:5000/schedules", json=payload)

print("Status Code:", response.status_code)
print("Response Text:", response.text)
