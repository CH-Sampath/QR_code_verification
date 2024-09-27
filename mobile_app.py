from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import cv2
import requests
import os
import pyzbar.pyzbar as pyzbar
import socketio

sio = socketio.Client()


class QRScannerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Scan QR Code")
        self.button = Button(text="Start Scanning", on_press=self.start_scanning)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.button)

        sio.connect('http://127.0.0.1:5000')

        return self.layout

    def start_scanning(self, instance):
        self.label.text = "Scanning..."
        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def update(self, dt):
        url = 'http://192.168.137.176:8080/video'
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            self.label.text = "Failed to connect to camera"
            return
        ret, frame = cap.read()
        if ret:
            decoded_objects = pyzbar.decode(frame)
            for obj in decoded_objects:
                self.process_qr_code(obj.data.decode('utf-8'))
                Clock.unschedule(self.update)
                cap.release()
                return
        cap.release()

    def process_qr_code(self, data):
        token = os.urandom(64).hex()
        user_id = "user123"
        guid = data  # GUID from the QR code

        response = requests.post('http://localhost:5000/validate_login', json={
            'guid': guid,
            'token': token,
            'user_id': user_id
        })

        if response.status_code == 200:
            self.label.text = "Login successful!"
            sio.emit('user_token', {'user_id': user_id, 'token': token})  # Emit user_token event
        else:
            self.label.text = "Error during login."

    @sio.event
    def connect(self):
        print("Connected to server")

    @sio.event
    def disconnect(self):
        print("Disconnected from server")

    @sio.on('token_ack')
    def handle_token_ack(data):
        print("Server acknowledged token: ", data['message'])

    @sio.on('token_error')
    def handle_token_error(data):
        print("Error from server: ", data['message'])


if __name__ == '__main__':
    QRScannerApp().run()
