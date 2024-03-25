from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@app.route('/', methods=['GET'])
def index():
    return """
    <script src="https://cdn.socket.io/socket.io-1.2.0.js"></script>
<script>
    var socket = io.connect('http://localhost:5000');
    socket.on('connect', function() {
        console.log('Connected!');
    });
    socket.on('disconnect', function() {
        console.log('Disconnected!');
    });
</script>
    """

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)