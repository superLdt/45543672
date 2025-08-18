import sqlite3

def check_vehicles_table():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('PRAGMA table_info(vehicles)')
        result = cursor.fetchall()
        
        print('vehicles表结构:')
        for row in result:
            print(f'  列名: {row[1]}, 类型: {row[2]}, 非空: {row[3]}, 默认值: {row[4]}, 主键: {row[5]}')
            
    except Exception as e:
        print(f'查询出错: {e}')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_vehicles_table()