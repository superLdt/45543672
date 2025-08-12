from functools import wraps
from flask import jsonify, session

def require_role(allowed_roles):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': '未登录或权限不足'
                    }
                }), 401
            
            user_role = session['user_role']
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': f'需要权限: {allowed_roles}, 当前权限: {user_role}'
                    }
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def create_response(success=True, data=None, error=None):
    """创建统一响应格式"""
    response = {'success': success}
    if data is not None:
        response['data'] = data
    if error is not None:
        response['error'] = error
    return jsonify(response)