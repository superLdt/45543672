from db_manager import DatabaseManager

def analyze_database():
    db = DatabaseManager()
    if db.connect():
        try:
            # 列出所有表
            tables = db.list_tables()
            print("数据库中的表:")
            for table in tables:
                print(f'\n=== 表名: {table} ===')
                # 查询表结构
                db.cursor.execute(f"PRAGMA table_info({table});")
                columns = db.cursor.fetchall()
                print("字段信息:")
                for column in columns:
                    print(f'  字段名: {column[1]}, 类型: {column[2]}, 主键: {column[5]}')
                # 查询表数据示例(前3行)
                try:
                    db.cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
                    rows = db.cursor.fetchall()
                    print("数据示例(前3行):")
                    for row in rows:
                        print(f'  {row}')
                except Exception as e:
                    print(f"查询数据失败: {str(e)}")
            return tables
        except Exception as e:
            print(f"分析数据库失败: {str(e)}")
            return []
        finally:
            db.disconnect()
    else:
        print("无法连接到数据库")
        return []

if __name__ == '__main__':
    analyze_database()