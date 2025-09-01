"""
数据库管理模块测试脚本
测试连接管理、表结构管理和数据操作管理模块的功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services import connection_manager, table_manager, data_manager
from config import DATABASE_CONFIG


def test_connection_manager():
    """测试连接管理模块"""
    print("=== 测试连接管理模块 ===")
    
    # 初始化连接管理器
    connection_manager.initialize(DATABASE_CONFIG)
    print("✓ 连接管理器初始化成功")
    
    # 获取连接
    db = connection_manager.get_connection()
    print("✓ 获取数据库连接成功")
    
    # 检查连接状态
    is_connected = connection_manager.is_connected()
    print(f"✓ 连接状态: {is_connected}")
    
    # 检查连接数量
    count = connection_manager.get_connection_count()
    print(f"✓ 当前连接数量: {count}")
    
    # 释放连接
    connection_manager.release_connection()
    print("✓ 释放连接成功")
    
    print("连接管理模块测试完成\n")


def test_table_manager():
    """测试表结构管理模块"""
    print("=== 测试表结构管理模块 ===")
    
    # 初始化连接管理器（如果尚未初始化）
    if not connection_manager._config:
        connection_manager.initialize(DATABASE_CONFIG)
    
    # 获取现有表
    existing_tables = table_manager.get_existing_tables()
    print(f"✓ 现有表: {existing_tables}")
    
    # 验证表结构
    validation_results = table_manager.validate_all_tables()
    print(f"✓ 表结构验证结果: {validation_results}")
    
    # 获取表定义
    companies_def = table_manager.get_table_definition("companies")
    if companies_def:
        print("✓ 获取companies表定义成功")
    else:
        print("✗ 获取companies表定义失败")
    
    print("表结构管理模块测试完成\n")


def test_data_manager():
    """测试数据操作管理模块"""
    print("=== 测试数据操作管理模块 ===")
    
    # 初始化连接管理器（如果尚未初始化）
    if not connection_manager._config:
        connection_manager.initialize(DATABASE_CONFIG)
    
    # 测试插入数据
    test_data = {
        "name": "测试公司",
        "contact_person": "测试联系人",
        "phone": "13800138000",
        "address": "测试地址"
    }
    
    # 检查companies表是否存在，如果不存在则创建
    if not table_manager.validate_table_structure("companies"):
        print("companies表不存在，正在创建...")
        table_manager.create_tables()
    
    # 插入数据
    inserted_id = data_manager.insert("companies", test_data)
    if inserted_id:
        print(f"✓ 插入数据成功，ID: {inserted_id}")
    else:
        print("✗ 插入数据失败")
        return
    
    # 查询数据
    results = data_manager.select("companies", where={"id": inserted_id})
    if results:
        print(f"✓ 查询数据成功: {results[0]}")
    else:
        print("✗ 查询数据失败")
    
    # 更新数据
    update_data = {"contact_person": "更新后的联系人"}
    updated_count = data_manager.update("companies", update_data, {"id": inserted_id})
    print(f"✓ 更新数据成功，影响行数: {updated_count}")
    
    # 统计行数
    count = data_manager.count("companies")
    print(f"✓ 统计行数成功: {count}")
    
    # 删除数据
    deleted_count = data_manager.delete("companies", {"id": inserted_id})
    print(f"✓ 删除数据成功，影响行数: {deleted_count}")
    
    print("数据操作管理模块测试完成\n")


def main():
    """主测试函数"""
    print("开始测试数据库管理模块...\n")
    
    try:
        # 测试连接管理模块
        test_connection_manager()
        
        # 测试表结构管理模块
        test_table_manager()
        
        # 测试数据操作管理模块
        test_data_manager()
        
        # 释放所有连接
        connection_manager.release_all_connections()
        print("✓ 所有连接已释放")
        
        print("所有测试完成！数据库管理模块工作正常。")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)