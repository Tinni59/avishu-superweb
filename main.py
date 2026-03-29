"""Единственная точка входа: `python main.py`."""

from app import create_app
from extensions import socketio
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

app = create_app()

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

CORS(app, supports_credentials=True)

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5007,
        debug=True,
        allow_unsafe_werkzeug=True,
        use_reloader=False
    )