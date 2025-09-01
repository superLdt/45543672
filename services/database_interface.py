"""
数据库操作抽象接口模块
提供统一的数据库操作接口，支持多种数据库类型
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseInterface(ABC):
    """数据库操作抽象接口类"""
    
    @abstractmethod
    def connect(self) -> bool:
        """
        连接到数据库
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        pass
    
    @abstractmethod  
    def disconnect(self) -> None:
        """
        断开数据库连接
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict]]:
        """
        执行查询操作
        
        Args:
            query (str): SQL查询语句
            params (Optional[tuple]): 查询参数
            
        Returns:
            Optional[List[Dict]]: 查询结果列表，失败返回None
        """
        pass
    
    @abstractmethod
    def execute_update(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """
        执行更新操作（INSERT/UPDATE/DELETE）
        
        Args:
            query (str): SQL更新语句
            params (Optional[tuple]): 更新参数
            
        Returns:
            Optional[int]: 受影响的行数，失败返回None
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> bool:
        """
        开始事务
        
        Returns:
            bool: 开始事务成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def commit_transaction(self) -> bool:
        """
        提交事务
        
        Returns:
            bool: 提交成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def rollback_transaction(self) -> bool:
        """
        回滚事务
        
        Returns:
            bool: 回滚成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def get_lastrowid(self) -> Optional[int]:
        """
        获取最后插入行的ID
        
        Returns:
            Optional[int]: 最后插入行的ID，失败返回None
        """
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name (str): 表名
            
        Returns:
            bool: 表存在返回True，不存在返回False
        """
        pass
    
    @abstractmethod
    def get_table_columns(self, table_name: str) -> Optional[List[Dict]]:
        """
        获取表的列信息
        
        Args:
            table_name (str): 表名
            
        Returns:
            Optional[List[Dict]]: 列信息列表，失败返回None
        """
        pass
    
    @abstractmethod
    def list_tables(self) -> Optional[List[str]]:
        """
        列出所有表名
        
        Returns:
            Optional[List[str]]: 表名列表，失败返回None
        """
        pass


class DatabaseError(Exception):
    """数据库操作异常类"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """
        初始化数据库异常
        
        Args:
            message (str): 错误消息
            original_error (Optional[Exception]): 原始异常
        """
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """
        返回异常字符串表示
        
        Returns:
            str: 异常信息
        """
        if self.original_error:
            return f"{self.message} (原始错误: {self.original_error})"
        return self.message


class ConnectionError(DatabaseError):
    """数据库连接异常"""
    pass


class QueryError(DatabaseError):
    """数据库查询异常"""
    pass


class TransactionError(DatabaseError):
    """数据库事务异常"""
    pass


class TableError(DatabaseError):
    """数据库表操作异常"""
    pass