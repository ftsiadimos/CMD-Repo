# Command‑CLI  
*A simple Flask‑based web UI for storing, searching and managing shell commands.*

---  

## Table of Contents
1. [Overview](#overview)  
2. [Features](#features)  
3. [Demo](#demo)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Running the Application](#running-the-application)  
7. [API Endpoints](#api-endpoints)  
8. [Testing](#testing)  
9. [Development](#development)  
10. [Contributing](#contributing)  
11. [License](#license)  

---  

## Overview
`command-cli` is a lightweight Flask application that lets you **save**, **search**, **tag**, and **share** shell commands through a clean web interface.  
It also provides a tiny JSON API so other tools (e.g., a terminal helper script) can fetch or add commands programmatically.

---  

## Features
- **CRUD UI** – add, edit, delete commands with description & tags.  
- **Search & pagination** – filter by text, control rows per page.  
- **Sortable columns** – click column headers to sort ascending/descending.  
- **Row‑click expand** – click any cell to reveal the full, un‑truncated command/description/tags.  
- **Copy button** – one‑click copy of the command to the clipboard.  
- **REST API** – `GET /api/commands` and `POST /api/commands`.  
- **Downloadable CLI helper** – `/download-cli` serves a `cli.py` script for terminal use.  
- **Responsive design** – works on desktop and mobile browsers.  

---  

## Demo
```bash
# Clone the repo
git clone https://github.com/yourusername/command-cli.git
cd command-cli

# Create a virtual environment and install deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the app
python app.py
```
Open <http://127.0.0.1:5000> in a browser.  

---  

## Installation

### Prerequisites
- Python 3.9+  
- `pip` (>=21)  
- SQLite (bundled with Python) – no external DB required.

### Steps
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/command-cli.git
cd command-cli

# 2. Set up a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
```
> **Tip:** The `requirements.txt` currently contains:
> ```
> Flask
> Flask-WTF
> Flask-SQLAlchemy
> ```

---  

## Configuration
Edit `config.py` (or create an instance config file `instance/config.py`) to override defaults:

```python
class Config:
    SECRET_KEY = "replace‑with‑a‑strong‑random‑value"
    SQLALCHEMY_DATABASE_URI = "sqlite:///instance/commands.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

*If you place a custom `instance/config.py`, Flask will load it automatically.*

---  

## Running the Application
```bash
# Development mode (auto‑reload)
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

Or simply:

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000`.  

---  

## API Endpoints
| Method | URL | Description | Example |
|--------|-----|-------------|---------|
| `POST` | `/api/commands` | Add a new command (JSON body). | `curl -X POST -H "Content-Type: application/json" -d '{"command":"ls -l","description":"List files","tags":"filesystem,list"}' http://localhost:5000/api/commands` |
| `GET`  | `/api/commands` | List all commands. Optional `search` query param. | `curl http://localhost:5000/api/commands?search=git` |

Responses are JSON; on success `POST` returns `{ "id": <int>, "command": "<cmd>" }`.

---  

## Testing
The project includes a basic test suite using **pytest**.

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

Add new tests in the `tests/` directory; they will be discovered automatically.

---  

## Development
### Project Structure
```
command-cli/
├─ app.py               # Flask factory & routes
├─ models.py            # SQLAlchemy models
├─ forms.py             # WTForms definitions
├─ config.py            # Default configuration
├─ templates/           # Jinja2 HTML templates
│   └─ index.html
├─ static/              # CSS/JS assets (if any)
├─ cli.py               # Optional helper script served for download
└─ README.md
```

### Adding a New Feature
1. Create/modify a view in `app.py` or a new blueprint.  
2. Add corresponding HTML in `templates/`.  
3. Update the database model in `models.py` if needed and run `flask db upgrade` (or simply `db.create_all()` for SQLite).  
4. Write unit tests under `tests/`.  

---  

## Contributing
Contributions are welcome! Please follow these steps:

1. Fork the repository.  
2. Create a feature branch: `git checkout -b feature/awesome-feature`.  
3. Make your changes, ensuring the test suite passes.  
4. Commit with a clear message and push to your fork.  
5. Open a Pull Request describing the change.

Please adhere to the existing code style (PEP 8) and include tests for new functionality.

---  

## License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.