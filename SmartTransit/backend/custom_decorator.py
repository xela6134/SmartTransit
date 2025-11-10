from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

# Allows routes to be only accessible for admins
def admin_only():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims["is_admin"] and not claims["is_driver"]:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Admins only!"), 403
        return decorator
    return wrapper

# Allows routes to be only accessible for admins & users
def admin_user_only():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims["is_driver"]:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Admins and Users only!"), 403
        return decorator
    return wrapper

# Allows routes to be only accessible for users
def user_only():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims["is_admin"] and not claims["is_driver"]:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Users only!"), 403
        return decorator
    return wrapper

# Allows routes to be only accessible for drivers
def driver_only():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims["is_admin"] and claims["is_driver"]:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Drivers only!"), 403
        return decorator
    return wrapper
