# QR Code Verification Project

## Overview
This project is designed to provide a comprehensive solution for QR code verification. It includes a web application, a mobile application, and a server-side script to handle various functionalities related to QR code generation and verification.

## Files

### `app.py`
This file contains the main web application built using Flask. It provides the following functionalities:
- It's the web interface for the users to continue their work from mobile
- Renders HTML templates for the web interface.
- Ensures session is valid (time limit being 15 minutes)

### `mobile_app.py`
This file contains the mobile application logic built using Kivy. It provides the following functionalities:
- Scans QR codes using the device's camera.
- Sends scanned QR code data to the server for verification.
- Creates a unique token at the time of QR scanning for any future API calls.
- Displays the verification result to the user.

### `server1.py`
This file contains the server-side logic for handling QR code verification requests. It provides the following functionalities:
- Receives QR code data from the mobile application.
- Verifies the QR code data and stores the token generated the mobile phone, to associate the next API calls with user.
- Sends the verification result back to the mobile application.

## Getting Started
To get started with this project, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/CH-Sampath/QR_code_verification.git
   cd QR_code_verification
   pip install -r requirements.txt
   python server1.py
   python app.py
   python mobile_app.py
   ```

