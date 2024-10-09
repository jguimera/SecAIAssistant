from flask import Flask
from flask_socketio import SocketIO
from app.SecAIAssistant  import SecAIAssistant
  
socketio = SocketIO()
secAIAssistant=SecAIAssistant('interactive')
def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gg65gjr39dkjn344_!67#'
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)
    return app

