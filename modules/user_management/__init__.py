from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from flask_login import current_user, login_required
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from flask import Blueprint, session, redirect, url_for, request

# 使用新的DatabaseService替代直接数据库连接
from services.database_service import DatabaseService

def get_db():
    """获取数据库连接，使用新的DatabaseService架构"""
    return DatabaseService.get_db()

user_management_bp = Blueprint('user_management_bp', __name__, url_prefix='/user-management', template_folder='templates')

# 权限检查装饰器
def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            
            # 获取用户权限
            conn = get_db()
            permissions = conn.execute('''
                SELECT p.name FROM Permission p
                JOIN RolePermission rp ON p.id = rp.permission_id
                JOIN UserRole ur ON rp.role_id = ur.role_id
                WHERE ur.user_id = ?
            ''', (current_user.id,)).fetchall()

            
            # 检查用户是否有超级管理员角色
            is_super_admin = '超级管理员' in current_user.roles
            
            # 检查权限
            permission_names = [p['name'] for p in permissions]
            if permission_name in permission_names or is_super_admin:
                return f(*args, **kwargs)
            else:
                return render_template('error.html', message='权限不足，无法访问此功能'), 403
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
    
    # 获取当前登录用户信息及角色名称列表
    current_user_info = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'roles': current_user.roles
    }
    return render_template('user_management/user_list.html', users=users_with_roles, search_query=search_query, user=current_user_info)

