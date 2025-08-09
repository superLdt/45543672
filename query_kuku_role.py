from db_manager import DatabaseManager

db = DatabaseManager()
if db.connect():
    try:
        # 查询用户kuku的role_id
        db.cursor.execute("SELECT role_id FROM User WHERE username='kuku'")
        result = db.cursor.fetchone()
        if result:
            role_id = result[0]
            print(f"用户kuku的role_id: {role_id}")
            # 查询对应的角色名称
            db.cursor.execute("SELECT name FROM Role WHERE id=?", (role_id,))
            role_result = db.cursor.fetchone()
            if role_result:
                role_name = role_result[0]
                print(f"用户kuku的角色: {role_name}")
            else:
                print(f"未找到role_id为{role_id}的角色")
        else:
            print("未找到用户kuku")
    except Exception as e:
        print(f"查询失败: {str(e)}")
    finally:
        db.disconnect()
else:
    print("无法连接到数据库")