"""
数据库工厂模块
根据配置创建相应的数据库实例
"""

import logging
from typing import Optional, Dict, Any
from .database_interface import DatabaseInterface
from .sqlite_database import SQLiteDatabase

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """数据库工厂类"""
    
    @staticmethod
    def create_database(config: Dict[str, Any]) -> DatabaseInterface:
        """
        根据配置创建数据库实例
        
        Args:
            config (Dict[str, Any]): 数据库配置
            
        Returns:
            DatabaseInterface: 数据库实例
            
        Raises:
            ValueError: 不支持的数据库类型
        """
        db_type = config.get('type', 'sqlite').lower()
        
        if db_type == 'sqlite':
            return DatabaseFactory._create_sqlite_database(config)
        elif db_type == 'mysql':
            return DatabaseFactory._create_mysql_database(config)
        elif db_type == 'postgresql':
            return DatabaseFactory._create_postgresql_database(config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    @staticmethod
    def _create_sqlite_database(config: Dict[str, Any]) -> SQLiteDatabase:
        """
        创建SQLite数据库实例
        
        Args:
            config (Dict[str, Any]): SQLite数据库配置
            
        Returns:
            SQLiteDatabase: SQLite数据库实例
        """
        sqlite_config = config.get('sqlite', {})
        database_path = sqlite_config.get('database', 'database.db')
        
        logger.info(f"创建SQLite数据库实例，路径: {database_path}")
        return SQLiteDatabase(database_path)
    
    @staticmethod
    def _create_mysql_database(config: Dict[str, Any]) -> DatabaseInterface:
        """
        创建MySQL数据库实例（预留实现）
        
        Args:
            config (Dict[str, Any]): MySQL数据库配置
            
        Returns:
            DatabaseInterface: MySQL数据库实例
            
        Raises:
            NotImplementedError: MySQL支持尚未实现
        """
        mysql_config = config.get('mysql', {})
        
        logger.warning("MySQL数据库支持尚未实现，创建空实例")
        # 返回一个空的数据库接口实例
        # 实际实现时需要创建MySQLDatabase类
        return DatabaseFactory._create_empty_database('mysql')
    
    @staticmethod
    def _create_postgresql_database(config: Dict[str, Any]) -> DatabaseInterface:
        """
        创建PostgreSQL数据库实例（预留实现）
        
        Args:
            config (Dict[str, Any]): PostgreSQL数据库配置
            
        Returns:
            DatabaseInterface: PostgreSQL数据库实例
            
        Raises:
            NotImplementedError: PostgreSQL支持尚未实现
        """
        postgresql_config = config.get('postgresql', {})
        
        logger.warning("PostgreSQL数据库支持尚未实现，创建空实例")
        # 返回一个空的数据库接口实例
        # 实际实现时需要创建PostgreSQLDatabase类
        return DatabaseFactory._create_empty_database('postgresql')
    
    @staticmethod
    def _create_empty_database(db_type: str) -> DatabaseInterface:
        """
        创建空的数据库实例（用于未实现的数据库类型）
        
        Args:
            db_type (str): 数据库类型
            
        Returns:
            DatabaseInterface: 空的数据库实例
            
        Raises:
            NotImplementedError: 数据库类型未实现
        """
        class EmptyDatabase(DatabaseInterface):
            """空的数据库实现类"""
            
            def __init__(self, db_type: str):
                self.db_type = db_type
            
            def connect(self) -> bool:
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def disconnect(self) -> None:
                pass
            
            def execute_query(self, query: str, params: Optional[tuple] = None):
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def execute_update(self, query: str, params: Optional[tuple] = None):
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def begin_transaction(self) -> bool:
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def commit_transaction(self) -> bool:
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def rollback_transaction(self) -> bool:
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def get_lastrowid(self):
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def table_exists(self, table_name: str) -> bool:
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def get_table_columns(self, table_name: str):
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
            
            def list_tables(self):
                raise NotImplementedError(f"{self.db_type}数据库支持尚未实现")
        
        return EmptyDatabase(db_type)
    
    @staticmethod
    def get_available_database_types() -> list:
        """
        获取支持的数据库类型列表
        
        Returns:
            list: 支持的数据库类型列表
        """
        return ['sqlite', 'mysql', 'postgresql']
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        验证数据库配置是否有效
        
        Args:
            config (Dict[str, Any]): 数据库配置
            
        Returns:
            bool: 配置有效返回True，否则返回False
        """
        if not config:
            logger.error("数据库配置为空")
            return False
        
        db_type = config.get('type')
        if not db_type:
            logger.error("数据库类型未指定")
            return False
        
        if db_type not in DatabaseFactory.get_available_database_types():
            logger.error(f"不支持的数据库类型: {db_type}")
            return False
        
        # 验证特定数据库类型的配置
        if db_type == 'sqlite':
            sqlite_config = config.get('sqlite', {})
            if not sqlite_config.get('database'):
                logger.error("SQLite数据库路径未指定")
                return False
        
        elif db_type == 'mysql':
            mysql_config = config.get('mysql', {})
            required_fields = ['host', 'user', 'password', 'database']
            for field in required_fields:
                if not mysql_config.get(field):
                    logger.error(f"MySQL配置缺少必要字段: {field}")
                    return False
        
        elif db_type == 'postgresql':
            postgresql_config = config.get('postgresql', {})
            required_fields = ['host', 'user', 'password', 'database']
            for field in required_fields:
                if not postgresql_config.get(field):
                    logger.error(f"PostgreSQL配置缺少必要字段: {field}")
                    return False
        
        logger.info(f"数据库配置验证通过，类型: {db_type}")
        return True