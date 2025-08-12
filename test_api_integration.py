#!/usr/bin/env python3
"""
API集成测试脚本
测试DatabaseManager与API的集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
from api.utils import generate_task_id, validate_dispatch_data
from config import DATABASE

def test_database_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    print(f"当前数据库路径: {DATABASE}")
    
    db_manager = DatabaseManager()
    if db_manager.connect():
        print("✅ 数据库连接成功")
        
        # 测试表是否存在
        tables = db_manager.list_tables()
        print(f"数据库中的表: {tables}")
        
        # 检查manual_dispatch_tasks表
        if db_manager.check_table_exists('manual_dispatch_tasks'):
            print("✅ manual_dispatch_tasks表存在")
        else:
            print("❌ manual_dispatch_tasks表不存在")
            
        db_manager.disconnect()
        return True
    else:
        print("❌ 数据库连接失败")
        return False

def test_task_id_generation():
    """测试任务ID生成"""
    print("\n=== 测试任务ID生成 ===")
    
    task_id = generate_task_id()
    if task_id:
        print(f"✅ 生成的任务ID: {task_id}")
        return True
    else:
        print("❌ 任务ID生成失败")
        return False

def test_data_validation():
    """测试数据验证"""
    print("\n=== 测试数据验证 ===")
    
    # 测试有效数据
    valid_data = {
        'title': '测试任务',
        'vehicle_type': '货车',
        'purpose': '测试',
        'start_location': '起点',
        'end_location': '终点',
        'dispatch_track': '轨道A'
    }
    
    is_valid, error_msg = validate_dispatch_data(valid_data)
    if is_valid:
        print("✅ 有效数据验证通过")
    else:
        print(f"❌ 有效数据验证失败: {error_msg}")
    
    # 测试无效数据
    invalid_data = {
        'title': '',  # 空标题
        'vehicle_type': '货车',
        'dispatch_track': '轨道C'  # 无效轨道
    }
    
    is_valid, error_msg = validate_dispatch_data(invalid_data)
    if not is_valid:
        print(f"✅ 无效数据正确拒绝: {error_msg}")
        return True
    else:
        print("❌ 无效数据未正确拒绝")
        return False

def main():
    """运行所有测试"""
    print("开始API集成测试...")
    
    tests = [
        test_database_connection,
        test_task_id_generation,
        test_data_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！API集成正常")
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main()