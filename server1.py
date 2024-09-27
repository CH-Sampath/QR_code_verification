from flask import Flask, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import qrcode
import time
import io
import requests
import threading
import os
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

user_tokens = {}  # {user_id: {'token': '...', 'guid': '...', 'timestamp': 0}}
valid_channels = {}

SESSION_TIMEOUT = 15 * 60  # 15 minutes


# Function to continuously generate and emit new QR codes
def generate_qr_code():
    while True:
        # Create a unique GUID for the QR code
        guid = str(uuid.uuid4())
        valid_channels[guid] = time.time()  # Store GUID with timestamp for validation

        # Emit the new QR code data to connected clients
        socketio.emit('new_qr', {'qr_data': guid})
        print(f"New QR code (GUID) emitted: {guid}")

        # Wait 30 seconds before generating a new QR code
        time.sleep(30)


# Route to generate and return a QR code image
@app.route('/generate_qr')
def get_qr():
    # Create QR code image from the GUID
    guid = next(iter(valid_channels))  # Get the latest GUID
    qr = qrcode.make(guid)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


# Route to validate login based on scanned QR (GUID) and token
@app.route('/validate_login', methods=['POST'])
def validate_login():
    data = request.json
    guid = data['guid']
    token = data['token']
    user_id = data['user_id']

    if guid in valid_channels:
        # GUID is valid, proceed with login
        user_tokens[user_id] = {'token': token, 'guid': guid, 'timestamp': time.time()}
        session['user_id'] = user_id  # Store user_id in session
        session['guid'] = guid  # Store GUID in session
        session['token'] = token  # Store token in session
        print(session)

        # Notify the web client to redirect
        socketio.emit('login-event', {'token': token, 'user_id': user_id, 'guid': guid})
        return jsonify({'success': True, 'msg': "Login successful"})
    else:
        return jsonify({'success': False, 'msg': "Invalid GUID"}), 400


# Route to handle session heartbeat to keep the session alive
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    user_id = data['user_id']
    token = data['token']

    if user_id in user_tokens and user_tokens[user_id]['token'] == token:
        # Refresh the session timestamp
        if time.time() - user_tokens[user_id]['timestamp'] < SESSION_TIMEOUT*10:
            user_tokens[user_id]['timestamp'] = time.time()
            return jsonify({'success': True, 'msg': "Session valid"})
        else:
            return jsonify({'success': False, 'msg': "Session expired"}), 401
    return jsonify({'success': False, 'msg': "Invalid session"}), 401


# Route to log out and clear session data
@app.route('/logout', methods=['POST'])
def handle_logout():
    data = request.json
    user_id = data['user_id']
    if user_id in user_tokens:
        del user_tokens[user_id]
        session.pop('user_id', None)
        session.pop('guid', None)
        session.pop('token', None)
        return jsonify({'success': True, 'msg': "Logged out"})
    return jsonify({'success': False, 'msg': "Logout failed"}), 400


# Provide session data to the webapp.py (client)
@app.route('/get_session_data', methods=['POST'])
def get_session_data():
    data = request.json
    user_id = data.get('user_id')

    if user_id in user_tokens:
        # Return the session data for the requested user
        return jsonify({
            'user_id': user_id,
            'token': user_tokens[user_id]['token'],
            'guid': user_tokens[user_id]['guid']
        })
    else:
        return jsonify({'success': False, 'msg': "No session found"}), 404


# Listen for 'user_token' event from the mobile app
@socketio.on('user_token')
def handle_user_token(data):
    user_id = data['user_id']
    token = data['token']

    if user_id in user_tokens and user_tokens[user_id]['token'] == token:
        user_tokens[user_id]['timestamp'] = time.time()  # Refresh session timestamp
        emit('token_ack', {'message': 'Token received and session updated'})
    else:
        emit('token_error', {'message': 'Invalid token or user ID'})


if __name__ == '__main__':
    qr_thread = threading.Thread(target=generate_qr_code)
    qr_thread.daemon = True
    qr_thread.start()
    socketio.run(app, port=5000, debug=True)


