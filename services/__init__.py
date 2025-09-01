# -*- coding: utf-8 -*-
"""
服务层模块
统一的业务逻辑处理
"""

# 导出主要服务
from .database_service import DatabaseService, init_database_service
from .error_handler import APIError, ValidationError, PermissionError, NotFoundError, api_response, error_handler, init_error_handlers
from .permission_service import PermissionService, require_role, require_permission, admin_required

__all__ = [
    'DatabaseService',
    'init_database_service', 
    'APIError',
    'ValidationError',
    'PermissionError', 
    'NotFoundError',
    'api_response',
    'error_handler',
    'init_error_handlers',
    'PermissionService',
    'require_role',
    'require_permission',
    'admin_required'
]