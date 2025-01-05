import datetime
import json
import re
from collections import defaultdict

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from sqlalchemy import func

from flask_app.models import db, Schedule
import secrets, os

app_blueprint = Blueprint('app_blueprint', __name__)


# @app_blueprint.route('/schedules', methods=['GET'])
# def get_schedules():
#     schedules = Schedule.query.all()
#     return jsonify([{
#         'id': s.id,
#         'task_id': s.task_id,
#         'schedule': s.schedule,
#         'filename': s.filename,
#         'filepath': s.filepath,
#         'server_key': s.server_key,
#         'retries': s.retries,
#         'retry_delay': s.retry_delay,
#         'timeout': s.timeout,
#         'dependency_server_key': s.dependency_server_key,
#         'command': s.command,
#         'timestamp': s.timestamp.isoformat()
#     } for s in schedules]), 201
#
#
# @app_blueprint.route('/schedules/<int:id>', methods=['PUT'])
# def update_schedule(id):
#     data = request.json
#     schedule = Schedule.query.get(id)
#     if not schedule:
#         return jsonify({'message': 'Schedule not found'}), 404
#
#     for key, value in data.items():
#         setattr(schedule, key, value)
#
#     db.session.commit()
#     return jsonify({'message': 'Schedule updated'})
#
#
@app_blueprint.route('/delete_task/<int:id>', methods=['DELETE'])
def delete_schedule(id):
    schedule = Schedule.query.get(id)
    if not schedule:
        return jsonify({'message': 'Schedule not found'}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule deleted'})


# Secret Key Generation and Handling
def generate_secret_key(length=32):
    """Generates a secure random secret key."""
    return secrets.token_urlsafe(length)


def create_secret_key_file(filepath='secret_key.txt'):
    """
    Generates a secret key and saves it to a file.
    If the file already exists, it does nothing.
    """
    if not os.path.exists(filepath):
        secret_key = generate_secret_key()
        with open(filepath, 'w') as f:
            f.write(secret_key)


# Generate the secret key file if it doesn't exist
create_secret_key_file()

# Load the secret key from the file
try:
    with open('secret_key.txt', 'r') as f:
        app_blueprint.secret_key = f.read().strip()
except FileNotFoundError:
    print("Error: Secret key file not found. Please make sure 'create_secret_key_file()' is called.")
    exit(1)


# --- Routes ---

@app_blueprint.route('/')
def index():
    username = session.get('username', 'Guest')
    return render_template('landing_page.html', username=username)


@app_blueprint.route('/create_task')
def create_task():
    return render_template('create_task.html')


@app_blueprint.route('/tasks')
def view_tasks():
    tasks = Schedule.query.all()
    return render_template('view_tasks.html', tasks=tasks)


@app_blueprint.route('/stats')
def stats():
    return render_template('stats.html')


@app_blueprint.route('/add_task', methods=['POST'])
def add_task():
    task = Schedule(
        task_id=request.form['task_id'],
        schedule=request.form['schedule'],
        filename=request.form['filename'],
        filepath=request.form['filepath'],
        server_key=request.form['server_key'],
        retries=int(request.form.get('retries', 3)),
        retry_delay=int(request.form.get('retry_delay', 60)),
        timeout=int(request.form.get('timeout')) if request.form.get('timeout') else None,
        dependency_server_key=request.form.get('dependent_server_keys'),
        command=request.form.get('command')
    )
    db.session.add(task)
    db.session.commit()
    return redirect(url_for('app_blueprint.create_task'))


@app_blueprint.route('/current_jobs_data')
def current_jobs_data():
    running_jobs = Schedule.query.filter(Schedule.retries > 0).all()
    running_jobs_count = len([task for task in running_jobs if task.check_file()])

    failed_jobs = Schedule.query.filter(Schedule.retries <= 0).all()
    failed_jobs_count = len([task for task in failed_jobs if not task.check_file()])

    waiting_jobs = Schedule.query.filter(Schedule.retries > 0).all()
    waiting_jobs_count = len([task for task in waiting_jobs if not task.check_file()])

    retrying_jobs_count = len([task for task in running_jobs if not task.check_file()])  # Retrying jobs

    total_jobs = Schedule.query.count()

    return jsonify({
        'running_jobs': running_jobs_count,
        'failed_jobs': failed_jobs_count,
        'waiting_jobs': waiting_jobs_count,
        'retrying_jobs': retrying_jobs_count,  # Include retrying jobs in the response
        'total_jobs': total_jobs
    })


@app_blueprint.route('/failure_stats')
def failure_stats():
    # Calculate the date 7 days ago
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

    # Query the database for failed tasks in the last week
    failed_tasks = (
        Schedule.query.filter(Schedule.retries == 0, Schedule.id.in_(
            db.session.query(Schedule.id).filter(Schedule.check_file() == False)
        ))
        .filter(Schedule.timestamp >= one_week_ago)
        .all()
    )

    # Extract the day of the week and count failures for each day
    failure_counts = defaultdict(int)
    for task in failed_tasks:
        day_of_week = task.timestamp.strftime('%A')
        failure_counts[day_of_week] += 1

    # Prepare the data for the chart
    failure_stats = {
        'labels': list(failure_counts.keys()),
        'data': list(failure_counts.values())
    }
    return jsonify(failure_stats)


@app_blueprint.route('/running_sensors')
def running_sensors():
    running_tasks = Schedule.query.filter(Schedule.retries > 0).all()
    running_sensors = [{'name': task.task_id, 'status': 'Active'} for task in running_tasks]
    return jsonify(running_sensors)


@app_blueprint.route('/all_runs_data')
def all_runs_data():
    today = datetime.date.today()
    start_date = today - datetime.timedelta(weeks=4)

    all_runs = {
        'labels': [],
        'successes': [],
        'failures': []
    }

    for week in range(4):
        week_start = start_date + datetime.timedelta(weeks=week)
        week_end = week_start + datetime.timedelta(days=6)
        week_label = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

        success_count = (
            Schedule.query.filter(Schedule.timestamp >= week_start, Schedule.timestamp <= week_end)
            .filter(Schedule.retries > 0)
            .filter(Schedule.check_file() == True)
            .count()
        )

        failure_count = (
            Schedule.query.filter(Schedule.timestamp >= week_start, Schedule.timestamp <= week_end)
            .filter(Schedule.retries == 0)
            .filter(Schedule.check_file() == False)
            .count()
        )

        all_runs['labels'].append(week_label)
        all_runs['successes'].append(success_count)
        all_runs['failures'].append(failure_count)

    return jsonify(all_runs)


@app_blueprint.route('/task_summary')
def task_summary():
    failed = 0
    retrying = 0
    success = 0
    waiting = 0

    time_range = request.args.get('time_range', 'last-week')
    server = request.args.get('server', 'all')
    file_pattern = request.args.get('file_pattern', '')

    tasks = Schedule.query()

    if time_range != 'all':
        # Example time range filtering (adapt to your needs)
        if time_range == 'last-week':
            one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            tasks = tasks.filter(Schedule.timestamp >= one_week_ago)
        elif time_range == 'last-month':
            one_month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            tasks = tasks.filter(Schedule.timestamp >= one_month_ago)
        # Add more conditions for other time ranges as needed

    if server != 'all':
        tasks = tasks.filter_by(server_key=server)
    if file_pattern:
        tasks = [task for task in tasks if re.search(file_pattern, task.filename)]

    for task in tasks:
        if task.retries <= 0:  # Check retries first
            if task.check_file():
                success += 1
            else:
                failed += 1
        else:
            if task.check_file():
                success += 1
            else:
                retrying += 1

    waiting = len(tasks) - (failed + retrying + success)

    return jsonify({
        'failed': failed,
        'retrying': retrying,
        'success': success,
        'waiting': waiting
    })


@app_blueprint.route('/recent_activity')
def recent_activity():
    print("Entering recent_activity route")
    activity = []
    tasks = Schedule.query.all()

    print("Tasks:", tasks)

    for task in tasks:
        filename = task.filename

        print(f"Task: {task.task_id}, Retries: {task.retries}")

        if task.retries <= 0 and not task.check_file():
            status_message = "failed"
            print(f"Task {task.task_id} marked as failed")
        elif task.retries > 0 and not task.check_file():
            status_message = f"failed. Retrying in {task.retry_delay} seconds"
        else:
            status_message = "completed successfully"

        print("Filename:", filename, "Status:", status_message)
        activity.append({'filename': filename, 'status': status_message})

    print("Returning activity:", activity)
    return jsonify(activity)


@app_blueprint.route('/server_keys')
def server_keys():
    server_keys = []
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    config_file_path = os.path.join(BASE_DIR, "../server_config.json")
    try:
        with open(config_file_path, 'r') as f:
            server_creds = json.load(f)
            server_keys = list(server_creds.keys())
    except FileNotFoundError:
        print("server_creds.json not found.")
    except json.JSONDecodeError:
        print("Error decoding server_creds.json.")
    return jsonify(server_keys)



@app_blueprint.route('/trend_data')
def trend_data():
    time_range = request.args.get('time_range')
    server = request.args.get('server', 'all')
    file_pattern = request.args.get('file_pattern', '')

    tasks = Schedule.query

    if server != 'all':
        tasks = tasks.filter_by(server_key=server)
    if file_pattern:
        tasks = tasks.filter(Schedule.filename.like(f"%{file_pattern}%"))

    # Example trend data calculation (replace with your actual logic)
    # This example groups tasks by day and counts successes and failures
    trend_data = {
        'labels': [],
        'successes': [],
        'failures': []
    }

    if time_range == 'last-week':
        # Calculate data for the last 7 days
        today = datetime.date.today()
        for i in range(7):
            day = today - datetime.timedelta(days=i)
            success_count = (
                tasks.filter(func.date(Schedule.timestamp) == day)
                .filter(Schedule.retries > 0)
                .count()
            )
            failure_count = (
                tasks.filter(func.date(Schedule.timestamp) == day)
                .filter(Schedule.retries == 0)
                .count()
            )
            trend_data['labels'].append(day.strftime('%Y-%m-%d'))
            trend_data['successes'].append(success_count)
            trend_data['failures'].append(failure_count)
        # Reverse the lists to show data in chronological order
        trend_data['labels'].reverse()
        trend_data['successes'].reverse()
        trend_data['failures'].reverse()

        # Transform the data for the desired axes configuration
        transformed_data = {
            'labels': trend_data['failures'],  # Use failures as labels (X-axis)
            'datasets': [
                {
                    'label': 'Dates',  # Use Dates as label for the dataset
                    'data': trend_data['labels'],  # Use dates as data (Y-axis)
                }
            ]
        }

        return jsonify(transformed_data)  # Return the transformed data

    # Add more conditions for other time ranges as needed

    return jsonify(trend_data)


@app_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # ... (verify username and password against your database) ...
        # if valid_credentials:
        #     session['username'] = username
        #     return redirect(url_for('index'))
    return render_template('login.html')


@app_blueprint.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('app_blueprint.index'))
