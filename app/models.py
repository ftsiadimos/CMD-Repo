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

    # Relationship to subcommands (one-to-many)
    # Use backref name 'parent' to avoid collision with Subcommand.command column
    subcommands = db.relationship(
        'Subcommand',
        backref='parent',
        cascade='all, delete-orphan',
        lazy='joined',
    )

    def __repr__(self):
        return f"<Command {self.command}>"


class Subcommand(db.Model):
    """Represents a subcommand associated with a parent Command."""
    id = db.Column(db.Integer, primary_key=True)
    command_id = db.Column(db.Integer, db.ForeignKey('command.id', ondelete='CASCADE'), nullable=False, index=True)
    command = db.Column(db.String(200), nullable=False)  # subcommand text
    description = db.Column(db.String(300), nullable=True)

    def __repr__(self):
        return f"<Subcommand {self.command} for {self.command_id}>"