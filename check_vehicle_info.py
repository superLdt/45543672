import sqlite3

def check_vehicle_info(task_id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM vehicles WHERE task_id = ?', (task_id,))
        result = cursor.fetchall()
        
        print('车辆信息:')
        if result:
            for row in result:
                print(row)
        else:
            print('未找到车辆信息')
            
    except Exception as e:
        print(f'查询出错: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_vehicle_info('T20250817161912')