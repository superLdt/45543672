"""
数据库迁移测试脚本

用于验证从旧版 db_manager.py 到新 services 架构的迁移过程
确保功能兼容性和数据一致性
"""

import os
import sys
import sqlite3
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from db_manager import DatabaseManager as OldDatabaseManager
from services.db_manager_compat import DatabaseManagerCompat as NewDatabaseManager


def test_connection_migration():
    """
    测试连接管理迁移
    
    验证新旧版本的连接功能是否一致
    """
    print("[TEST] 测试连接管理迁移...")
    
    # 创建新旧版本实例
    old_db = OldDatabaseManager()
    new_db = NewDatabaseManager()
    
    # 测试连接
    old_connected = old_db.connect()
    new_connected = new_db.connect()
    
    print(f"旧版连接状态: {old_connected}")
    print(f"新版连接状态: {new_connected}")
    
    # 验证连接状态一致
    assert old_connected == new_connected, "连接状态不一致"
    
    # 测试断开连接
    old_db.disconnect()
    new_db.disconnect()
    
    print("[OK] 连接管理迁移测试通过")
    return True


def test_table_operations():
    """
    测试表操作迁移
    
    验证新旧版本的表操作功能是否一致
    """
    print("[TEST] 测试表操作迁移...")
    
    old_db = OldDatabaseManager()
    new_db = NewDatabaseManager()
    
    # 建立连接
    old_db.connect()
    new_db.connect()
    
    try:
        # 测试获取表列表
        old_tables = old_db.list_tables()
        new_tables = new_db.list_tables()
        
        print(f"旧版表列表: {len(old_tables)} 张表")
        print(f"新版表列表: {len(new_tables)} 张表")
        
        # 验证表数量一致（考虑新版过滤系统表的情况）
        # 新版会过滤掉 sqlite_sequence 等系统表，所以数量可能不一致
        # 但非系统表的内容应该一致
        system_tables = {"sqlite_sequence"}
        old_non_system_tables = [t for t in old_tables if t not in system_tables]
        
        if len(old_non_system_tables) != len(new_tables):
            print(f"[WARN] 非系统表数量不一致 - 旧版: {len(old_non_system_tables)}, 新版: {len(new_tables)}")
            assert False, "非系统表数量不一致"
        
        # 验证表内容一致（排除系统表）
        old_non_system_tables_set = set(old_tables) - system_tables
        new_tables_set = set(new_tables)
        
        if old_non_system_tables_set != new_tables_set:
            missing_in_new = old_non_system_tables_set - new_tables_set
            missing_in_old = new_tables_set - old_non_system_tables_set
            
            if missing_in_new:
                print(f"[WARN] 新版缺少的表: {missing_in_new}")
            if missing_in_old:
                print(f"[WARN] 旧版缺少的表: {missing_in_old}")
            
            assert False, "非系统表内容不一致"
        
        # 测试表存在检查
        test_table = 'manual_dispatch_tasks' if 'manual_dispatch_tasks' in old_tables else old_tables[0] if old_tables else None
        
        if test_table:
            old_exists = old_db.check_table_exists(test_table)
            new_exists = new_db.check_table_exists(test_table)
            
            print(f"表 '{test_table}' 存在检查 - 旧版: {old_exists}, 新版: {new_exists}")
            assert old_exists == new_exists, "表存在检查结果不一致"
        
        print("[OK] 表操作迁移测试通过")
        return True
        
    finally:
        # 确保断开连接
        old_db.disconnect()
        new_db.disconnect()


def test_query_operations():
    """
    测试查询操作迁移
    
    验证新旧版本的查询功能是否一致
    """
    print("[TEST] 测试查询操作迁移...")
    
    old_db = OldDatabaseManager()
    new_db = NewDatabaseManager()
    
    old_db.connect()
    new_db.connect()
    
    try:
        # 测试简单查询
        test_query = "SELECT name FROM sqlite_master WHERE type='table'"
        
        old_result = old_db.execute_query(test_query)
        new_result = new_db.execute_query(test_query)
        
        print(f"旧版查询结果: {len(old_result)} 条记录")
        print(f"新版查询结果: {len(new_result)} 条记录")
        
        # 验证查询结果数量一致
        assert len(old_result) == len(new_result), "查询结果数量不一致"
        
        # 如果有数据，验证具体内容
        if old_result and new_result:
            # 提取表名进行比较
            old_tables = [row['name'] for row in old_result]
            new_tables = [row['name'] for row in new_result]
            
            old_tables_set = set(old_tables)
            new_tables_set = set(new_tables)
            
            assert old_tables_set == new_tables_set, "查询结果内容不一致"
        
        print("[OK] 查询操作迁移测试通过")
        return True
        
    finally:
        old_db.disconnect()
        new_db.disconnect()


