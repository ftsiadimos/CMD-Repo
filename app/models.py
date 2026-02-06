from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


def utcnow():
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(200), nullable=False, index=True)  # indexed for faster search
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(100), nullable=True, index=True)  # indexed for faster filtering
    created_at = db.Column(db.DateTime, default=utcnow, index=True)  # indexed for sorting

    def __repr__(self):
        return f"<Command {self.command}>"