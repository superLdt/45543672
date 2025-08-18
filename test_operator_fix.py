#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证dispatch_status_history表中operator字段是否正确存储用户名
"""

import sqlite3
import os

def test_operator_fix():
    """测试operator字段是否正确存储用户名"""
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询最新的状态历史记录
        cursor.execute("""
            SELECT task_id, status_change, operator, note, created_at 
            FROM dispatch_status_history 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        print("最新的状态历史记录：")
        print("-" * 80)
        for row in results:
            print(f"任务ID: {row['task_id']}")
            print(f"状态变更: {row['status_change']}")
            print(f"操作人: {row['operator']}")
            print(f"备注: {row['note']}")
            print(f"时间: {row['created_at']}")
            print("-" * 40)
        
        # 检查是否有数字ID作为operator的情况
        cursor.execute("""
            SELECT operator FROM dispatch_status_history 
            WHERE operator IS NOT NULL
        """)
        
        operators = [row['operator'] for row in cursor.fetchall()]
        numeric_count = sum(1 for op in operators if str(op).isdigit())
        print(f"\n发现 {numeric_count} 条记录使用数字ID作为operator")
        
        if numeric_count == 0:
            print("✅ 修复成功：所有operator字段都正确存储了用户名")
        else:
            print("⚠️ 仍有记录使用数字ID作为operator")
            
        conn.close()
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_operator_fix()