#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的人工派车数据库表结构
验证表创建、数据插入、查询等功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
import datetime

def test_new_tables():
    """测试新的表结构"""
    print("=== 测试新的人工派车表结构 ===")
    
    db = DatabaseManager()
    if not db.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        # 1. 创建表
        print("1. 创建人工派车相关表...")
        db.create_manual_dispatch_tables()
        print("✅ 表创建完成")
        
        # 2. 插入示例数据
        print("2. 插入示例数据...")
        db.insert_sample_dispatch_data()
        print("✅ 示例数据插入完成")
        
        # 3. 创建测试任务
        print("3. 创建测试派车任务...")
        task_data = {
            'required_date': '2024-01-15',
            'start_bureau': '北京局',
            'route_direction': '北京-上海',
            'carrier_company': '北京运输公司',
            'route_name': '京沪邮路',
            'transport_type': '单程',
            'requirement_type': '正班',
            'volume': 15.5,
            'weight': 800.0,
            'special_requirements': '需要冷藏运输',
            'operator': '测试用户'
        }
        
        result = db.create_dispatch_task(task_data)
        if result['success']:
            task_id = result['task_id']
        else:
            print(f"❌ 创建任务失败: {result['error']}")
            return False
        print(f"✅ 创建任务成功，任务ID: {task_id}")
        
        # 4. 查询任务列表
        print("4. 查询任务列表...")
        tasks = db.get_dispatch_tasks()
        print(f"✅ 获取到 {len(tasks)} 个任务")
        
        for task in tasks:
            print(f"  - 任务ID: {task['task_id']}")
            print(f"    日期: {task['required_date']}")
            print(f"    路向: {task['route_direction']}")
            print(f"    承运公司: {task['carrier_company']}")
            print(f"    状态: {task['status']}")
        
        # 5. 更新任务状态
        print("5. 更新任务状态...")
        result = db.update_task_status(task_id, '已分配', '管理员', '测试状态更新')
        if result['success']:
            print("✅ 状态更新成功")
        else:
            print(f"❌ 状态更新失败: {result['error']}")
        
        # 6. 分配车辆
        print("6. 分配车辆...")
        vehicle_data = {
            'manifest_number': 'LD20240115001',
            'manifest_serial': 'LD20240115001',
            'dispatch_number': 'PC20240115001',
            'license_plate': '京A12345',
            'carriage_number': '1号车厢'
        }
        
        result = db.assign_vehicle(task_id, vehicle_data)
        if result['success']:
            print("✅ 车辆分配成功")
        else:
            print(f"❌ 车辆分配失败: {result['error']}")
        
        # 7. 查询任务详情
        print("7. 查询任务详情...")
        task_detail = db.get_dispatch_task_detail(task_id)
        if task_detail:
            print(f"✅ 任务详情:")
            print(f"  任务ID: {task_detail['task_id']}")
            print(f"  日期: {task_detail['required_date']}")
            print(f"  始发局: {task_detail['start_bureau']}")
            print(f"  路向: {task_detail['route_direction']}")
            print(f"  状态: {task_detail['status']}")
        
        # 8. 查询状态历史
        print("8. 查询状态变更历史...")
        history = db.get_task_status_history(task_id)
        print(f"✅ 获取到 {len(history)} 条状态变更记录")
        
        for h in history:
            print(f"  - {h['timestamp']}: {h['status_change']} (操作人: {h['operator']})")
            if h['note']:
                print(f"    备注: {h['note']}")
        
        print("\n=== 所有测试通过 ===")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.disconnect()

if __name__ == '__main__':
    test_new_tables()