# -*- coding: utf-8 -*-
"""
错误处理中间件
统一处理API错误和异常
"""
import logging
from flask import jsonify, request
from functools import wraps

logger = logging.getLogger(__name__)

class APIError(Exception):
    """API异常基类"""
    def __init__(self, message, code=500, data=None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)

class ValidationError(APIError):
    """数据验证错误"""
    def __init__(self, message, data=None):
        super().__init__(message, 400, data)

class PermissionError(APIError):
    """权限错误"""
    def __init__(self, message="权限不足"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    """资源不存在错误"""
    def __init__(self, message="资源不存在"):
        super().__init__(message, 404)

def handle_api_error(error):
    """API错误处理器"""
    logger.error(f"API错误: {error.message}", exc_info=True)
    
    response = {
        'success': False,
        'error': {
            'code': error.code,
            'message': error.message
        }
    }
    
    if error.data:
        response['error']['data'] = error.data
    
    return jsonify(response), error.code

def handle_unexpected_error(error):
    """未知错误处理器"""
    logger.error(f"未处理的错误: {str(error)}", exc_info=True)
    
    return jsonify({
        'success': False,
        'error': {
            'code': 500,
            'message': '服务器内部错误'
        }
    }), 500

def api_response(success=True, data=None, error=None, code=200):
    """统一API响应格式"""
    response = {'success': success}
    
    if success and data is not None:
        response['data'] = data
    elif not success and error:
        response['error'] = error
    
    return jsonify(response), code

def error_handler(f):
    """错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return handle_api_error(e)
        except Exception as e:
            return handle_unexpected_error(e)
    return decorated_function

def init_error_handlers(app):
    """初始化错误处理器"""
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(500, handle_unexpected_error)