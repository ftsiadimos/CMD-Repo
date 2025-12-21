# =============================================================================
# COMMAND REPOSITORY CLI - FLASK APPLICATION
# =============================================================================
# This Flask application provides a web interface and REST API for managing
# a repository of shell commands. Users can add, edit, delete, search, and
# export/import commands with descriptions and tags.
#
# Features:
# - Web interface with responsive design
# - REST API for programmatic access
# - Command search and filtering
# - JSON export/import functionality
# - CLI tool download
# =============================================================================

import os
from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify, send_from_directory, current_app
from config import Config
from models import db, Command
from forms import CommandForm

# =============================================================================
# APPLICATION FACTORY PATTERN
# =============================================================================
def create_app():
    """
    Application factory function that creates and configures the Flask app.
    Uses the factory pattern for better testability and configuration management.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Create DB tables once at startup (not on every request)
    with app.app_context():
        db.create_all()



    # =============================================================================
    # REST API ROUTES
    # =============================================================================
    # These routes provide programmatic access to the command repository.
    # All API endpoints return JSON responses.
    # =============================================================================

    # ---------- API: Add Command ----------
    @app.route("/api/commands", methods=["POST"])
    def api_add_command():
        """
        Create a new command via JSON API.

        HTTP Method: POST
        Endpoint: /api/commands
        Content-Type: application/json

        Request Body (JSON):
        {
            "command": "ls -la /var/log",     // Required: The shell command text
            "description": "List log files",  // Optional: Human-readable description
            "tags": "linux,logs,system"       // Optional: Comma-separated tags
        }

        Response (Success - 201 Created):
        {
            "id": 123,                       // Database ID of created command
            "command": "ls -la /var/log"     // The command that was stored
        }

        Response (Error - 400 Bad Request):
        {
            "error": "Missing required field 'command'"
        }

        Notes:
        - Command text is automatically trimmed of whitespace
        - Empty description/tags are stored as NULL in database
        - Duplicate commands are allowed (no uniqueness constraint)
        """
        # Parse JSON request body
        data = request.get_json()

        # Validate required fields
        if not data or "command" not in data:
            return jsonify({"error": "Missing required field 'command'"}), 400

        # Create new command object with sanitized data
        cmd = Command(
            command=data["command"].strip(),                    # Trim whitespace
            description=data.get("description", "").strip() or None,  # Empty string -> None
            tags=data.get("tags", "").strip() or None,          # Empty string -> None
        )

        # Save to database
        db.session.add(cmd)
        db.session.commit()

        # Return success response with created resource details
        return jsonify({"id": cmd.id, "command": cmd.command}), 201


    # ---------- API: List Commands ----------
    @app.route("/api/commands", methods=["GET"])
    def api_list_commands():
        """
        Retrieve all commands or search for specific commands via JSON API.

        HTTP Method: GET
        Endpoint: /api/commands
        Query Parameters:
            search (optional): Search term to filter commands

        Examples:
        GET /api/commands                          # Returns all commands
        GET /api/commands?search=docker           # Returns commands containing "docker"
        GET /api/commands?search=linux+logs       # Returns commands containing "linux" OR "logs"

        Response (Success - 200 OK):
        [
            {
                "id": 123,
                "command": "ls -la /var/log",
                "description": "List all log files with details",
                "tags": "linux,system,logs",
                "created_at": "2023-12-01T10:30:00.000Z"
            },
            ...
        ]

        Search Behavior:
        - Searches across command, description, and tags fields
        - Case-insensitive partial matching (ILIKE)
        - Uses OR logic between fields
        - Orders results by creation date (newest first)

        Notes:
        - Dates are returned in ISO 8601 format
        - NULL values are preserved as null in JSON
        - No pagination (returns all matching results)
        """
        # Extract and sanitize search parameter
        search = request.args.get("search", "").strip()

        # Build database query based on search criteria
        if search:
            # Create case-insensitive search filter across multiple fields
            # Uses SQL ILIKE for pattern matching with wildcards
            q = (
                Command.command.ilike(f"%{search}%")      # Search in command text
                | Command.description.ilike(f"%{search}%") # Search in descriptions
                | Command.tags.ilike(f"%{search}%")        # Search in tags
            )
            # Execute query with search filter, ordered by creation date
            commands = Command.query.filter(q).order_by(Command.created_at.desc()).all()
        else:
            # No search filter - return all commands
            commands = Command.query.order_by(Command.created_at.desc()).all()

        # Transform database objects to JSON-serializable dictionaries
        result = [
            {
                "id": c.id,
                "command": c.command,
                "description": c.description,  # May be None/null
                "tags": c.tags,                # May be None/null
                "created_at": c.created_at.isoformat(),  # Convert datetime to ISO string
            }
            for c in commands
        ]

        # Return JSON response
        return jsonify(result), 200

    # ---------- API: Get Single Command ----------
    @app.route("/api/commands/<int:cmd_id>", methods=["GET"])
    def api_get_command(cmd_id):
        """
        Retrieve a single command by its database ID via JSON API.

        HTTP Method: GET
        Endpoint: /api/commands/<id>
        URL Parameters:
            cmd_id (integer): The database ID of the command to retrieve

        Examples:
        GET /api/commands/123    # Retrieve command with ID 123

        Response (Success - 200 OK):
        {
            "id": 123,
            "command": "ls -la /var/log",
            "description": "List all log files with details",
            "tags": "linux,system,logs",
            "created_at": "2023-12-01T10:30:00.000Z"
        }

        Response (Error - 404 Not Found):
        {
            "error": "Command with ID 123 not found."
        }

        Notes:
        - ID must be a valid integer
        - Returns 404 for non-existent commands
        - Dates are in ISO 8601 format
        - NULL database values become null in JSON
        """
        # Query database for command by ID
        # db.session.get() returns None if not found (SQLAlchemy 2.0+)
        cmd = db.session.get(Command, cmd_id)

        # Handle case where command doesn't exist
        if not cmd:
            return jsonify({"error": f"Command with ID {cmd_id} not found."}), 404

        # Return command data as JSON
        return jsonify(
            {
                "id": cmd.id,
                "command": cmd.command,
                "description": cmd.description,  # May be None/null
                "tags": cmd.tags,                # May be None/null
                "created_at": cmd.created_at.isoformat(),  # Convert datetime to ISO string
            }
        ), 200

    # =============================================================================
    # WEB INTERFACE ROUTES
    # =============================================================================
    # These routes provide the HTML web interface for managing commands.
    # All routes use Flask-WTF forms and render Jinja2 templates.
    # =============================================================================

    # ---------- WEB: Home/Index Page ----------
    @app.route("/", methods=["GET"])
    def index():
        """
        Main page displaying all commands with search, pagination, and sorting.

        HTTP Method: GET
        Endpoint: /
        Template: index.html
        Query Parameters (all optional):
            page (int): Page number for pagination (default: 1)
            per_page (int): Commands per page (default: 5, max: 500)
            search (str): Search term for filtering commands
            sort_by (str): Field to sort by (command, description, tags, created_at)
            sort_dir (str): Sort direction (asc, desc) (default: desc)

        Examples:
        GET /                                    # Page 1, 5 commands, newest first
        GET /?page=2&per_page=10                # Page 2, 10 commands per page
        GET /?search=docker                     # Search for "docker" commands
        GET /?sort_by=command&sort_dir=asc      # Sort by command name A-Z

        Features:
        - Full-text search across command, description, and tags
        - Pagination with configurable page sizes
        - Multi-column sorting (ascending/descending)
        - Tag aggregation for search suggestions
        - Responsive table with expandable rows
        - Copy-to-clipboard functionality

        Template Variables:
            commands: List of Command objects for current page
            page: Current page number
            per_page: Commands per page
            total_pages: Total number of pages
            search: Current search term
            sort_by: Current sort field
            sort_dir: Current sort direction
            total_commands: Total command count
            total_tags: Set of all unique tags
        """
        # ===== PARAMETER PARSING =====
        # Extract pagination parameters with validation
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        # Sanitize per_page to prevent abuse (reasonable bounds)
        if per_page <= 0:
            per_page = 5  # Minimum 1 command per page
        if per_page > 500:
            per_page = 500  # Maximum 500 commands per page (performance limit)
        search = request.args.get('search', '')
        # Sorting
        sort_by = request.args.get('sort_by', '')
        sort_dir = request.args.get('sort_dir', 'desc')

        # ===== DATABASE QUERY BUILDING =====
        # Query the database, applying the search filter first
        query = Command.query
        if search:
            s = f"%{search}%"
            query = query.filter(
                Command.command.ilike(s)
                | Command.description.ilike(s)
                | Command.tags.ilike(s)
            )

        # ===== SORTING LOGIC =====
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

        # ===== PAGINATION CALCULATION =====
        total = query.count()
        total_pages = (total + per_page - 1) // per_page if per_page else 1

        # ===== TAG EXTRACTION =====
        # Optimized: single pass with set comprehension
        tag_rows = Command.query.with_entities(Command.tags).filter(Command.tags.isnot(None)).all()
        total_tags = {
            tag.strip()
            for row in tag_rows
            for tag in row[0].split(",")
            if tag.strip()
        }

        # ===== PAGINATED QUERY EXECUTION =====
        commands = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        # ===== TEMPLATE RENDERING =====
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

    # ---------- WEB: Add New Command ----------
    @app.route("/add", methods=["GET", "POST"])
    def add():
        """
        Display form to add a new command and handle form submission.
        GET /add - Show add form
        POST /add - Process form submission
        """
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

    # ---------- WEB: Edit Existing Command ----------
    @app.route("/edit/<int:cmd_id>", methods=["GET", "POST"])
    def edit(cmd_id):
        """
        Display form to edit an existing command and handle form submission.
        GET /edit/123 - Show edit form for command ID 123
        POST /edit/123 - Process form submission
        """
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

    # ---------- WEB: Delete Command ----------
    @app.route("/delete/<int:cmd_id>", methods=["POST"])
    def delete(cmd_id):
        """
        Delete a command by ID.
        POST /delete/123 - Delete command with ID 123
        """
        cmd = Command.query.get_or_404(cmd_id)
        db.session.delete(cmd)
        db.session.commit()
        flash("Command deleted.", "warning")
        return redirect(url_for("index"))

    # ---------- WEB: Download CLI Tool ----------
    @app.route('/download-cli')
    def download_cli():
        """
        Download the command-line interface tool.
        GET /download-cli - Download repocomcli file
        """
        # Pass the directory as the first positional argument
        return send_from_directory(
            current_app.root_path,   # <-- positional, not keyword
            'repocomcli',
            as_attachment=True
        )

    # ---------- WEB: Help Page ----------
    @app.route("/help")
    def help_page():
        """
        Display help documentation for the CLI tool.
        GET /help - Show CLI usage documentation
        """
        return render_template("help.html")

    # ---------- WEB: Export Commands to JSON ----------
    @app.route('/export-json')
    def export_json():
        """
        Export all commands as a downloadable JSON file.
        GET /export-json - Download commands_backup.json
        """
        commands = Command.query.order_by(Command.created_at.desc()).all()
        data = [
            {
                "id": cmd.id,
                "command": cmd.command,
                "description": cmd.description,
                "tags": cmd.tags,
                "created_at": cmd.created_at.isoformat() if cmd.created_at else None,
            }
            for cmd in commands
        ]
        response = jsonify(data)
        response.headers['Content-Disposition'] = 'attachment; filename=commands_backup.json'
        response.headers['Content-Type'] = 'application/json'
        return response

    # ---------- WEB: Import Commands from JSON ----------
    @app.route('/import-json', methods=['GET', 'POST'])
    def import_json():
        """
        Import commands from an uploaded JSON file.
        GET /import-json - Show upload form
        POST /import-json - Process uploaded JSON file
        """
        if request.method == 'POST':
            # ===== FILE VALIDATION =====
            if 'file' not in request.files:
                flash('No file selected.', 'danger')
                return redirect(url_for('import_json'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(url_for('import_json'))
            
            if not file.filename.endswith('.json'):
                flash('Please upload a JSON file.', 'danger')
                return redirect(url_for('import_json'))
            
            # ===== JSON PARSING AND IMPORT =====
            try:
                import json
                from datetime import datetime, timezone
                
                data = json.load(file)
                if not isinstance(data, list):
                    flash('Invalid JSON format. Expected a list of commands.', 'danger')
                    return redirect(url_for('import_json'))
                
                # ===== PROCESSING IMPORT DATA =====
                imported_count = 0
                skipped_count = 0
                
                for item in data:
                    if not isinstance(item, dict) or 'command' not in item:
                        skipped_count += 1
                        continue
                    
                    # Check if command already exists
                    existing = Command.query.filter_by(command=item['command']).first()
                    if existing:
                        skipped_count += 1
                        continue
                    
                    cmd = Command(
                        command=item['command'].strip(),
                        description=item.get('description', '').strip() if item.get('description') else None,
                        tags=item.get('tags', '').strip() if item.get('tags') else None,
                    )
                    db.session.add(cmd)
                    imported_count += 1
                
                db.session.commit()
                flash(f'Successfully imported {imported_count} commands. Skipped {skipped_count} (duplicates or invalid).', 'success')
                return redirect(url_for('index'))
                
            # ===== ERROR HANDLING =====
            except json.JSONDecodeError:
                flash('Invalid JSON file. Please check the file format.', 'danger')
                return redirect(url_for('import_json'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error importing file: {str(e)}', 'danger')
                return redirect(url_for('import_json'))
        
        return render_template('import.html')

    # =============================================================================
    # APPLICATION CREATION AND EXECUTION
    # =============================================================================
    return app

# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
# This block only runs when the script is executed directly (not imported).
# Used for development server with debug mode enabled.
# =============================================================================
app = create_app()

if __name__ == "__main__":
    # When running with python app.py the debug reloader is handy.
    app.run(debug=True)