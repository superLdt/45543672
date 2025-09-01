# -*- coding: utf-8 -*-
"""
权限管理服务
统一处理用户权限验证
"""
from functools import wraps
from flask import session, current_app
from flask_login import current_user
from services.error_handler import PermissionError
import logging

logger = logging.getLogger(__name__)

class PermissionService:
    """权限服务类"""
    
    @staticmethod
    def check_role(required_roles):
        """检查用户角色"""
        if not current_user.is_authenticated:
            raise PermissionError("用户未登录")
        
        user_roles = current_user.roles if hasattr(current_user, 'roles') else []
        user_role = user_roles[0] if user_roles else None
        
        if not user_role:
            raise PermissionError("用户无角色权限")
        
        if isinstance(required_roles, str):
            required_roles = [required_roles]
        
        if user_role not in required_roles and '超级管理员' not in user_roles:
            raise PermissionError(f"需要角色权限: {', '.join(required_roles)}")
        
        return True
    
    @staticmethod
    def check_module_permission(module_name, action='view'):
        """检查模块权限"""
        if not current_user.is_authenticated:
            raise PermissionError("用户未登录")
        
        # 超级管理员拥有所有权限
        if hasattr(current_user, 'roles') and '超级管理员' in current_user.roles:
            return True
        
        # TODO: 实现具体的模块权限检查逻辑
        # 这里需要查询数据库中的权限配置
        return True
    
    @staticmethod
    def get_user_permissions():
        """获取当前用户的权限列表"""
        if not current_user.is_authenticated:
            return []
        
        # TODO: 从数据库查询用户权限
        return []

def require_role(roles):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            PermissionService.check_role(roles)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(module_name, action='view'):
    """模块权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            PermissionService.check_module_permission(module_name, action)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        PermissionService.check_role(['管理员', '超级管理员'])
        return f(*args, **kwargs)
    return decorated_function