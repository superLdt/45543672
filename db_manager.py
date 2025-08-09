import sqlite3
import os
from config import DATABASE  # 从config.py导入数据库路径配置

class DatabaseManager:
    def __init__(self, db_path=DATABASE):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f'成功连接到数据库: {self.db_path}')
            return True
        except Exception as e:
            print(f'连接数据库失败: {str(e)}')
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            print('数据库连接已关闭')

    def check_table_exists(self, table_name):
        """检查表是否存在"""
        if not self.cursor:
            print('未连接到数据库')
            return False

        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f'检查表{table_name}失败: {str(e)}')
            return False

    def list_tables(self):
        """列出所有表"""
        if not self.cursor:
            print('未连接到数据库')
            return []

        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f'列出表失败: {str(e)}')
            return []

    def check_user_table(self):
        """检查用户表结构和数据"""
        if not self.check_table_exists('User'):
            print('用户表不存在')
            return False

        try:
            # 检查表结构
            self.cursor.execute("PRAGMA table_info(User);")
            columns = self.cursor.fetchall()
            print('用户表结构:')
            for column in columns:
                print(f'  {column[1]} ({column[2]})')

            # 检查数据
            self.cursor.execute("SELECT id, username, full_name, is_active FROM User;")
            users = self.cursor.fetchall()
            print('用户数据:')
            if not users:
                print('  没有找到用户数据')
            else:
                for user in users:
                    print(f'  ID: {user[0]}, 用户名: {user[1]}, 姓名: {user[2]}, 激活状态: {user[3]}')
            return True
        except Exception as e:
            print(f'检查用户表失败: {str(e)}')
            return False

# 使用示例
if __name__ == '__main__':
    # 创建数据库管理器实例
    db_manager = DatabaseManager()

    # 连接到数据库
    if db_manager.connect():
        # 列出所有表
        tables = db_manager.list_tables()
        print('数据库中的表:')
        for table in tables:
            print(f'  - {table}')

        # 检查用户表
        db_manager.check_user_table()

        # 断开连接
        db_manager.disconnect()
    else:
        print('无法连接到数据库，检查文件是否存在。')