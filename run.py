import os
from app import create_app

# Create Flask app at import time (required for Gunicorn later)
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port)

# venv\Scripts\activate
# set FLASK_APP=run.py
# flask run --host=0.0.0.0 --port=5003
# flask run --port 5003 # This will only work if you have set FLASK_RUN_HOST=0.0.0.0 and FLASK_RUN_PORT=5003 in your environment variables



