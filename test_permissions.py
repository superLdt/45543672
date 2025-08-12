#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限配置测试脚本
用于测试DatabaseManager中的权限配置功能
"""

from db_manager import DatabaseManager

def test_permissions():
    """测试权限配置功能"""
    print("🧪 开始测试权限配置功能...")
    
    db = DatabaseManager()
    
    # 测试1：初始化数据库和权限
    print("\n📋 测试1：初始化数据库和权限")
    if db.initialize_all_tables():
        print("✅ 数据库和权限初始化成功")
    else:
        print("❌ 数据库初始化失败")
        return False
    
    # 测试2：检查并修复权限
    print("\n🔍 测试2：检查并修复权限")
    if db.check_and_fix_permissions():
        print("✅ 权限检查完成")
    else:
        print("❌ 权限检查失败")
        return False
    
    # 测试3：验证权限数据
    print("\n📊 测试3：验证权限数据")
    try:
        db.connect()
        
        # 检查角色数量
        db.cursor.execute('SELECT COUNT(*) FROM Role')
        role_count = db.cursor.fetchone()[0]
        print(f"角色数量: {role_count}")
        
        # 检查权限数量
        db.cursor.execute('SELECT COUNT(*) FROM Permission')
        permission_count = db.cursor.fetchone()[0]
        print(f"权限数量: {permission_count}")
        
        # 检查角色权限关系
        db.cursor.execute('SELECT COUNT(*) FROM RolePermission')
        role_permission_count = db.cursor.fetchone()[0]
        print(f"角色权限关系数量: {role_permission_count}")
        
        # 检查每个角色的权限
        db.cursor.execute('''
            SELECT r.name, COUNT(rp.permission_id) as permission_count
            FROM Role r
            LEFT JOIN RolePermission rp ON r.id = rp.role_id
            GROUP BY r.id, r.name
            ORDER BY r.name
        ''')
        
        print("\n📋 各角色权限统计:")
        for role_name, count in db.cursor.fetchall():
            print(f"  {role_name}: {count} 个权限")
            
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ 验证权限数据失败: {str(e)}")
        return False

if __name__ == '__main__':
    test_permissions()