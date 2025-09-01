# -*- coding: utf-8 -*-
"""
服务层模块
统一的业务逻辑处理
"""

# 导出主要服务
from .database_service import DatabaseService, init_database_service
from .error_handler import APIError, ValidationError, PermissionError, NotFoundError, api_response, error_handler, init_error_handlers

# 导出数据库管理模块
from .db_connection_manager import DBConnectionManager, connection_manager
from .db_table_manager import DBTableManager, table_manager
from .db_data_manager import DBDataManager, data_manager

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
    'DBConnectionManager',
    'connection_manager',
    'DBTableManager', 
    'table_manager',
    'DBDataManager',
    'data_manager'
]