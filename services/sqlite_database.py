"""
SQLite数据库具体实现模块
实现DatabaseInterface接口，提供SQLite数据库操作功能
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from .database_interface import DatabaseInterface, ConnectionError, QueryError, TransactionError, TableError

logger = logging.getLogger(__name__)


class SQLiteDatabase(DatabaseInterface):
    """SQLite数据库实现类"""
    
    def __init__(self, database_path: str):
        """
        初始化SQLite数据库连接
        
        Args:
            database_path (str): 数据库文件路径
        """
        self.database_path = database_path
        self.connection: Optional[sqlite3.Connection] = None
        self.in_transaction = False
    
    def connect(self) -> bool:
        """
        连接到SQLite数据库
        
        Returns:
            bool: 连接成功返回True，失败返回False
        """
        try:
            # 确保数据库文件目录存在
            db_path = Path(self.database_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.connection = sqlite3.connect(self.database_path)
            # 设置行工厂以返回字典格式的结果
            self.connection.row_factory = sqlite3.Row
            # 启用外键约束
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            logger.info(f"成功连接到SQLite数据库: {self.database_path}")
            return True
            
        except sqlite3.Error as e:
            error_msg = f"连接SQLite数据库失败: {e}"
            logger.error(error_msg)
            raise ConnectionError(error_msg, e)
    
    def disconnect(self) -> None:
        """
        断开SQLite数据库连接
        """
        try:
            if self.connection:
                if self.in_transaction:
                    self.rollback_transaction()
                self.connection.close()
                self.connection = None
                logger.info("已断开SQLite数据库连接")
        except sqlite3.Error as e:
            error_msg = f"断开SQLite数据库连接失败: {e}"
            logger.error(error_msg)
            raise ConnectionError(error_msg, e)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict]]:
        """
        执行SQL查询操作
        
        Args:
            query (str): SQL查询语句
            params (Optional[tuple]): 查询参数
            
        Returns:
            Optional[List[Dict]]: 查询结果列表，失败返回None
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 将结果转换为字典列表
            results = []
            for row in cursor.fetchall():
                results.append(dict(row))
            
            cursor.close()
            return results
            
        except sqlite3.Error as e:
            error_msg = f"执行查询失败: {e}\nSQL: {query}\n参数: {params}"
            logger.error(error_msg)
            raise QueryError(error_msg, e)
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> Optional[int]:
        """
        执行SQL更新操作
        
        Args:
            query (str): SQL更新语句
            params (Optional[tuple]): 更新参数
            
        Returns:
            Optional[int]: 受影响的行数，失败返回None
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            affected_rows = cursor.rowcount
            cursor.close()
            
            return affected_rows
            
        except sqlite3.Error as e:
            error_msg = f"执行更新失败: {e}\nSQL: {query}\n参数: {params}"
            logger.error(error_msg)
            raise QueryError(error_msg, e)
    
    def begin_transaction(self) -> bool:
        """
        开始事务
        
        Returns:
            bool: 开始事务成功返回True，失败返回False
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            self.connection.execute("BEGIN TRANSACTION")
            self.in_transaction = True
            logger.debug("事务开始")
            return True
            
        except sqlite3.Error as e:
            error_msg = f"开始事务失败: {e}"
            logger.error(error_msg)
            raise TransactionError(error_msg, e)
    
    def commit_transaction(self) -> bool:
        """
        提交事务
        
        Returns:
            bool: 提交成功返回True，失败返回False
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            self.connection.commit()
            self.in_transaction = False
            logger.debug("事务已提交")
            return True
            
        except sqlite3.Error as e:
            error_msg = f"提交事务失败: {e}"
            logger.error(error_msg)
            raise TransactionError(error_msg, e)
    
    def rollback_transaction(self) -> bool:
        """
        回滚事务
        
        Returns:
            bool: 回滚成功返回True，失败返回False
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            self.connection.rollback()
            self.in_transaction = False
            logger.debug("事务已回滚")
            return True
            
        except sqlite3.Error as e:
            error_msg = f"回滚事务失败: {e}"
            logger.error(error_msg)
            raise TransactionError(error_msg, e)
    
    def get_lastrowid(self) -> Optional[int]:
        """
        获取最后插入行的ID
        
        Returns:
            Optional[int]: 最后插入行的ID，失败返回None
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return result[0]
            return None
            
        except sqlite3.Error as e:
            error_msg = f"获取最后插入行ID失败: {e}"
            logger.error(error_msg)
            raise QueryError(error_msg, e)
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name (str): 表名
            
        Returns:
            bool: 表存在返回True，不存在返回False
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """
            
            result = self.execute_query(query, (table_name,))
            return bool(result)
            
        except sqlite3.Error as e:
            error_msg = f"检查表存在失败: {e}"
            logger.error(error_msg)
            raise TableError(error_msg, e)
    
    def get_table_columns(self, table_name: str) -> Optional[List[Dict]]:
        """
        获取表的列信息
        
        Args:
            table_name (str): 表名
            
        Returns:
            Optional[List[Dict]]: 列信息列表，失败返回None
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(query)
            return result
            
        except sqlite3.Error as e:
            error_msg = f"获取表列信息失败: {e}"
            logger.error(error_msg)
            raise TableError(error_msg, e)
    
    def list_tables(self) -> Optional[List[str]]:
        """
        列出所有表名
        
        Returns:
            Optional[List[str]]: 表名列表，失败返回None
        """
        if not self.connection:
            raise ConnectionError("数据库未连接")
        
        try:
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            
            result = self.execute_query(query)
            tables = [row['name'] for row in result] if result else []
            return tables
            
        except sqlite3.Error as e:
            error_msg = f"列出表名失败: {e}"
            logger.error(error_msg)
            raise TableError(error_msg, e)
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.disconnect()
    
    def __del__(self):
        """
        析构函数，确保连接被关闭
        """
        try:
            if self.connection:
                self.disconnect()
        except:
            pass