# 创建新用户
@user_management_bp.route('/users/new', methods=['GET', 'POST'])
@permission_required('user_manage')
def user_new():
    conn = get_db()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # 验证密码匹配
        if password != confirm_password:
            roles = conn.execute('SELECT * FROM Role').fetchall()
            companies = conn.execute('SELECT * FROM Company').fetchall()
            return render_template('user_management/user_edit.html', error='两次输入的密码不一致', roles=roles, companies=companies, user_roles=[])
        
        # 验证密码长度
        if len(password) < 8:
            roles = conn.execute('SELECT * FROM Role').fetchall()
            companies = conn.execute('SELECT * FROM Company').fetchall()
            return render_template('user_management/user_edit.html', error='密码长度不能少于8位', roles=roles, companies=companies, user_roles=[])
        
        full_name = request.form['full_name']
        email = request.form['email']
        company_id_str = request.form.get('company_id')
        try:
            company_id = int(company_id_str) if company_id_str else None
        except ValueError:
            company_id = None  # 处理非整数输入
        role_id_str = request.form.get('role')
        role_id = None
        if role_id_str:
            try:
                role_id = int(role_id_str)
            except ValueError:
                role_id = None
        
        # 哈希密码
        # 在第125行附近，替换现有的密码哈希代码
        # 原来的代码：
        # hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # 新的代码：
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(password)
        
        conn = get_db()
        try:
            # 检查用户名和邮箱是否已存在 (增强调试日志)
            print(f"正在检查用户名: {username} (精确匹配)")  # 调试日志
            existing_user = conn.execute('SELECT id FROM User WHERE username = ? COLLATE NOCASE', (username,)).fetchone()
            if existing_user:
                print(f"用户名已存在: {username} (现有用户ID: {existing_user['id']})")  # 调试日志
                print(f"当前事务状态: {conn.in_transaction}")  # 调试事务状态
                roles = conn.execute('SELECT * FROM Role').fetchall()
                companies = conn.execute('SELECT * FROM Company').fetchall()
                print(f"查询到的角色数量: {len(roles)}, 公司数量: {len(companies)}")  # 调试日志
                return render_template('user_management/user_edit.html', error='用户名已存在', roles=roles, companies=companies, user_roles=[])
            
            # 检查邮箱是否已存在
            print(f"正在检查邮箱: {email}")  # 调试日志
            existing_email = conn.execute('SELECT id FROM User WHERE email = ?', (email,)).fetchone()
            if existing_email:
                print(f"邮箱已存在: {email} (现有用户ID: {existing_email['id']})")  # 调试日志
                roles = conn.execute('SELECT * FROM Role').fetchall()
                companies = conn.execute('SELECT * FROM Company').fetchall()
                return render_template('user_management/user_edit.html', error='邮箱已被注册', roles=roles, companies=companies, user_roles=[])
            
            # 创建用户 (增强调试和错误处理)
            print(f"正在创建新用户: {username}, 姓名: {full_name}, 邮箱: {email}")  # 调试日志
            try:
                # 开始事务
                with conn:
                    conn.execute('''
                        INSERT INTO User (username, password, full_name, email, company_id, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (username, hashed_password, full_name, email, company_id, 1, datetime.now(), datetime.now()))
                    
                    # 获取新创建的用户
                    user = conn.execute('SELECT id FROM User WHERE username = ?', (username,)).fetchone()
                    print(f"新用户创建成功，ID: {user['id']}")  # 调试日志
                    
                    # 分配角色（单个角色）
                    if role_id:
                        conn.execute('INSERT INTO UserRole (user_id, role_id) VALUES (?, ?)', (user['id'], role_id))
                        print(f"角色分配成功，角色ID: {role_id}")  # 调试日志
                
                # 确保当前用户会话有效
                if not current_user.is_authenticated:
                    print("警告：当前用户会话无效")
                
                return redirect(url_for('user_management_bp.user_list'))
            except Exception as e:
                print(f"用户创建过程中出错: {str(e)}")  # 调试日志
                roles = conn.execute('SELECT * FROM Role').fetchall()
                companies = conn.execute('SELECT * FROM Company').fetchall()
                return render_template('user_management/user_edit.html', 
                                    error=f"创建用户失败: {str(e)}", 
                                    roles=roles, 
                                    companies=companies, 
                                    user_roles=[])
        except sqlite3.IntegrityError:
            roles = conn.execute('SELECT * FROM Role').fetchall()
            companies = conn.execute('SELECT * FROM Company').fetchall()
            return render_template('user_management/user_edit.html', error="用户名已存在", roles=roles, companies=companies, user_roles=[])
        finally:
              pass  # 由Flask自动管理连接关闭

    # GET请求 - 显示表单
    conn = get_db()
    # 获取所有角色
    all_roles = conn.execute('SELECT * FROM Role').fetchall()
    companies = conn.execute('SELECT * FROM Company').fetchall()
    current_user_info = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'roles': current_user.roles
    }

    return render_template('user_management/user_edit.html', 
                         roles=all_roles, 
                         companies=companies, 
                         editing_user=None, 
                         user=current_user_info,
                         user_roles=[])

# 编辑用户
@user_management_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@permission_required('user_manage')
def user_edit(id):
    """
    编辑用户信息的视图函数
    支持GET请求加载用户数据和表单，POST请求处理更新逻辑
    """
    # 统一获取数据库连接（避免多次创建连接）
    conn = get_db()
    try:
        # 1. 查询被编辑的用户信息
        user = conn.execute(
            'SELECT * FROM User WHERE id = ?', 
            (id,)
        ).fetchone()

        # 打印用户信息（调试用）
        if user:
            current_app.logger.info(f"加载用户信息: ID={user['id']}, 用户名={user['username']}, 状态={user['is_active']}")
        else:
            current_app.logger.warning(f"用户不存在: ID={id}")

        # 2. 预加载角色和公司数据（GET/POST都需要用到）
        roles = conn.execute('SELECT * FROM Role').fetchall()
        companies = conn.execute('SELECT * FROM Company').fetchall()

        # 3. 处理用户不存在的情况
        if not user:
            return render_template(
                'user_management/user_edit.html',
                user=None,
                roles=roles,
                companies=companies,
                error="用户不存在或已被删除"
            )

        # 4. 处理POST请求（更新用户信息）
        if request.method == 'POST':
            return _handle_post_request(conn, user, id, roles, companies)

        # 5. 处理GET请求（渲染编辑表单）
        return _handle_get_request(conn, user, roles, companies)

    except sqlite3.Error as e:
        # 数据库异常处理
        current_app.logger.error(f"数据库操作错误: {str(e)}")
        return render_template(
            'user_management/user_edit.html',
            user=user,
            roles=roles,
            companies=companies,
            error=f"数据加载失败: {str(e)}"
        )
    finally:
        # 确保连接关闭（无论成功/失败）
        conn.close()


def _handle_post_request(conn, user, user_id, roles, companies):
    """处理POST请求：解析表单数据并更新用户信息"""
    try:
        # 解析表单数据
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        company_id_str = request.form.get('company_id', '')
        is_active = 1 if request.form.get('is_active') else 0  # 处理激活状态
        role_id_str = request.form.get('role')  # 单选角色
        role_id = None
        if role_id_str:
            try:
                role_id = int(role_id_str)
            except ValueError:
                role_id = None
        new_password = request.form.get('new_password', '').strip()

        # 处理公司ID（转换为整数或None）
        try:
            company_id = int(company_id_str) if company_id_str else None
        except ValueError:
            company_id = None
            current_app.logger.warning("无效的公司ID，已设为None")

        # 构建更新字段和SQL语句
        update_fields = [full_name, email, company_id, is_active, datetime.now(), user_id]
        base_query = '''
            UPDATE User 
            SET full_name = ?, email = ?, company_id = ?, is_active = ?, updated_at = ?
            WHERE id = ?
        '''

        # 若提供新密码，追加密码更新逻辑
        if new_password:
            # 密码复杂度验证（示例：至少8位）
            if len(new_password) < 8:
                return render_template(
                    'user_management/user_edit.html',
                    user=user,
                    roles=roles,
                    companies=companies,
                    error="密码长度不能少于8位"
                )
            # 安全哈希处理（替代原sha256，自带盐值）
            hashed_password = generate_password_hash(new_password)
            # 调整SQL和字段列表（插入密码字段）
            base_query = '''
                UPDATE User 
                SET full_name = ?, email = ?, company_id = ?, is_active = ?, 
                    password = ?, updated_at = ?
                WHERE id = ?
            '''
            update_fields.insert(4, hashed_password)  # 插入密码到字段列表

        # 执行用户信息更新
        conn.execute(base_query, tuple(update_fields))

        # 同步用户角色（先删除旧关联，再添加新角色）
        conn.execute('DELETE FROM UserRole WHERE user_id = ?', (user_id,))
        if role_id and any(str(r['id']) == str(role_id) for r in roles):
            conn.execute(
                'INSERT INTO UserRole (user_id, role_id) VALUES (?, ?)',
                (user_id, role_id)
            )

        # 提交事务
        conn.commit()
        current_app.logger.info(f"用户更新成功: ID={user_id}")
        return redirect(url_for('user_management_bp.user_list'))

    except sqlite3.Error as e:
        # 数据库错误回滚事务
        conn.rollback()
        current_app.logger.error(f"用户更新失败: {str(e)}")
        return render_template(
            'user_management/user_edit.html',
            user=user,
            roles=roles,
            companies=companies,
            error=f"更新失败: {str(e)}"
        )


def _handle_get_request(conn, user, roles, companies):
    """处理GET请求：加载用户当前角色并渲染表单"""
    # 获取被编辑用户的角色ID（用于模板勾选）
    edited_user_role = conn.execute(
        'SELECT role_id FROM UserRole WHERE user_id = ?',
        (user['id'],)
    ).fetchone()
    edited_user_role_ids = [str(edited_user_role['role_id'])] if edited_user_role else []

    # 获取当前登录用户的角色信息（用于权限控制等扩展场景）
    current_user_roles = conn.execute(
        '''
        SELECT r.id, r.name FROM Role r
        JOIN UserRole ur ON r.id = ur.role_id
        WHERE ur.user_id = ?
        ''',
        (current_user.id,)
    ).fetchall()

    # 构造当前用户信息字典（传递给模板）
    current_user_info = {
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name or '未设置',
        'roles': [r['name'] for r in current_user_roles]
    }

    # 渲染编辑表单
    return render_template(
        'user_management/user_edit.html',
        editing_user=user,
        roles=roles,
        companies=companies,
        user_roles=edited_user_role_ids,  # 被编辑用户的角色ID（用于勾选）
        user=current_user_info
    )
    # 打印下id
    print(f"编辑用户ID: {id}")      
    # 打印下request.form
    print(f"request.form: {request.form}")      
   





    conn = get_db()
    user = conn.execute('SELECT * FROM User WHERE id = ?', (id,)).fetchone()
    if user is None:
        return redirect(url_for('user_management_bp.user_list'))


    if user is None:
        return redirect(url_for('user_management_bp.user_list'))
    
    conn = get_db()
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        company_id_str = request.form.get('company_id')
        try:
            company_id = int(company_id_str) if company_id_str else None
        except ValueError:
            company_id = None  # 处理非整数输入
        is_active = 1 if request.form.get('is_active') else 0
        role_id_str = request.form.get('role')
        
        # 验证角色ID
        try:
            role_id = int(role_id_str) if role_id_str else None
            if role_id is None:
                return render_template('user_management/user_edit.html', user=user, error='请选择一个角色')
        except ValueError:
            return render_template('user_management/user_edit.html', user=user, error='角色ID无效')
        
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
            
            # 分配新角色（单个角色）
            conn.execute('INSERT INTO UserRole (user_id, role_id) VALUES (?, ?)', (id, role_id))
                
            conn.commit()
            return redirect(url_for('user_management_bp.user_list'))
        except sqlite3.Error as e:
            return render_template('user_management/user_edit.html', user=user, error=str(e))
        finally:
            pass

    
    try:
        # 确保数据库连接
        conn = get_db()
        
        # 获取编辑用户的角色信息
        user_role = conn.execute(
            'SELECT role_id FROM UserRole WHERE user_id = ?', 
            (id,)).fetchone()
        user_roles = [user_role['role_id']] if user_role else []
            
        # 获取所有角色和公司
        roles = conn.execute('SELECT * FROM Role').fetchall()
        companies = conn.execute('SELECT * FROM Company').fetchall()
        
       
            
        return render_template('user_management/user_edit.html',
                            user=user,
                            roles=roles,
                            user_roles=user_roles,
                            companies=companies,
                            current_user=current_user)
                            
    except Exception as e:
        current_app.logger.error(f"用户编辑错误: {str(e)}")
        return render_template('error.html', message="加载用户信息失败"), 500
    finally:
        pass  # 连接由Flask管理

    # 移除try-except块外的重复返回语句

# 删除用户
@user_management_bp.route('/users/<int:id>/delete', methods=['POST'])
@permission_required('user_manage')
def user_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM User WHERE id = ?', (id,))
    conn.commit()

    return redirect(url_for('user_management_bp.user_list'))

# 重置用户密码
@user_management_bp.route('/users/<int:id>/reset-password', methods=['POST'])
@permission_required('user_manage')
def user_reset_password(id):
    from werkzeug.security import generate_password_hash
    conn = get_db()
    # 检查用户是否存在
    user = conn.execute('SELECT id FROM User WHERE id = ?', (id,)).fetchone()
    if not user:
        return redirect(url_for('user_management_bp.user_list'))
    # 重置密码为admin123
    hashed_password = generate_password_hash('admin123')
    conn.execute('UPDATE User SET password = ? WHERE id = ?', (hashed_password, id))
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