def test_data_consistency():
    """
    测试数据一致性
    
    验证新旧版本对相同数据的操作结果一致
    """
    print("[TEST] 测试数据一致性...")
    
    old_db = OldDatabaseManager()
    new_db = NewDatabaseManager()
    
    old_db.connect()
    new_db.connect()
    
    try:
        # 选择一个测试表
        test_table = None
        tables = old_db.list_tables()
        
        # 优先选择有数据的表进行测试
        for table in ['manual_dispatch_tasks', 'vehicles', 'Company', 'User']:
            if table in tables:
                test_table = table
                break
        
        if not test_table:
            test_table = tables[0] if tables else None
        
        if not test_table:
            print("[WARN] 没有可测试的表，跳过数据一致性测试")
            return True
        
        print(f"测试表: {test_table}")
        
        # 查询数据
        query = f"SELECT * FROM {test_table} LIMIT 5"
        
        old_data = old_db.execute_query(query)
        new_data = new_db.execute_query(query)
        
        print(f"旧版数据记录数: {len(old_data)}")
        print(f"新版数据记录数: {len(new_data)}")
        
        # 验证数据记录数一致
        assert len(old_data) == len(new_data), "数据记录数不一致"
        
        # 如果有数据，验证数据结构
        if old_data and new_data:
            # 验证列名一致
            old_columns = set(old_data[0].keys())
            new_columns = set(new_data[0].keys())
            
            if old_columns != new_columns:
                print(f"[WARN] 列名不一致 - 旧版: {old_columns}, 新版: {new_columns}")
                # 对于兼容层，允许新版有额外列
                if not old_columns.issubset(new_columns):
                    assert False, "旧版有新版没有的列"
            
            # 验证具体数据值（抽样检查）
            for i, (old_row, new_row) in enumerate(zip(old_data, new_data)):
                for col in old_columns:
                    if col in new_row:
                        assert old_row[col] == new_row[col], f"第 {i} 行数据不一致"
        
        print("[OK] 数据一致性测试通过")
        return True
        
    finally:
        old_db.disconnect()
        new_db.disconnect()


def test_performance_comparison():
    """
    性能对比测试
    
    比较新旧版本的性能差异
    """
    print("[TEST] 性能对比测试...")
    
    import time
    
    old_db = OldDatabaseManager()
    new_db = NewDatabaseManager()
    
    # 预热连接
    old_db.connect()
    new_db.connect()
    
    test_query = "SELECT name FROM sqlite_master WHERE type='table'"
    
    # 测试旧版性能
    old_times = []
    for _ in range(10):
        start_time = time.time()
        old_db.execute_query(test_query)
        old_times.append(time.time() - start_time)
    
    # 测试新版性能
    new_times = []
    for _ in range(10):
        start_time = time.time()
        new_db.execute_query(test_query)
        new_times.append(time.time() - start_time)
    
    # 计算平均时间
    old_avg = sum(old_times) / len(old_times)
    new_avg = sum(new_times) / len(new_times)
    
    print(f"旧版平均查询时间: {old_avg:.6f} 秒")
    print(f"新版平均查询时间: {new_avg:.6f} 秒")
    
    if new_avg > 0:
        performance_ratio = old_avg / new_avg
        print(f"性能比率: {performance_ratio:.2f}x")
        
        # 允许新版有轻微性能差异（±20%）
        if performance_ratio < 0.8:
            print("[WARN] 新版性能下降超过20%")
        elif performance_ratio > 1.2:
            print("[OK] 新版性能提升超过20%")
        else:
            print("[OK] 性能在可接受范围内")
    
    old_db.disconnect()
    new_db.disconnect()
    
    print("[OK] 性能对比测试完成")
    return True


def run_all_tests():
    """运行所有迁移测试"""
    print("=" * 60)
    print("[START] 开始数据库迁移测试")
    print("=" * 60)
    
    tests = [
        test_connection_migration,
        test_table_operations,
        test_query_operations,
        test_data_consistency,
        test_performance_comparison
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] {test_func.__name__} 测试失败: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print("[RESULT] 测试结果汇总")
    print("=" * 60)
    print(f"[OK] 通过: {passed}")
    print(f"[ERROR] 失败: {failed}")
    print(f"[TOTAL] 总计: {passed + failed}")
    
    if failed == 0:
        print("[SUCCESS] 所有迁移测试通过！可以安全进行重构。")
        return True
    else:
        print("[WARN] 存在测试失败，请检查兼容性问题后再进行重构。")
        return False


def create_backup():
    """创建数据库备份"""
    import shutil
    import datetime
    
    db_file = os.path.join(project_root, 'database.db')
    if not os.path.exists(db_file):
        print("[WARN] 数据库文件不存在，跳过备份")
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(project_root, f'database_backup_{timestamp}.db')
    
    try:
        shutil.copy2(db_file, backup_file)
        print(f"[OK] 数据库备份已创建: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"[ERROR] 创建备份失败: {e}")
        return None


if __name__ == '__main__':
    """主函数：运行迁移测试"""
    
    # 创建备份
    backup_path = create_backup()
    
    if backup_path:
        print(f"备份文件: {backup_path}")
    
    print()
    
    # 运行测试
    success = run_all_tests()
    
    if success:
        print("\n[NEXT] 下一步行动:")
        print("1. 逐步替换代码中的 DatabaseManager 引用")
        print("2. 使用 services.db_manager_compat 作为过渡")
        print("3. 最终迁移到 services.database_service")
    else:
        print("\n[ERROR] 请先解决测试失败的问题再继续重构")
    
    sys.exit(0 if success else 1)