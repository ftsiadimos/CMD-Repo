import os
from flask import Flask
from config import Config
from .models import db


def create_app():
    """Create and configure the Flask application."""
    # Use project-level templates/static directories (templates/ and static/ are at repo root)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=template_folder,
        static_folder=static_folder,
    )

    # Ensure the instance folder exists so the SQLite DB file can be created
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Create DB tables once at startup
    with app.app_context():
        db.create_all()

    # Register Blueprints
    from .api import api_bp
    from .views import web_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # Backwards compatibility: expose original endpoint names used by templates
    # Templates and some code expect endpoints like 'index', 'add', 'edit', etc.
    # Map these to the blueprint view functions so url_for('index') still works.
    app.add_url_rule('/', endpoint='index', view_func=app.view_functions['web.index'])
    app.add_url_rule('/add', endpoint='add', view_func=app.view_functions['web.add'], methods=['GET','POST'])
    app.add_url_rule('/edit/<int:cmd_id>', endpoint='edit', view_func=app.view_functions['web.edit'], methods=['GET','POST'])
    app.add_url_rule('/delete/<int:cmd_id>', endpoint='delete', view_func=app.view_functions['web.delete'], methods=['POST'])
    app.add_url_rule('/download-cli', endpoint='download_cli', view_func=app.view_functions['web.download_cli'])
    app.add_url_rule('/help', endpoint='help_page', view_func=app.view_functions['web.help_page'])
    app.add_url_rule('/export-json', endpoint='export_json', view_func=app.view_functions['web.export_json'])
    app.add_url_rule('/import-json', endpoint='import_json', view_func=app.view_functions['web.import_json'], methods=['GET','POST'])

    return app

# For WSGI servers like Gunicorn: expose a module-level `app` callable
app = create_app()
