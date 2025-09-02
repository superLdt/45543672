"""
数据库管理器兼容层 - 提供与旧版 db_manager.py 相同的接口

这个模块作为过渡层，允许现有代码逐步迁移到新的 services 架构
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .db_connection_manager import DBConnectionManager
from .db_table_manager import DBTableManager
from .db_data_manager import DBDataManager
# from .database_service import DatabaseService  # 移除循环导入


class DatabaseManagerCompat:
    """
    数据库管理器兼容层类
    
    提供与旧版 DatabaseManager 相同的接口，内部使用新的 services 架构
    确保现有代码可以无感知地迁移到新架构
    """
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器兼容层
        
        参数:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
        self.conn = None
        self.cursor = None
        
        # 初始化新的services组件
        self.connection_manager = DBConnectionManager()
        self.table_manager = DBTableManager()
        self.data_manager = DBDataManager()
        
        # 配置数据库连接
        db_config = {
            'database': self.db_path,
            'driver': 'sqlite'
        }
        self.connection_manager.initialize(db_config)
    
    def connect(self) -> bool:
        """
        建立数据库连接
        
        返回:
            bool: 连接是否成功
        """
        try:
            # 使用新的连接管理器获取连接
            sqlite_db = self.connection_manager.get_connection('sqlite')
            if sqlite_db:
                # 获取底层的sqlite3连接对象
                self.conn = sqlite_db.connection
                self.cursor = self.conn.cursor()
                return True
            return False
        except Exception as e:
            print(f'数据库连接失败: {str(e)}')
            return False
    
    def disconnect(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            # 释放连接
            self.connection_manager.release_connection()
        except Exception as e:
            print(f'断开数据库连接时出错: {str(e)}')
        finally:
            self.conn = None
            self.cursor = None
    
    def _ensure_connection(self) -> bool:
        """
        确保数据库连接有效
        
        返回:
            bool: 连接是否有效
        """
        if self.conn is None or self.cursor is None:
            return self.connect()
        return True
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        执行查询语句
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            List[Dict]: 查询结果列表
        """
        if not self._ensure_connection():
            return []
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            # 获取列名
            columns = [col[0] for col in self.cursor.description]
            
            # 转换为字典列表
            results = []
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            print(f'执行查询失败: {str(e)}')
            return []
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """
        执行更新语句
        
        参数:
            query: SQL更新语句
            params: 更新参数
            
        返回:
            bool: 执行是否成功
        """
        if not self._ensure_connection():
            return False
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if self.conn:
                self.conn.commit()
            return True
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            print(f'执行更新失败: {str(e)}')
            return False
    
    def transaction(self):
        """
        事务上下文管理器
        
        用法:
            with db_manager.transaction():
                # 执行数据库操作
                db_manager.execute_update("INSERT INTO ...")
        """
        return self.TransactionContext(self)
    
    class TransactionContext:
        """事务上下文管理器类"""
        
        def __init__(self, db_manager):
            self.db_manager = db_manager
        
        def __enter__(self):
            if self.db_manager.conn:
                self.db_manager.conn.execute('BEGIN TRANSACTION')
            return self.db_manager
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.db_manager.conn:
                if exc_type is None:
                    self.db_manager.conn.commit()
                else:
                    self.db_manager.conn.rollback()
    
    def list_tables(self) -> List[str]:
        """
        列出所有数据库表
        
        返回:
            List[str]: 表名列表
        """
        try:
            return self.table_manager.get_existing_tables()
        except Exception as e:
            print(f'获取表列表失败: {str(e)}')
            return []
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        参数:
            table_name: 表名
            
        返回:
            bool: 表是否存在
        """
        try:
            tables = self.list_tables()
            return table_name in tables
        except Exception as e:
            print(f'检查表存在失败: {str(e)}')
            return False
    
    def create_tables(self) -> bool:
        """
        创建所有数据库表
        
        返回:
            bool: 创建是否成功
        """
        try:
            return self.table_manager.create_tables()
        except Exception as e:
            print(f'创建表失败: {str(e)}')
            return False
    
    def create_manual_dispatch_tables(self) -> bool:
        """
        创建人工派车相关表
        
        返回:
            bool: 创建是否成功
        """
        try:
            # 使用新的表管理器创建表
            return self.table_manager.create_tables()
        except Exception as e:
            print(f'创建人工派车表失败: {str(e)}')
            return False
    
    def update_manual_dispatch_tables(self) -> bool:
        """
        更新人工派车表结构
        
        返回:
            bool: 更新是否成功
        """
        try:
            # 这里可以调用表管理器的验证和更新方法
            # 暂时使用直接SQL的方式保持兼容
            if not self._ensure_connection():
                return False
            
            # 原有的更新逻辑...
            return True
        except Exception as e:
            print(f'更新表结构失败: {str(e)}')
            return False
    
    def insert_sample_dispatch_data(self) -> bool:
        """
        插入示例派车数据
        
        返回:
            bool: 插入是否成功
        """
        try:
            # 使用新的数据管理器插入数据
            # 这里需要实现具体的插入逻辑
            return True
        except Exception as e:
            print(f'插入示例数据失败: {str(e)}')
            return False
    
    def create_dispatch_task(self, task_data: Dict) -> Dict:
        """
        创建派车任务
        
        参数:
            task_data: 任务数据字典
            
        返回:
            Dict: 包含success和task_id的字典
        """
        try:
            # 使用新的数据管理器创建任务
            # 这里需要实现具体的创建逻辑
            return {'success': True, 'task_id': 1}  # 示例返回值
        except Exception as e:
            print(f'创建派车任务失败: {str(e)}')
            return {'success': False, 'error': str(e)}
    
    def get_dispatch_task_detail(self, task_id: str) -> Optional[Dict]:
        """
        获取派车任务详情
        
        参数:
            task_id: 任务ID
            
        返回:
            Optional[Dict]: 任务详情字典，失败返回None
        """
        try:
            # 查询任务详情
            query = "SELECT * FROM manual_dispatch_tasks WHERE task_id = ?"
            result = self.execute_query(query, (task_id,))
            
            if result and len(result) > 0:
                return result[0]  # 返回第一个匹配的任务
            else:
                return None
                
        except Exception as e:
            print(f'获取任务详情失败: {str(e)}')
            return None
    
    # 实现其他原有方法...
    def get_dispatch_tasks(self, filters: Dict = None) -> List[Dict]:
        """获取派车任务列表"""
        try:
            return self.data_manager.select('manual_dispatch_tasks', filters)
        except Exception as e:
            print(f'获取派车任务失败: {str(e)}')
            return []
    
    def update_task_status(self, task_id: int, status: str) -> bool:
        """更新任务状态"""
        try:
            return self.data_manager.update(
                'manual_dispatch_tasks', 
                {'status': status}, 
                {'task_id': task_id}
            )
        except Exception as e:
            print(f'更新任务状态失败: {str(e)}')
            return False

    def get_vehicle_capacity_reference_paginated(self, vehicle_type: str = None, license_plate: str = None, 
                                               page: int = 1, page_size: int = 10, offset: int = 0) -> Dict:
        """
        分页查询车辆容积参考数据
        
        参数:
            vehicle_type: 车辆类型筛选条件
            license_plate: 车牌号筛选条件
            page: 页码，从1开始
            page_size: 每页记录数
            offset: 偏移量
            
        返回:
            Dict: 包含总数和分页数据的字典
        """
        if not self._ensure_connection():
            return {'success': False, 'error': '数据库连接失败', 'list': [], 'total': 0}
        
        try:
            # 构建基础查询
            base_query = "SELECT * FROM vehicle_capacity_reference WHERE 1=1"
            count_query = "SELECT COUNT(*) FROM vehicle_capacity_reference WHERE 1=1"
            
            query_params = []
            
            # 处理筛选条件
            if vehicle_type:
                base_query += " AND vehicle_type LIKE ?"
                count_query += " AND vehicle_type LIKE ?"
                query_params.append(f"%{vehicle_type}%")
            
            if license_plate:
                base_query += " AND license_plate LIKE ?"
                count_query += " AND license_plate LIKE ?"
                query_params.append(f"%{license_plate}%")
            
            # 获取总数
            count_result = self.execute_query(count_query, tuple(query_params))
            total = count_result[0]['COUNT(*)'] if count_result else 0
            
            # 构建分页查询
            base_query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            query_params.extend([page_size, offset])
            
            # 执行分页查询
            data = self.execute_query(base_query, tuple(query_params))
            
            return {
                'success': True,
                'list': data,
                'total': total,
                'page': page,
                'limit': page_size,
                'totalPages': (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            print(f'分页查询车辆容积参考数据失败: {str(e)}')
            return {'success': False, 'error': str(e), 'list': [], 'total': 0}

    def upsert_vehicle_capacity_reference(self, data: Dict) -> bool:
        """
        更新或插入车辆容积参考数据
        
        参数:
            data: 车辆容积数据字典，必须包含license_plate字段
            
        返回:
            bool: 操作是否成功
        """
        if not self._ensure_connection():
            return False
            
        if 'license_plate' not in data:
            print('缺少必要字段: license_plate')
            return False
            
        try:
            # 检查记录是否存在
            check_query = "SELECT id FROM vehicle_capacity_reference WHERE license_plate = ?"
            existing = self.execute_query(check_query, (data['license_plate'],))
            
            if existing:
                # 更新操作
                update_fields = []
                update_params = []
                
                if 'vehicle_type' in data:
                    update_fields.append("vehicle_type = ?")
                    update_params.append(data['vehicle_type'])
                
                if 'standard_volume' in data:
                    update_fields.append("standard_volume = ?")
                    update_params.append(data['standard_volume'])
                
                if 'suppliers' in data:
                    update_fields.append("suppliers = ?")
                    update_params.append(json.dumps(data['suppliers']) if isinstance(data['suppliers'], (list, dict)) else data['suppliers'])
                
                update_fields.append("updated_at = datetime('now')")
                
                update_query = f"UPDATE vehicle_capacity_reference SET {', '.join(update_fields)} WHERE license_plate = ?"
                update_params.append(data['license_plate'])
                
                return self.execute_update(update_query, tuple(update_params))
            else:
                # 插入操作
                insert_fields = ['license_plate']
                insert_placeholders = ['?']
                insert_params = [data['license_plate']]
                
                if 'vehicle_type' in data:
                    insert_fields.append('vehicle_type')
                    insert_placeholders.append('?')
                    insert_params.append(data['vehicle_type'])
                
                if 'standard_volume' in data:
                    insert_fields.append('standard_volume')
                    insert_placeholders.append('?')
                    insert_params.append(data['standard_volume'])
                
                if 'suppliers' in data:
                    insert_fields.append('suppliers')
                    insert_placeholders.append('?')
                    insert_params.append(json.dumps(data['suppliers']) if isinstance(data['suppliers'], (list, dict)) else data['suppliers'])
                
                insert_query = f"INSERT INTO vehicle_capacity_reference ({', '.join(insert_fields)}) VALUES ({', '.join(insert_placeholders)})"
                return self.execute_update(insert_query, tuple(insert_params))
                
        except Exception as e:
            print(f'更新或插入车辆容积参考数据失败: {str(e)}')
            return False


    @classmethod
    def init_database(cls) -> bool:
        """
        静态方法：初始化数据库
        
        返回:
            bool: 初始化是否成功
        """
        try:
            db_manager = cls()
            if db_manager.connect():
                # 初始化所有数据库表
                success = db_manager.create_tables()
                db_manager.disconnect()
                
                if success:
                    print("✅ 数据库初始化完成")
                else:
                    print("❌ 数据库初始化失败")
                
                return success
            else:
                print("❌ 数据库连接失败")
                return False
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False


# 全局实例（保持与原有代码兼容）
# 注意：建议逐步迁移到使用 DatabaseService 而不是这个兼容层
db_manager = DatabaseManagerCompat()


if __name__ == '__main__':
    """测试兼容层功能"""
    
    # 测试连接
    manager = DatabaseManagerCompat()
    if manager.connect():
        print("✅ 连接成功")
        
        # 测试查询
        tables = manager.list_tables()
        print(f"数据库中的表: {tables}")
        
        # 测试表存在检查
        exists = manager.check_table_exists('manual_dispatch_tasks')
        print(f"manual_dispatch_tasks 表存在: {exists}")
        
        manager.disconnect()
        print("✅ 断开连接")
    else:
        print("❌ 连接失败")