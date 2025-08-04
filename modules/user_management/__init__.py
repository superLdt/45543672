from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from flask import Blueprint, session, redirect, url_for, request

# 使用延迟导入避免循环依赖
from flask import current_app

def get_db():
    if 'db' not in current_app.config:
        from app import get_db as _get_db
        return _get_db()
    return current_app.config['db']

user_management_bp = Blueprint('user_management_bp', __name__, url_prefix='/user-management', template_folder='templates')

# 权限检查装饰器
def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查用户是否登录
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            # 获取用户权限
            conn = get_db()
            permissions = conn.execute('''
                SELECT p.name FROM Permission p
                JOIN RolePermission rp ON p.id = rp.permission_id
                JOIN UserRole ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ?
            ''', (session['user_id'],)).fetchall()

            
            # 检查用户是否有超级管理员角色
            is_super_admin = any(role['name'] == '超级管理员' for role in get_user_roles(session['user_id']))
            
            # 检查权限
            permission_names = [p['name'] for p in permissions]
            if permission_name in permission_names or is_super_admin:
                return f(*args, **kwargs)
            else:
                return render_template('under_development.html'), 403
        return decorated_function
    return decorator

# 获取用户角色的辅助函数
def get_user_roles(user_id):
    conn = get_db()
    roles = conn.execute('''
        SELECT r.* FROM Role r
        JOIN UserRole ur ON r.id = ur.role_id
        WHERE ur.user_id = ?
    ''', (user_id,)).fetchall()

    return roles

# 用户管理首页
@user_management_bp.route('/')
def index():
    return redirect(url_for('user_management_bp.user_list'))

# 用户列表页面 - 添加搜索功能
@user_management_bp.route('/users')
@permission_required('user_manage')
def user_list():
    search_query = request.args.get('search', '').strip()
    conn = get_db()
    
    if search_query:
        users = conn.execute('''
            SELECT * FROM User 
            WHERE username LIKE ? OR full_name LIKE ? OR email LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        users = conn.execute('SELECT * FROM User ORDER BY created_at DESC').fetchall()
    
    # 获取每个用户的角色信息
    users_with_roles = []
    for user in users:
        roles = conn.execute('''
            SELECT r.* FROM Role r
            JOIN UserRole ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
        ''', (user['id'],)).fetchall()
        users_with_roles.append({** user, 'roles': roles})
    

    # 获取当前登录用户信息
    current_user = conn.execute('SELECT * FROM User WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('user_management/user_list.html', users=users_with_roles, search_query=search_query, user=current_user)

# 创建新用户
@user_management_bp.route('/users/new', methods=['GET', 'POST'])
@permission_required('user_manage')
def user_new():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # 验证密码匹配
        if password != confirm_password:
            roles = conn.execute('SELECT * FROM Role').fetchall()
            return render_template('user_management/user_edit.html', error='两次输入的密码不一致', roles=roles)
        
        full_name = request.form['full_name']
        email = request.form['email']
        company_id_str = request.form.get('company_id')
        try:
            company_id = int(company_id_str) if company_id_str else None
        except ValueError:
            company_id = None  # 处理非整数输入
        role_ids = request.form.getlist('roles')
        # 验证并转换角色ID为整数
        valid_role_ids = []
        for role_id_str in role_ids:
            try:
                role_id = int(role_id_str)
                valid_role_ids.append(role_id)
            except ValueError:
                pass  # 忽略无效的角色ID
        role_ids = valid_role_ids
        
        # 哈希密码
        # 在第125行附近，替换现有的密码哈希代码
        # 原来的代码：
        # hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 新的代码：
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)
        
        conn = get_db()
        try:
            # 检查用户名是否已存在
            existing_user = conn.execute('SELECT id FROM User WHERE username = ?', (username,)).fetchone()
            if existing_user:
                roles = conn.execute('SELECT * FROM Role').fetchall()
                return render_template('user_management/user_edit.html', error='用户名已存在', roles=roles)
            
            # 创建用户
            conn.execute('''
                INSERT INTO User (username, password, full_name, email, company_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, full_name, email, company_id, 1, datetime.now(), datetime.now()))
            
            # 获取新创建的用户
            user = conn.execute('SELECT id FROM User WHERE username = ?', (username,)).fetchone()
            
            # 分配角色
            for role_id in role_ids:
                conn.execute('INSERT INTO UserRole (user_id, role_id) VALUES (?, ?)', (user['id'], role_id))
                
            conn.commit()
            return redirect(url_for('user_management_bp.user_list'))
        except sqlite3.IntegrityError:
            roles = conn.execute('SELECT * FROM Role').fetchall()
            return render_template('user_management/user_edit.html', error="用户名已存在", roles=roles)
        finally:
              pass  # 由Flask自动管理连接关闭

    # GET请求 - 显示表单
    conn = get_db()
    roles = conn.execute('SELECT * FROM Role').fetchall()
    companies = conn.execute('SELECT * FROM Company').fetchall()
    current_user = conn.execute('SELECT * FROM User WHERE id = ?', (session['user_id'],)).fetchone()

    return render_template('user_management/user_edit.html', roles=roles, companies=companies, user=None)

