# -*- coding: utf-8 -*-
"""
数据库服务层
统一管理数据库连接和事务
"""
import sqlite3
from contextlib import contextmanager
from flask import g, current_app
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """统一的数据库服务"""
    
    @staticmethod
    def get_db():
        """获取数据库连接"""
        if 'db_manager' not in g:
            g.db_manager = DatabaseManager()
            if not g.db_manager.connect():
                logger.error("数据库连接失败")
                raise Exception('数据库连接失败')
            # 检查连接是否成功建立
            if g.db_manager.conn is not None:
                g.db_manager.conn.row_factory = sqlite3.Row
            else:
                logger.error("数据库连接对象为空")
                raise Exception('数据库连接对象为空')
        return g.db_manager.conn
    
    @staticmethod
    def close_db(error=None):
        """关闭数据库连接"""
        db_manager = g.pop('db_manager', None)
        if db_manager is not None:
            db_manager.disconnect()
    
    @staticmethod
    @contextmanager
    def get_db_manager():
        """获取数据库管理器的上下文管理器"""
        db_manager = DatabaseManager()
        try:
            if not db_manager.connect():
                raise Exception('数据库连接失败')
            yield db_manager
        except Exception as e:
            if db_manager.conn:
                db_manager.conn.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            db_manager.disconnect()
    
    @staticmethod
    @contextmanager
    def transaction():
        """数据库事务管理器"""
        conn = DatabaseService.get_db()
        if conn is None:
            logger.error("数据库连接为空，无法开启事务")
            raise Exception('数据库连接为空，无法开启事务')
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"事务回滚: {str(e)}")
            raise

def init_database_service(app):
    """初始化数据库服务"""
    app.teardown_appcontext(DatabaseService.close_db)