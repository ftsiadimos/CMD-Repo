from flask import Blueprint, request, jsonify
from .models import db, Command, Subcommand

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/commands", methods=["POST"])
def api_add_command():
    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "Missing required field 'command'"}), 400

    cmd = Command(
        command=data["command"].strip(),
        description=data.get("description", "").strip() or None,
        tags=data.get("tags", "").strip() or None,
    )

    # Handle optional subcommands list in request JSON
    subitems = data.get('subcommands') or []
    for sc in subitems:
        sc_cmd = sc.get('command', '').strip()
        if not sc_cmd:
            continue
        sc_desc = sc.get('description', '').strip() if sc.get('description') else None
        cmd.subcommands.append(Subcommand(command=sc_cmd, description=sc_desc))

    db.session.add(cmd)
    db.session.commit()

    return jsonify({"id": cmd.id, "command": cmd.command}), 201


@api_bp.route("/api/commands", methods=["GET"])
def api_list_commands():
    search = request.args.get("search", "").strip()
    if search:
        q = (
            Command.command.ilike(f"%{search}%")
            | Command.description.ilike(f"%{search}%")
            | Command.tags.ilike(f"%{search}%")
        )
        commands = Command.query.filter(q).order_by(Command.created_at.desc()).all()
    else:
        commands = Command.query.order_by(Command.created_at.desc()).all()

    result = [
        {
            "id": c.id,
            "command": c.command,
            "description": c.description,
            "tags": c.tags,
            "created_at": c.created_at.isoformat(),
            "subcommands": [ {"command": sc.command, "description": sc.description} for sc in c.subcommands ],
        }
        for c in commands
    ]

    return jsonify(result), 200


@api_bp.route("/api/commands/<int:cmd_id>", methods=["GET"])
def api_get_command(cmd_id):
    cmd = db.session.get(Command, cmd_id)
    if not cmd:
        return jsonify({"error": f"Command with ID {cmd_id} not found."}), 404
    return jsonify({
        "id": cmd.id,
        "command": cmd.command,
        "description": cmd.description,
        "tags": cmd.tags,
        "created_at": cmd.created_at.isoformat(),
        "subcommands": [ {"command": sc.command, "description": sc.description} for sc in cmd.subcommands ],
    }), 200
