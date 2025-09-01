"""
表结构管理模块
负责数据库表结构的创建、验证、维护和迁移
"""
from typing import Dict, List, Any, Optional
from .database_interface import DatabaseInterface, DatabaseError
from .db_connection_manager import connection_manager


class DBTableManager:
    """数据库表结构管理器类"""
    
    def __init__(self, database_type: str = "sqlite"):
        """
        初始化表结构管理器
        
        Args:
            database_type: 数据库类型，默认为sqlite
        """
        self.database_type = database_type
        self._table_definitions = self._load_table_definitions()
    
    def _load_table_definitions(self) -> Dict[str, str]:
        """
        加载表结构定义
        
        Returns:
            Dict[str, str]: 表名到建表语句的映射
        """
        return {
            "companies": """
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    contact_person TEXT,
                    phone TEXT,
                    address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "vehicles": """
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    license_plate TEXT NOT NULL UNIQUE,
                    vehicle_type TEXT,
                    capacity REAL,
                    status TEXT DEFAULT 'available',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """,
            "drivers": """
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    license_number TEXT,
                    status TEXT DEFAULT 'available',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """,
            "orders": """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT NOT NULL UNIQUE,
                    company_id INTEGER NOT NULL,
                    vehicle_id INTEGER,
                    driver_id INTEGER,
                    pickup_location TEXT,
                    delivery_location TEXT,
                    cargo_description TEXT,
                    weight REAL,
                    status TEXT DEFAULT 'pending',
                    scheduled_time DATETIME,
                    completed_time DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
                    FOREIGN KEY (driver_id) REFERENCES drivers (id)
                )
            """,
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    role TEXT DEFAULT 'user',
                    company_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """
        }
    
    def create_tables(self) -> bool:
        """
        创建所有表结构
        
        Returns:
            bool: 是否创建成功
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            for table_name, create_sql in self._table_definitions.items():
                db.execute_query(create_sql)
                print(f"表 {table_name} 创建成功")
            
            return True
        except DatabaseError as e:
            print(f"创建表结构失败: {str(e)}")
            return False
        except Exception as e:
            print(f"创建表结构时发生未知错误: {str(e)}")
            return False
    
    def drop_tables(self) -> bool:
        """
        删除所有表结构
        
        Returns:
            bool: 是否删除成功
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            # 获取所有表名
            tables = self.get_existing_tables()
            
            for table_name in tables:
                drop_sql = f"DROP TABLE IF EXISTS {table_name}"
                db.execute_query(drop_sql)
                print(f"表 {table_name} 删除成功")
            
            return True
        except DatabaseError as e:
            print(f"删除表结构失败: {str(e)}")
            return False
        except Exception as e:
            print(f"删除表结构时发生未知错误: {str(e)}")
            return False
    
    def get_existing_tables(self) -> List[str]:
        """
        获取数据库中现有的所有表名
        
        Returns:
            List[str]: 表名列表
        """
        try:
            db = connection_manager.get_connection(self.database_type)
            
            if self.database_type == "sqlite":
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            elif self.database_type in ["mysql", "postgresql"]:
                query = "SHOW TABLES"
            else:
                return []
            
            result = db.execute_query(query)
            tables = [row[0] for row in result] if result else []
            
            # 过滤掉系统表
            system_tables = ["sqlite_sequence", "spatial_ref_sys"]
            return [table for table in tables if table not in system_tables]
        except Exception:
            return []
    
    def validate_table_structure(self, table_name: str) -> bool:
        """
        验证表结构是否符合预期
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 表结构是否有效
        """
        if table_name not in self._table_definitions:
            print(f"未知表名: {table_name}")
            return False
        
        existing_tables = self.get_existing_tables()
        return table_name in existing_tables
    
    def validate_all_tables(self) -> Dict[str, bool]:
        """
        验证所有表结构
        
        Returns:
            Dict[str, bool]: 表名到验证结果的映射
        """
        results = {}
        existing_tables = self.get_existing_tables()
        
        for table_name in self._table_definitions.keys():
            results[table_name] = table_name in existing_tables
        
        return results
    
    def get_table_definition(self, table_name: str) -> Optional[str]:
        """
        获取表的定义语句
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[str]: 建表语句，如果表不存在返回None
        """
        return self._table_definitions.get(table_name)
    
    def add_table_definition(self, table_name: str, create_sql: str) -> None:
        """
        添加新的表定义
        
        Args:
            table_name: 表名
            create_sql: 建表语句
        """
        self._table_definitions[table_name] = create_sql
    
    def remove_table_definition(self, table_name: str) -> bool:
        """
        移除表定义
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 是否移除成功
        """
        if table_name in self._table_definitions:
            del self._table_definitions[table_name]
            return True
        return False


# 全局表管理器实例
table_manager = DBTableManager()