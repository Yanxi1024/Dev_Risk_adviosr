# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class AnalysisRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_json = db.Column(db.JSON, nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # "initial" or "detailed"
    ownership = db.Column(db.String(10), nullable=False)      # "personal" or "shared"
    risk_name = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
