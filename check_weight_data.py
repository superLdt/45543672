#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中重量字段的数据
"""
import sqlite3
import os

def check_weight_data():
    """检查数据库中的重量数据"""
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(manual_dispatch_tasks)")
        columns = cursor.fetchall()
        print("表结构:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} (nullable: {col[3]})")
        
        # 检查重量数据
        cursor.execute("SELECT task_id, weight, start_bureau, route_name FROM manual_dispatch_tasks LIMIT 10")
        rows = cursor.fetchall()
        
        print("\n重量数据样本:")
        for row in rows:
            task_id, weight, start, end = row
            print(f"任务 {task_id}: 重量={weight}, 路线={start}-{end}")
        
        # 统计空值
        cursor.execute("SELECT COUNT(*) FROM manual_dispatch_tasks WHERE weight IS NULL OR weight = '' OR weight = 0")
        null_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM manual_dispatch_tasks")
        total_count = cursor.fetchone()[0]
        
        print(f"\n统计: {null_count}/{total_count} 条记录的重量为空或0")
        
        conn.close()
        
    except Exception as e:
        print(f"查询出错: {e}")

if __name__ == "__main__":
    check_weight_data()