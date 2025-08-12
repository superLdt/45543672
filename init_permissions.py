#!/usr/bin/env python3
"""
权限初始化模块
确保应用启动时角色权限配置正确
"""

import sqlite3
import logging
from db_manager import DatabaseManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 角色权限配置映射
ROLE_PERMISSIONS_CONFIG = {
    '超级管理员': [
        'user_manage', 'role_manage', 'permission_manage',
        'basic_data_view', 'basic_data_edit',
        'planning_view', 'planning_edit',
        'cost_view', 'cost_manage',
        'schedule_view', 'schedule_manage',
        'reconciliation_view', 'reconciliation_manage'
    ],
    '区域调度员': [
        'basic_data_view', 'planning_view', 
        'schedule_view', 'reconciliation_view'
    ],
    '对账人员': [
        'basic_data_view', 'cost_view', 'reconciliation_view'
    ],
    '供应商': [
        'schedule_view', 'reconciliation_view'
    ],
    '车间地调': [
        'basic_data_view', 'schedule_view'
    ]
}

def initialize_roles_and_permissions():
    """初始化角色和权限"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        logger.error("数据库连接失败，无法初始化权限")
        return False
    
    cursor = db_manager.cursor
    try:
        logger.info("开始初始化角色和权限...")
        
        # 1. 确保所有角色存在
        _ensure_roles_exist(cursor)
        
        # 2. 确保所有权限存在
        _ensure_permissions_exist(cursor)
        
        # 3. 配置角色权限
        _configure_role_permissions(cursor)
        
        db_manager.conn.commit()
        logger.info("角色权限初始化完成")
        return True
        
    except Exception as e:
        db_manager.conn.rollback()
        logger.error(f"权限初始化失败: {str(e)}")
        return False
    finally:
        db_manager.disconnect()

def _ensure_roles_exist(cursor):
    """确保所有角色存在"""
    roles = [
        ('超级管理员', '系统最高权限管理员'),
        ('区域调度员', '负责区域内调度管理'),
        ('对账人员', '负责财务对账工作'),
        ('供应商', '外部供应商账户'),
        ('车间地调', '负责车间车辆需求与供应商车辆审批')
    ]
    
    inserted_count = 0
    for name, description in roles:
        cursor.execute('''
            INSERT OR IGNORE INTO Role (name, description)
            VALUES (?, ?)
        ''', (name, description))
        if cursor.rowcount > 0:
            inserted_count += 1
            logger.info(f"创建角色: {name}")
    
    if inserted_count > 0:
        logger.info(f"新增 {inserted_count} 个角色")

def _ensure_permissions_exist(cursor):
    """确保所有权限存在"""
    permissions = [
        ('user_manage', 'user_management', '用户管理权限'),
        ('role_manage', 'user_management', '角色管理权限'),
        ('permission_manage', 'system', '权限管理权限'),
        ('basic_data_view', 'basic_data', '基础数据查看权限'),
        ('basic_data_edit', 'basic_data', '基础数据编辑权限'),
        ('planning_view', 'planning', '规划数据查看权限'),
        ('planning_edit', 'planning', '规划数据编辑权限'),
        ('cost_view', 'cost_analysis', '成本数据查看权限'),
        ('cost_manage', 'cost_analysis', '成本数据管理权限'),
        ('schedule_view', 'scheduling', '调度数据查看权限'),
        ('schedule_manage', 'scheduling', '调度数据管理权限'),
        ('reconciliation_view', 'reconciliation', '对账数据查看权限'),
        ('reconciliation_manage', 'reconciliation', '对账数据管理权限')
    ]
    
    inserted_count = 0
    for name, module, description in permissions:
        cursor.execute('''
            INSERT OR IGNORE INTO Permission (name, module, description)
            VALUES (?, ?, ?)
        ''', (name, module, description))
        if cursor.rowcount > 0:
            inserted_count += 1
            logger.info(f"创建权限: {name}")
    
    if inserted_count > 0:
        logger.info(f"新增 {inserted_count} 个权限")

def _configure_role_permissions(cursor):
    """配置角色权限"""
    # 获取所有权限的ID映射
    cursor.execute('SELECT id, name FROM Permission')
    permission_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 获取所有角色的ID映射
    cursor.execute('SELECT id, name FROM Role')
    role_map = {row[1]: row[0] for row in cursor.fetchall()}
    
    configured_count = 0
    
    for role_name, permission_names in ROLE_PERMISSIONS_CONFIG.items():
        if role_name not in role_map:
            continue
            
        role_id = role_map[role_name]
        
        for permission_name in permission_names:
            if permission_name not in permission_map:
                continue
                
            permission_id = permission_map[permission_name]
            
            cursor.execute('''
                INSERT OR IGNORE INTO RolePermission (role_id, permission_id)
                VALUES (?, ?)
            ''', (role_id, permission_id))
            
            if cursor.rowcount > 0:
                configured_count += 1
                logger.debug(f"为角色 {role_name} 配置权限 {permission_name}")
    
    if configured_count > 0:
        logger.info(f"配置了 {configured_count} 个角色权限关系")

def check_and_fix_permissions():
    """检查并修复权限配置"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        return False
    
    cursor = db_manager.cursor
    try:
        # 检查角色权限是否完整
        cursor.execute('''
            SELECT r.name, COUNT(rp.permission_id) as permission_count
            FROM Role r
            LEFT JOIN RolePermission rp ON r.id = rp.role_id
            GROUP BY r.id, r.name
        ''')
        
        roles_with_permissions = cursor.fetchall()
        
        needs_fix = False
        for role_name, count in roles_with_permissions:
            expected_count = len(ROLE_PERMISSIONS_CONFIG.get(role_name, []))
            if count != expected_count:
                logger.warning(f"角色 {role_name} 权限不完整: 现有 {count}, 期望 {expected_count}")
                needs_fix = True
        
        if needs_fix:
            logger.info("检测到权限配置问题，开始修复...")
            return initialize_roles_and_permissions()
        
        logger.info("权限配置检查完成，无需修复")
        return True
        
    except Exception as e:
        logger.error(f"权限检查失败: {str(e)}")
        return False
    finally:
        db_manager.disconnect()

if __name__ == '__main__':
    # 命令行直接运行
    initialize_roles_and_permissions()