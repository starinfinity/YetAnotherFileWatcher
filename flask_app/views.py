from flask import Blueprint, request, jsonify
from flask_app.models import db, Schedule

app_blueprint = Blueprint('app_blueprint', __name__)

@app_blueprint.route('/schedules', methods=['GET'])
def get_schedules():
    schedules = Schedule.query.all()
    return jsonify([{
        'id': s.id,
        'task_id': s.task_id,
        'schedule': s.schedule,
        'filename': s.filename,
        'filepath': s.filepath,
        'server_key': s.server_key,
        'retries': s.retries,
        'retry_delay': s.retry_delay,
        'timeout': s.timeout,
        'dependency_server_key': s.dependency_server_key,
        'command': s.command,
        'timestamp': s.timestamp.isoformat()
    } for s in schedules]), 201


@app_blueprint.route('/schedules', methods=['POST'])
def create_schedule():
    print(f"Request Path: {request.path}")
    print(f"Request Method: {request.method}")
    print(f"Request Headers: {request.headers}")
    print(f"Request JSON: {request.json}")
    if not request.json:
        return jsonify({'error': 'No JSON payload received'}), 400
    data = request.json
    print(data)
    new_schedule = Schedule(**data)
    db.session.add(new_schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule created', 'id': new_schedule.id}), 201


@app_blueprint.route('/schedules/<int:id>', methods=['PUT'])
def update_schedule(id):
    data = request.json
    schedule = Schedule.query.get(id)
    if not schedule:
        return jsonify({'message': 'Schedule not found'}), 404

    for key, value in data.items():
        setattr(schedule, key, value)

    db.session.commit()
    return jsonify({'message': 'Schedule updated'})


@app_blueprint.route('/schedules/<int:id>', methods=['DELETE'])
def delete_schedule(id):
    schedule = Schedule.query.get(id)
    if not schedule:
        return jsonify({'message': 'Schedule not found'}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': 'Schedule deleted'})
