import re
import time
import json
import croniter
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_app.models import Schedule
import paramiko

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
config_file_path = os.path.join(BASE_DIR, "../server_config.json")

with open(config_file_path, "r") as f:
    SERVER_CONFIG = json.load(f)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, '../instance/scheduler.db')  # Adjust for instance folder
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)
session = Session()


def check_file(server, filepath, filename):
    """
    Checks if a file exists on a remote server using SSH.
    """
    print("Checking file on remote server...")

    # Fetch server credentials from configuration
    server_config = SERVER_CONFIG.get(server, {})
    hostname = server_config.get('hostname')
    username = server_config.get('username')
    password = server_config.get('password')
    server_path = server_config.get('path', '')

    # Combine server path, filepath, and filename
    full_path = os.path.join(server_path, filepath, filename)
    print(f"Checking file at: {full_path}")

    # Initialize SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"Connecting to {hostname}...")
        ssh.connect(hostname, username=username, password=password)

        sftp = ssh.open_sftp()

        print(f"Accessing directory: {filepath}")
        files = sftp.listdir(filepath)

        # Filter files using regex
        matched_files = [file for file in files if re.search(filename, file)]
        sftp.close()
        if matched_files:
            print(f"Matched files in {filepath}:")
            for file in matched_files:
                print(f" - {file}")
            return True
        else:
            print(f"No files matched the pattern {filename} in {filepath}.")
            return False
    except paramiko.ssh_exception.SSHException as e:
        print(e)
        return False

    finally:
        if sftp:
            sftp.close()
        print(f"Disconnected from {hostname}")


def execute_command(server, command):
    # Simulate running a command on the dependent server
    print(f"Executing command on {server}: {command}")
    os.system(command)


def process_schedule(schedule):
    print(f"processing config {schedule.task_id}")
    server_key = schedule.server_key
    dependency_server_key = schedule.dependency_server_key
    retries = schedule.retries
    retry_delay = schedule.retry_delay
    timeout = schedule.timeout
    command = schedule.command
    filepath = schedule.filepath
    filename = schedule.filename

    start_time = datetime.now()
    retry_count = 0

    while retry_count < retries and (datetime.now() - start_time).total_seconds() < timeout:
        if check_file(server_key, filepath, filename):
            execute_command(dependency_server_key, command)
            return True
        else:
            print("file not found..")
        time.sleep(retry_delay)
        retry_count += 1

    print(f"Task {schedule.task_id} timed out.")
    return False


def scheduler_loop():
    while True:
        now = datetime.now(timezone.utc)
        schedules = session.query(Schedule).all()

        for schedule in schedules:
            cron = croniter.croniter(schedule.schedule, schedule.timestamp)
            next_run = cron.get_next(datetime)
            next_run_local = next_run.replace(tzinfo=timezone.utc)
            print(now)
            print(next_run_local)
            print(next_run_local <= now)
            if next_run_local <= now:
                process_schedule(schedule)
                schedule.timestamp = now
                session.commit()

        time.sleep(60)


scheduler_loop()
