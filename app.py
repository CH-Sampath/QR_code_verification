from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from datetime import timedelta
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS
app.secret_key = 'supersecretkey'  # Ensure this is strong and unique
app.permanent_session_lifetime = timedelta(minutes=15)  # Session lifetime of 15 minutes
user_sessions = {}  # Dictionary to store user session details


# Index route (default page)
@app.route('/')
def index():
    return render_template('index.html')


# Login route (renders login page)
@app.route('/login')
def login():
    session.permanent = True  # Session persists as long as app.permanent_session_lifetime
    return render_template('login.html')


@app.route('/success', methods=['POST'])
def success():
    data = request.get_json()  # Parse the incoming JSON data
    print(data)
    token = data.get('token')
    user_id = data.get('user_id')
    guid = data.get('guid')
    session['token'] = token
    session['user_id'] = user_id
    session['guid'] = guid

    if token and user_id and guid:
        return redirect(url_for('render_success'))  # Redirect to GET /success
    else:
        return "Invalid data", 400  # Return error if any parameter is missing

    # A new route to render the success page using a GET request
@app.route('/success', methods=['GET'])
def render_success():
    if 'token' in session and 'user_id' in session and 'guid' in session:
        token = session['token']
        user_id = session['user_id']
        guid = session['guid']
        return render_template('success.html', token=token, user_id=user_id, guid=guid)
    else:
        return redirect(url_for('login'))  # Redirect to login if session data is missing


@app.route('/logout')
def logout():
    user_id = session.get('user_id')  # Get user_id before clearing session
    session.clear()  # Clear session on the web client side

    # Notify the server.py to log out and invalidate the session
    requests.post('http://localhost:5000/logout', json={'user_id': user_id})

    return redirect(url_for('login'))  # Redirect to login page after logout


# Check session validity (typically called by mobile app or web client for heartbeat)
@app.route('/check_session', methods=['POST'])
def check_session():
    data = request.json
    user_id = data['user_id']
    token = data['token']

    # Validate if the session is still active
    if user_id in user_sessions and session.get('token') == token:
        # Check session expiration based on the last recorded timestamp
        if time.time() - user_sessions[user_id]['timestamp'] < 15 * 60:
            return jsonify({'success': True, 'msg': "Session valid"})

    # If session is invalid or expired, return an error
    return jsonify({'success': False, 'msg': "Session expired"}), 401


# Route to get session data from server.py
@app.route('/get_session', methods=['POST'])
def get_session():
    data = request.json
    user_id = data.get('user_id')

    # Make a request to server.py to get session data
    response = requests.post('http://localhost:5000/get_session_data', json={'user_id': user_id})

    if response.status_code == 200:
        session_data = response.json()
        return jsonify({'success': True, 'data': session_data})
    else:
        return jsonify({'success': False, 'msg': "Failed to retrieve session data"}), response.status_code


if __name__ == '__main__':
    app.run(port=5001, debug=True)  # Webapp will run on port 5001
