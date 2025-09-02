"""
数据库连接管理模块
负责数据库连接的创建、维护和释放，提供连接池功能
"""
import threading
from typing import Optional, Dict, Any
from .database_interface import DatabaseInterface, DatabaseError, ConnectionError
from .db_factory import DatabaseFactory


class DBConnectionManager:
    """数据库连接管理器类"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._connections = {}
                cls._instance._config = None
        return cls._instance
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        初始化连接管理器
        
        Args:
            config: 数据库配置字典
        """
        self._config = config
    
    def get_connection(self, database_type: str = "sqlite") -> DatabaseInterface:
        """
        获取数据库连接
        
        Args:
            database_type: 数据库类型，默认为sqlite
            
        Returns:
            DatabaseInterface: 数据库连接实例
            
        Raises:
            ConnectionError: 连接创建失败时抛出
        """
        if self._config is None:
            raise ConnectionError("连接管理器未初始化，请先调用initialize方法")
        
        # 使用线程ID作为连接键，确保每个线程有自己的连接
        thread_key = f"{database_type}_{threading.get_ident()}"
        
        if thread_key not in self._connections:
            try:
                # 创建新的数据库连接
                db_config = self._config
                db_instance = DatabaseFactory.create_database(db_config)
                db_instance.connect()
                self._connections[thread_key] = db_instance
            except Exception as e:
                raise ConnectionError(f"创建数据库连接失败: {str(e)}")
        
        return self._connections[thread_key]
    
    def release_connection(self, database_type: str = "sqlite") -> None:
        """
        释放数据库连接
        
        Args:
            database_type: 数据库类型，默认为sqlite
        """
        thread_key = f"{database_type}_{threading.get_ident()}"
        
        if thread_key in self._connections:
            try:
                self._connections[thread_key].disconnect()
                del self._connections[thread_key]
            except Exception:
                # 忽略断开连接时的异常
                pass
    
    def release_all_connections(self) -> None:
        """释放所有数据库连接"""
        for thread_key, connection in list(self._connections.items()):
            try:
                connection.disconnect()
            except Exception:
                # 忽略断开连接时的异常
                pass
        self._connections.clear()
    
    def is_connected(self, database_type: str = "sqlite") -> bool:
        """
        检查是否已建立连接
        
        Args:
            database_type: 数据库类型，默认为sqlite
            
        Returns:
            bool: 连接状态
        """
        thread_key = f"{database_type}_{threading.get_ident()}"
        return thread_key in self._connections
    
    def get_connection_count(self) -> int:
        """
        获取当前活跃连接数量
        
        Returns:
            int: 连接数量
        """
        return len(self._connections)


# 全局连接管理器实例
connection_manager = DBConnectionManager()