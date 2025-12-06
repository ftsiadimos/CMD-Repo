import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify, send_from_directory, current_app
from config import Config
from models import db, Command
from forms import CommandForm

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Create DB tables on first run
    @app.before_request
    def create_tables():
        db.create_all()



    # -------------------------------------------------------
    # 3.  API Routes – add these before the line "return app"
    # -------------------------------------------------------

    # ---------- API ----------

    @app.route("/api/commands", methods=["POST"])
    def api_add_command():
        """
        Create a new command via JSON:
            {
                "command": "ls -l",
                "description": "List files",
                "tags": "filesystem,list"
            }
        """
        data = request.get_json()
        if not data or "command" not in data:
            return jsonify({"error": "Missing required field 'command'"}), 400

        cmd = Command(
            command=data["command"].strip(),
            description=data.get("description", "").strip() or None,
            tags=data.get("tags", "").strip() or None,
        )
        db.session.add(cmd)
        db.session.commit()
        return jsonify({"id": cmd.id, "command": cmd.command}), 201


    @app.route("/api/commands", methods=["GET"])
    def api_list_commands():
        """
        Return all commands in JSON.
        Optional query parameter: search=<text>
        """
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
            }
            for c in commands
        ]
        return jsonify(result), 200

        # -----------------------------------------------------------------
        # 4.  API route for a single command by ID
        # -----------------------------------------------------------------
    @app.route("/api/commands/<int:cmd_id>", methods=["GET"])
    def api_get_command(cmd_id):
            """Return a single command by its ID.

            Returns a JSON object with the same fields as the list endpoint.
            If the command does not exist, a 404 error with a JSON error message
            is returned.
            """
            cmd = Command.query.get(cmd_id)
            if not cmd:
                return jsonify({"error": f"Command with ID {cmd_id} not found."}), 404
            return jsonify(
                {
                    "id": cmd.id,
                    "command": cmd.command,
                    "description": cmd.description,
                    "tags": cmd.tags,
                    "created_at": cmd.created_at.isoformat(),
                }
            ), 200


    # ---------- Routes ----------

    @app.route("/", methods=["GET"])
    def index():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        # sanitize per_page to reasonable bounds (default to 5)
        if per_page <= 0:
            per_page = 5
        if per_page > 500:
            per_page = 500
        search = request.args.get('search', '')
        # Sorting
        sort_by = request.args.get('sort_by', '')
        sort_dir = request.args.get('sort_dir', 'desc')

        # Query the database, applying the search filter first
        query = Command.query
        if search:
            s = f"%{search}%"
            query = query.filter(
                Command.command.ilike(s)
                | Command.description.ilike(s)
                | Command.tags.ilike(s)
            )

        # Apply ordering based on sort params (validate against allowed columns)
        allowed_sorts = {
            'command': Command.command,
            'description': Command.description,
            'tags': Command.tags,
            'created_at': Command.created_at,
        }
        if sort_by in allowed_sorts:
            col = allowed_sorts[sort_by]
            if sort_dir == 'asc':
                query = query.order_by(col.asc())
            else:
                query = query.order_by(col.desc())
        else:
            # default ordering
            query = query.order_by(Command.created_at.desc())

        total = query.count()
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        tag_rows = Command.query.with_entities(Command.tags).all()
        unique_tags = set()
        for row in tag_rows:
            if not row[0]:
                continue
            for tag in [t.strip() for t in row[0].split(",") if t.strip()]:
                unique_tags.add(tag)
        total_tags = unique_tags
       
        commands = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return render_template(
            'index.html',
            commands=commands,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            total_commands=total,
            total_tags=total_tags
        )

    @app.route("/add", methods=["GET", "POST"])
    def add():
        """Create a new command."""
        form = CommandForm()
        if form.validate_on_submit():
            cmd = Command(
                command=form.command.data.strip(),
                description=form.description.data.strip() or None,
                tags=form.tags.data.strip() or None,
            )
            db.session.add(cmd)
            db.session.commit()
            flash("Command added successfully!", "success")
            return redirect(url_for("index"))
        return render_template("add.html", form=form)

    @app.route("/edit/<int:cmd_id>", methods=["GET", "POST"])
    def edit(cmd_id):
        """Edit an existing command."""
        cmd = Command.query.get_or_404(cmd_id)
        form = CommandForm(obj=cmd)
        if form.validate_on_submit():
            cmd.command = form.command.data.strip()
            cmd.description = form.description.data.strip() or None
            cmd.tags = form.tags.data.strip() or None
            db.session.commit()
            flash("Command updated.", "info")
            return redirect(url_for("index"))
        return render_template("edit.html", form=form, command=cmd)

    @app.route("/delete/<int:cmd_id>", methods=["POST"])
    def delete(cmd_id):
        """Delete a command."""
        cmd = Command.query.get_or_404(cmd_id)
        db.session.delete(cmd)
        db.session.commit()
        flash("Command deleted.", "warning")
        return redirect(url_for("index"))

    @app.route('/download-cli')
    def download_cli():
        """Serve the cli.py file for download."""
        # Pass the directory as the first positional argument
        return send_from_directory(
            current_app.root_path,   # <-- positional, not keyword
            'repocomcli',
            as_attachment=True
        )

    @app.route("/help")
    def help_page():
        """Render the CLI help page."""
        return render_template("help.html")

    @app.route('/backup')
    def backup():
        """Send the SQLite database file as a download."""
        db_path = os.path.join(current_app.root_path, 'instance/app.db')
        if not os.path.isfile(db_path):
            abort(404, description="Database file not found")
        # `as_attachment=True` forces a download dialog
        return send_from_directory(
            directory=os.path.dirname(db_path),
            path=os.path.basename(db_path),
            as_attachment=True,
            download_name='app.db'
        )

    return app

app = create_app()

if __name__ == "__main__":
    # When running with python app.py the debug reloader is handy.
    app.run(debug=True)