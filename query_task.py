import sqlite3

def query_task_status(task_id):
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        cursor = conn.cursor()
        
        cursor.execute('SELECT task_id, status FROM manual_dispatch_tasks WHERE task_id = ?', (task_id,))
        result = cursor.fetchone()
        
        if result:
            print(f'任务ID: {result["task_id"]}, 状态: {result["status"]}')
        else:
            print('未找到任务')
            
    except Exception as e:
        print(f'查询出错: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    query_task_status('T20250817161912')