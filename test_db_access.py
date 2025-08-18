import sqlite3
from db_manager import DatabaseManager

def test_db_access():
    """测试数据库访问"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("数据库连接失败")
        return
    
    try:
        # 检查任务是否存在且状态为"待供应商响应"
        task_id = 'T20250817144348'  # 使用用户报告的task_id
        db_manager.cursor.execute('''
            SELECT * FROM manual_dispatch_tasks 
            WHERE task_id = ? AND status = ?
        ''', (task_id, '待供应商响应'))
        
        task = db_manager.cursor.fetchone()
        if not task:
            print(f"任务 {task_id} 不存在或状态不正确")
            # 让我们查询所有任务看看
            db_manager.cursor.execute('''
                SELECT task_id, status FROM manual_dispatch_tasks
            ''')
            tasks = db_manager.cursor.fetchall()
            print("所有任务:")
            for t in tasks:
                print(f"  {t['task_id']}: {t['status']}")
        else:
            print(f"找到任务 {task_id}")
            print(f"任务状态: {task['status']}")
            print(f"任务类型: {type(task)}")
            print(f"任务所有字段: {dict(task)}")
    
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    test_db_access()