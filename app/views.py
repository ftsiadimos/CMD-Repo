import os
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    send_from_directory,
    current_app,
    jsonify,
)
from .models import db, Command, Subcommand
from .forms import CommandForm

web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    if per_page <= 0:
        per_page = 5
    if per_page > 500:
        per_page = 500

    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', '')
    sort_dir = request.args.get('sort_dir', 'desc')

    query = Command.query
    if search:
        s = f"%{search}%"
        query = query.filter(
            Command.command.ilike(s)
            | Command.description.ilike(s)
            | Command.tags.ilike(s)
        )

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
        query = query.order_by(Command.created_at.desc())

    total = query.count()
    total_pages = (total + per_page - 1) // per_page if per_page else 1

    tag_rows = Command.query.with_entities(Command.tags).filter(Command.tags.isnot(None)).all()
    total_tags = {
        tag.strip()
        for row in tag_rows
        for tag in row[0].split(",")
        if tag.strip()
    }

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
        total_tags=total_tags,
    )


@web_bp.route("/add", methods=["GET", "POST"])
def add():
    form = CommandForm()
    if form.validate_on_submit():
        cmd = Command(
            command=form.command.data.strip(),
            description=form.description.data.strip() or None,
            tags=form.tags.data.strip() or None,
        )

        # Add subcommands from the form (if any)
        sub_cmds = request.form.getlist('subcmd_command[]')
        sub_descs = request.form.getlist('subcmd_description[]')
        for i, sc in enumerate(sub_cmds):
            sc_text = sc.strip()
            if not sc_text:
                continue
            sc_desc = (sub_descs[i].strip() if i < len(sub_descs) else None) or None
            cmd.subcommands.append(Subcommand(command=sc_text, description=sc_desc))

        db.session.add(cmd)
        db.session.commit()
        flash("Command added successfully!", "success")
        return redirect(url_for("web.index"))
    return render_template("add.html", form=form)


@web_bp.route("/edit/<int:cmd_id>", methods=["GET", "POST"])
def edit(cmd_id):
    cmd = Command.query.get_or_404(cmd_id)
    form = CommandForm(obj=cmd)
    if form.validate_on_submit():
        cmd.command = form.command.data.strip()
        cmd.description = form.description.data.strip() or None
        cmd.tags = form.tags.data.strip() or None

        # Replace subcommands with submitted list
        sub_cmds = request.form.getlist('subcmd_command[]')
        sub_descs = request.form.getlist('subcmd_description[]')

        # Clear existing subcommands and add new ones
        cmd.subcommands[:] = []
        for i, sc in enumerate(sub_cmds):
            sc_text = sc.strip()
            if not sc_text:
                continue
            sc_desc = (sub_descs[i].strip() if i < len(sub_descs) else None) or None
            cmd.subcommands.append(Subcommand(command=sc_text, description=sc_desc))

        db.session.commit()
        flash("Command updated.", "info")
        return redirect(url_for("web.index"))
    return render_template("edit.html", form=form, command=cmd)


@web_bp.route("/delete/<int:cmd_id>", methods=["POST"])
def delete(cmd_id):
    cmd = Command.query.get_or_404(cmd_id)
    db.session.delete(cmd)
    db.session.commit()
    flash("Command deleted.", "warning")
    return redirect(url_for("web.index"))


@web_bp.route('/download-cli')
def download_cli():
    # The CLI tool lives at the project root. When the app is packaged inside
    # the `app` folder, adjust the directory to the parent of the package root.
    project_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
    return send_from_directory(project_root, 'repocomcli', as_attachment=True)


@web_bp.route("/help")
def help_page():
    return render_template("help.html")


@web_bp.route('/export-json')
def export_json():
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


@web_bp.route('/import-json', methods=['GET', 'POST'])
def import_json():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('web.import_json'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('web.import_json'))

        if not file.filename.endswith('.json'):
            flash('Please upload a JSON file.', 'danger')
            return redirect(url_for('web.import_json'))

        try:
            import json

            data = json.load(file)
            if not isinstance(data, list):
                flash('Invalid JSON format. Expected a list of commands.', 'danger')
                return redirect(url_for('web.import_json'))

            imported_count = 0
            skipped_count = 0

            for item in data:
                if not isinstance(item, dict) or 'command' not in item:
                    skipped_count += 1
                    continue

                existing = Command.query.filter_by(command=item['command']).first()
                if existing:
                    skipped_count += 1
                    continue

                cmd = Command(
                    command=item['command'].strip(),
                    description=item.get('description', '').strip() if item.get('description') else None,
                    tags=item.get('tags', '').strip() if item.get('tags') else None,
                )

                # Import subcommands if present
                subitems = item.get('subcommands') or []
                for sc in subitems:
                    sc_cmd = sc.get('command', '').strip()
                    if not sc_cmd:
                        continue
                    sc_desc = sc.get('description', '').strip() if sc.get('description') else None
                    cmd.subcommands.append(Subcommand(command=sc_cmd, description=sc_desc))

                db.session.add(cmd)
                imported_count += 1

            db.session.commit()
            flash(f'Successfully imported {imported_count} commands. Skipped {skipped_count} (duplicates or invalid).', 'success')
            return redirect(url_for('web.index'))

        except json.JSONDecodeError:
            flash('Invalid JSON file. Please check the file format.', 'danger')
            return redirect(url_for('web.import_json'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing file: {str(e)}', 'danger')
            return redirect(url_for('web.import_json'))

    return render_template('import.html')
