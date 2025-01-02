from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), unique=True, nullable=False)
    schedule = db.Column(db.String(50), nullable=False)  # Cron expression
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    server_key = db.Column(db.String(50), nullable=False)
    retries = db.Column(db.Integer, default=3)
    retry_delay = db.Column(db.Integer, default=60)  # Seconds
    timeout = db.Column(db.Integer, nullable=False)
    dependency_server_key = db.Column(db.String(50), nullable=False)
    command = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Schedule {self.task_id}>"
