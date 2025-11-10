from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_socketio import SocketIO
import os

# Import blueprints
# from backend.auth import auth_bp, register_jwt_blocklist_loader, close_db_connection
# from backend.location import location_bp
# from backend.booking import booking_bp

from auth import auth_bp, register_jwt_blocklist_loader, close_db_connection
from location import location_bp
from booking import booking_bp
from settings import settings_bp
from driver import driver_bp
from payment import payment_bp
from report_generate import route_gen_bp
from admin import admin_bp
from route_optimisation import route_op_bp

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
# Secret key for JWT signing
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 15)))

# Q. what are these `dev only` and `prod only`?
# A. dev only: local dev works on HTTP which is terrible in terms of security
#              so we configure the cookies and connections to have terrible security
#
#   prod only: we now communicate on HTTPS, and it is a secure protocol
#              so the cookies shouldn't be insecure purposely

app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'
app.config['JWT_COOKIE_SECURE'] = False           # dev only      
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'         # dev only      
# app.config['JWT_COOKIE_SECURE'] = True          # prod only
# app.config['JWT_COOKIE_SAMESITE'] = "None"      # prod only
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = True


# --- Extension Initialization ---

# Bcrypt for password hashing
bcrypt = Bcrypt(app)

# JWTManager for handling JWT operations
jwt = JWTManager(app)

# This connects the function defined in auth.py (check_if_token_revoked)
# it tells Flask-JWT-Extended to call this function on every request that uses a JWT
register_jwt_blocklist_loader(jwt)

# This ensures close_db_connection is called automatically when the application is done with it
app.teardown_appcontext(close_db_connection)


# TODO: Change origin according to React Native stuff
CORS(app, origins=["http://localhost:3000", "http://localhost:8081", "http://10.0.2.2:8000"], supports_credentials=True)

# Register 'blueprints'
# (which are modularised code)
# Check auth.py
app.register_blueprint(auth_bp)
app.register_blueprint(location_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(driver_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(route_gen_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(route_op_bp)
if __name__ == '__main__':
    socketio.run(app,
                 debug=True,
                 host='0.0.0.0',
                 port=int(os.environ.get('PORT', 8000)),
                 allow_unsafe_werkzeug=True)
