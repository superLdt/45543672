from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from db_manager import DatabaseManager
from datetime import datetime

system_bp = Blueprint('system_bp', __name__, template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.roles.name not in ['管理员', '超级管理员']:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@system_bp.route('/')
@login_required
def index():
    return render_template('system/index.html', user=current_user)

@system_bp.route('/users')
@login_required
@admin_required
def manage_users():
    return render_template('system/users.html', title='用户管理', user=current_user)

@system_bp.route('/settings')
@login_required
@admin_required
def system_settings():
    return render_template('system/settings.html', title='系统设置', user=current_user)

@system_bp.route('/page-config')
@login_required
@admin_required
def role_permissions():
    return render_template('system/role_permissions.html', title='角色权限配置', user=current_user)

@admin_required
def page_config():
    return render_template('system/page_config.html', title='页面配置', user=current_user)

@system_bp.route('/api/modules')
@login_required
@admin_required
def get_modules():
    db_manager = DatabaseManager()
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.name, m.display_name, m.icon_class, m.sort_order, m.is_active,
                   r.name as role_name, rmp.can_view, rmp.can_edit, rmp.can_delete
            FROM modules m
            LEFT JOIN role_module_permissions rmp ON m.id = rmp.module_id
            LEFT JOIN roles r ON rmp.role_id = r.id
            ORDER BY m.sort_order, r.name
        ''')
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_manager.disconnect()
    return jsonify(result)

@system_bp.route('/api/role-permissions/<int:role_id>')
@login_required
@admin_required
def get_role_permissions(role_id):
    db_manager = DatabaseManager()
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.name, m.display_name, 
                   COALESCE(rmp.can_view, 0) as can_view,
                   COALESCE(rmp.can_edit, 0) as can_edit,
                   COALESCE(rmp.can_delete, 0) as can_delete
            FROM modules m
            LEFT JOIN role_module_permissions rmp ON m.id = rmp.module_id AND rmp.role_id = ?
            WHERE m.is_active = 1
            ORDER BY m.sort_order
        ''', (role_id,))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db_manager.disconnect()
    return jsonify(result)

@system_bp.route('/api/update-permissions', methods=['POST'])
@login_required
@admin_required
def update_permissions():
    data = request.json
    role_id = data.get('role_id')
    permissions = data.get('permissions')
    
    db_manager = DatabaseManager()
    try:
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        # 先删除该角色的所有权限
        cursor.execute('DELETE FROM role_module_permissions WHERE role_id = ?', (role_id,))
        
        # 重新插入权限
        for perm in permissions:
            cursor.execute('''
                INSERT INTO role_module_permissions (role_id, module_id, can_view, can_edit, can_delete)
                VALUES (?, ?, ?, ?, ?)
            ''', (role_id, perm['module_id'], perm['can_view'], 
                  perm['can_edit'], perm['can_delete']))
        
        conn.commit()
        return jsonify({'success': True, 'message': '权限更新成功'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        db_manager.disconnect()