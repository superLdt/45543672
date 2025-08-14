from functools import wraps
from flask import jsonify, session

def require_role(allowed_roles):
    """权限验证装饰器 - 单一角色版本"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否登录
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': '未登录或权限不足'
                    }
                }), 401
            
            # 获取用户角色（单一角色）
            user_role = session.get('user_role')
            if not user_role:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': '用户角色信息缺失'
                    }
                }), 403
            
            # 检查用户角色是否在允许的角色列表中
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