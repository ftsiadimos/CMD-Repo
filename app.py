from app import create_app

# Create a WSGI application callable for Gunicorn (module-level variable `app`)
app = create_app()
