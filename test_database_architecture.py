"""
数据库架构测试脚本
测试新的数据库抽象层和工厂模式
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.database_interface import DatabaseInterface
from services.sqlite_database import SQLiteDatabase
from services.db_factory import DatabaseFactory
from config import DATABASE_CONFIG


def test_database_interface():
    """测试数据库接口"""
    print("=== 测试数据库接口 ===")
    
    # 测试SQLite数据库实例化
    try:
        db = SQLiteDatabase('test_database.db')
        print("✅ SQLite数据库实例化成功")
        
        # 测试连接
        if db.connect():
            print("✅ SQLite数据库连接成功")
            
            # 测试查询
            result = db.execute_query("SELECT 1 as test")
            if result and result[0]['test'] == 1:
                print("✅ SQLite数据库查询成功")
            
            # 测试表操作
            tables = db.list_tables()
            print(f"✅ 表列表查询成功: {tables}")
            
            db.disconnect()
            print("✅ SQLite数据库断开连接成功")
        
        # 删除测试数据库
        if os.path.exists('test_database.db'):
            os.remove('test_database.db')
            
    except Exception as e:
        print(f"❌ SQLite数据库测试失败: {e}")
        return False
    
    return True


def test_database_factory():
    """测试数据库工厂"""
    print("\n=== 测试数据库工厂 ===")
    
    try:
        # 测试SQLite数据库创建
        sqlite_db = DatabaseFactory.create_database(DATABASE_CONFIG)
        print("✅ SQLite数据库工厂创建成功")
        
        # 测试连接
        if sqlite_db.connect():
            print("✅ 工厂创建的SQLite数据库连接成功")
            
            # 测试基本操作
            result = sqlite_db.execute_query("SELECT 1 as test")
            if result and result[0]['test'] == 1:
                print("✅ 工厂创建的SQLite数据库查询成功")
            
            sqlite_db.disconnect()
            print("✅ 工厂创建的SQLite数据库断开连接成功")
        
        # 测试配置验证
        valid_config = {
            'type': 'sqlite',
            'sqlite': {'database': 'test.db'}
        }
        
        if DatabaseFactory.validate_config(valid_config):
            print("✅ 配置验证成功")
        
        # 测试无效配置
        invalid_config = {'type': 'invalid'}
        if not DatabaseFactory.validate_config(invalid_config):
            print("✅ 无效配置验证正确")
        
    except Exception as e:
        print(f"❌ 数据库工厂测试失败: {e}")
        return False
    
    return True


def test_database_operations():
    """测试数据库操作"""
    print("\n=== 测试数据库操作 ===")
    
    try:
        # 创建测试数据库
        db = SQLiteDatabase('test_operations.db')
        
        if db.connect():
            # 测试事务
            db.begin_transaction()
            
            # 创建测试表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
            """
            
            db.execute_update(create_table_sql)
            print("✅ 测试表创建成功")
            
            # 测试插入数据
            insert_sql = "INSERT INTO test_users (name, email) VALUES (?, ?)"
            db.execute_update(insert_sql, ('测试用户', 'test@example.com'))
            print("✅ 数据插入成功")
            
            # 获取最后插入ID
            last_id = db.get_lastrowid()
            print(f"✅ 最后插入ID: {last_id}")
            
            # 测试查询数据
            select_sql = "SELECT * FROM test_users WHERE id = ?"
            result = db.execute_query(select_sql, (last_id,))
            
            if result and result[0]['name'] == '测试用户':
                print("✅ 数据查询成功")
            
            # 测试表存在检查
            if db.table_exists('test_users'):
                print("✅ 表存在检查成功")
            
            # 测试获取列信息
            columns = db.get_table_columns('test_users')
            if columns:
                print("✅ 列信息获取成功")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            
            db.commit_transaction()
            print("✅ 事务提交成功")
            
            db.disconnect()
            
            # 清理测试数据库
            if os.path.exists('test_operations.db'):
                os.remove('test_operations.db')
            
    except Exception as e:
        print(f"❌ 数据库操作测试失败: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("开始测试新的数据库架构...\n")
    
    success_count = 0
    total_tests = 3
    
    # 运行所有测试
    if test_database_interface():
        success_count += 1
    
    if test_database_factory():
        success_count += 1
    
    if test_database_operations():
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"总测试数: {total_tests}")
    print(f"成功数: {success_count}")
    print(f"失败数: {total_tests - success_count}")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！新的数据库架构工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)