# 编辑用户
@user_management_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('user_manage')
def user_edit(id):
    conn = get_db()
    user = conn.execute('SELECT * FROM User WHERE id = ?', (id,)).fetchone()
    
    if user is None:

        return render_template('user_management/user_edit.html', roles=roles, companies=companies, user=None)
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        company_id_str = request.form.get('company_id')
        try:
            company_id = int(company_id_str) if company_id_str else None
        except ValueError:
            company_id = None  # 处理非整数输入
        is_active = 1 if request.form.get('is_active') else 0
        role_ids = request.form.getlist('roles')
        
        # 如果提供了新密码，则更新密码
        new_password = request.form.get('new_password')
        
        try:
            update_fields = [full_name, email, company_id, is_active, datetime.now(), id]
            query = '''
                UPDATE User 
                SET full_name = ?, email = ?, company_id = ?, is_active = ?, updated_at = ?
                WHERE id = ?
            '''
            
            if new_password and new_password.strip():
                # 在第200行附近，替换编辑用户时的密码哈希代码
                # 原来的代码：
                # hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                
                # 新的代码：
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash(new_password)
                query = '''
                    UPDATE User 
                    SET full_name = ?, email = ?, company_id = ?, is_active = ?, password = ?, updated_at = ?
                    WHERE id = ?
                '''
                update_fields.insert(4, hashed_password)
                
            # 更新用户
            conn.execute(query, tuple(update_fields))
            
            # 移除现有角色
            conn.execute('DELETE FROM UserRole WHERE user_id = ?', (id,))
            
            # 分配新角色
            for role_id in role_ids:
                conn.execute('INSERT INTO UserRole (user_id, role_id) VALUES (?, ?)', (id, role_id))
                
            conn.commit()
            return redirect(url_for('user_management_bp.user_list'))
        except sqlite3.Error as e:
            return render_template('user_management/user_edit.html', user=user, error=str(e))
        finally:
            pass

    
    # GET请求 - 显示表单
    user_roles = [r['role_id'] for r in conn.execute('SELECT role_id FROM UserRole WHERE user_id = ?', (id,)).fetchall()]
    roles = conn.execute('SELECT * FROM Role').fetchall()
    companies = conn.execute('SELECT * FROM Company').fetchall()

    return render_template('user_management/user_edit.html', user=user, roles=roles, user_roles=user_roles, companies=companies)

# 删除用户
@user_management_bp.route('/users/<int:id>/delete', methods=['POST'])
@permission_required('user_manage')
def user_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM User WHERE id = ?', (id,))
    conn.commit()

    return redirect(url_for('user_management_bp.user_list'))

# 角色列表
@user_management_bp.route('/roles')
@permission_required('user_manage')
def role_list():
    conn = get_db()  # 修正为get_db()
    roles = conn.execute('SELECT * FROM Role').fetchall()
    current_user = conn.execute('SELECT * FROM User WHERE id = ?', (session['user_id'],)).fetchone()

    return render_template('user_management/role_list.html', roles=roles, user=current_user)

# 编辑角色权限
@user_management_bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('user_manage')
def role_edit(id):
    conn = get_db()  # 修正为get_db()
    role = conn.execute('SELECT * FROM Role WHERE id = ?', (id,)).fetchone()
    
    if role is None:

        return render_template('under_development.html'), 404
    
    if request.method == 'POST':
        permission_ids = request.form.getlist('permissions')
        
        try:
            # 移除现有权限
            conn.execute('DELETE FROM RolePermission WHERE role_id = ?', (id,))
            
            # 分配新权限
            for permission_id in permission_ids:
                conn.execute('INSERT INTO RolePermission (role_id, permission_id) VALUES (?, ?)', (id, permission_id))
                
            conn.commit()
            return redirect(url_for('user_management_bp.role_list'))
        except sqlite3.Error as e:
            return render_template('user_management/role_edit.html', role=role, error=str(e))
        finally:
            pass  # 由Flask自动管理连接关闭
    
    # GET请求 - 显示表单
    role_permissions = [p['permission_id'] for p in conn.execute('SELECT permission_id FROM RolePermission WHERE role_id = ?', (id,)).fetchall()]
    permissions = conn.execute('SELECT * FROM Permission ORDER BY module').fetchall()
    current_user = conn.execute('SELECT * FROM User WHERE id = ?', (session['user_id'],)).fetchone()

    return render_template('user_management/role_edit.html', role=role, permissions=permissions, role_permissions=role_permissions, user=current_user)

# 检查用户名是否已存在 (AJAX)
@user_management_bp.route('/check_username', methods=['POST'])
def check_username():
    username = request.form.get('username')
    user_id = request.form.get('user_id', None)
    
    conn = get_db()  # 修正为get_db()
    query = 'SELECT id FROM User WHERE username = ?'
    params = [username]
    
    if user_id:
        query += ' AND id != ?'
        params.append(user_id)
        
    user = conn.execute(query, params).fetchone()
    
    return jsonify({'exists': user is not None})
