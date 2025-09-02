"""
数据操作管理模块
负责数据的增删改查操作，提供统一的数据访问接口
"""
from typing import Dict, List, Any, Optional, Union
from .database_interface import DatabaseInterface, DatabaseError
from .db_connection_manager import connection_manager


class DBDataManager:
    """数据操作管理器类"""
    
    def __init__(self, database_type: str = "sqlite"):
        """
        初始化数据操作管理器
        
        Args:
            database_type: 数据库类型，默认为sqlite
        """
        self.database_type = database_type
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """
        插入数据
        
        Args:
            table_name: 表名
            data: 要插入的数据字典
            
        Returns:
            Optional[int]: 插入行的ID，失败时返回None
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 构建插入语句
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            # 执行插入操作
            result = db.execute_query(sql, values)
            
            # 获取最后插入的ID
            if self.database_type == "sqlite":
                last_id = db.get_lastrowid()
                return last_id
            else:
                return result
        except DatabaseError as e:
            print(f"插入数据失败: {str(e)}")
            return None
    
    def update(self, table_name: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """
        更新数据
        
        Args:
            table_name: 表名
            data: 要更新的数据字典
            where: 更新条件字典
            
        Returns:
            int: 受影响的行数
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 构建SET子句
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            
            # 构建WHERE子句
            where_clause = ' AND '.join([f"{key} = ?" for key in where.keys()])
            
            # 合并参数值
            values = list(data.values()) + list(where.values())
            
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            # 执行更新操作
            result = db.execute_update(sql, values)
            return result
        except DatabaseError as e:
            print(f"更新数据失败: {str(e)}")
            return 0
    
    def delete(self, table_name: str, where: Dict[str, Any]) -> int:
        """
        删除数据
        
        Args:
            table_name: 表名
            where: 删除条件字典
            
        Returns:
            int: 受影响的行数
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 构建WHERE子句
            where_clause = ' AND '.join([f"{key} = ?" for key in where.keys()])
            values = list(where.values())
            
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            # 执行删除操作
            result = db.execute_update(sql, values)
            return result
        except DatabaseError as e:
            print(f"删除数据失败: {str(e)}")
            return 0
    
    def select(self, table_name: str, 
               columns: List[str] = None, 
               where: Dict[str, Any] = None,
               order_by: str = None,
               limit: int = None,
               offset: int = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            table_name: 表名
            columns: 要查询的列名列表，None表示所有列
            where: 查询条件字典
            order_by: 排序字段
            limit: 限制返回行数
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 构建SELECT子句
            if columns is None:
                select_clause = "*"
            else:
                select_clause = ', '.join(columns)
            
            # 构建WHERE子句
            where_clause = ""
            values = []
            if where:
                where_clause = ' AND '.join([f"{key} = ?" for key in where.keys()])
                values = list(where.values())
            
            # 构建SQL语句
            sql = f"SELECT {select_clause} FROM {table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit is not None:
                sql += f" LIMIT {limit}"
            if offset is not None:
                sql += f" OFFSET {offset}"
            
            # 执行查询操作
            result = db.execute_query(sql, values)
            
            # 转换为字典列表
            if result and len(result) > 0:
                if columns is None:
                    # 获取所有列名
                    column_names = self._get_column_names(table_name)
                else:
                    column_names = columns
                
                return [dict(zip(column_names, row)) for row in result]
            else:
                return []
        except DatabaseError as e:
            print(f"查询数据失败: {str(e)}")
            return []
    
    def _get_column_names(self, table_name: str) -> List[str]:
        """
        获取表的列名
        
        Args:
            table_name: 表名
            
        Returns:
            List[str]: 列名列表
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            if self.database_type == "sqlite":
                sql = f"PRAGMA table_info({table_name})"
                result = db.execute_query(sql)
                if result and len(result) > 0:
                    # 处理字典格式的结果
                    if isinstance(result[0], dict):
                        return [row['name'] for row in result]
                    else:
                        # 处理元组格式的结果
                        return [row[1] for row in result]
                return []
            else:
                # 对于其他数据库类型，返回空列表
                return []
        except Exception:
            return []
    
    def count(self, table_name: str, where: Dict[str, Any] = None) -> int:
        """
        统计行数
        
        Args:
            table_name: 表名
            where: 统计条件字典
            
        Returns:
            int: 行数
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 构建WHERE子句
            where_clause = ""
            values = []
            if where:
                where_clause = ' AND '.join([f"{key} = ?" for key in where.keys()])
                values = list(where.values())
            
            sql = f"SELECT COUNT(*) FROM {table_name}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            
            result = db.execute_query(sql, values)
            if result and len(result) > 0:
                return list(result[0].values())[0] if isinstance(result[0], dict) else result[0][0]
            return 0
        except DatabaseError as e:
            print(f"统计行数失败: {str(e)}")
            return 0
    
    def execute_raw_query(self, sql: str, params: List[Any] = None) -> Any:
        """
        执行原始SQL查询
        
        Args:
            sql: SQL语句
            params: 参数列表
            
        Returns:
            Any: 查询结果
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            return db.execute_query(sql, params)
        except DatabaseError as e:
            print(f"执行原始查询失败: {str(e)}")
            return None
    
    def execute_raw_command(self, sql: str, params: List[Any] = None) -> int:
        """
        执行原始SQL命令
        
        Args:
            sql: SQL语句
            params: 参数列表
            
        Returns:
            int: 受影响的行数
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            return db.execute_update(sql, params)
        except DatabaseError as e:
            print(f"执行原始命令失败: {str(e)}")
            return 0
    
    def begin_transaction(self) -> bool:
        """
        开始事务
        
        Returns:
            bool: 是否成功开始事务
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            db.begin_transaction()
            return True
        except DatabaseError as e:
            print(f"开始事务失败: {str(e)}")
            return False
    
    def commit_transaction(self) -> bool:
        """
        提交事务
        
        Returns:
            bool: 是否成功提交事务
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            db.commit_transaction()
            return True
        except DatabaseError as e:
            print(f"提交事务失败: {str(e)}")
            return False
    
    def rollback_transaction(self) -> bool:
        """
        回滚事务
        
        Returns:
            bool: 是否成功回滚事务
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            db.rollback_transaction()
            return True
        except DatabaseError as e:
            print(f"回滚事务失败: {str(e)}")
            return False


# 全局数据管理器实例
data_manager = DBDataManager()