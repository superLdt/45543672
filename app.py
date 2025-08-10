print('=== 脚本开始执行 ===')
import os
import sys
import traceback
import sqlite3
import logging
from flask import Flask, g, request, session, redirect, url_for, render_template, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import traceback
from functools import wraps
import jinja2


# 应用初始化
from flask_login import LoginManager, UserMixin, login_required, current_user,login_user,logout_user    

class User(UserMixin):
    def __init__(self, user_id, username, full_name, roles=None):
        self.id = user_id
        self.username = username
        self.full_name = full_name
        self.roles = roles or []
from config import SECRET_KEY
app = Flask(__name__)
app.secret_key = SECRET_KEY

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面路由
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# 从配置文件导入数据库路径
from config import DATABASE


# 日志配置
app.logger.setLevel(logging.DEBUG)



# 数据库操作函数
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT id, username, full_name FROM User WHERE id = ? AND is_active = 1', (user_id,)).fetchone()
    if user:
        # 获取用户角色
        roles = db.execute('''
            SELECT r.name FROM Role r
            JOIN UserRole ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
        ''', (user_id,)).fetchall()
        role_names = [role['name'] for role in roles]
        return User(user['id'], user['username'], user['full_name'], role_names)
    return None

def get_db():
    db_manager = getattr(g, '_db_manager', None)
    if db_manager is None:
        db_manager = g._db_manager = DatabaseManager()
        if not db_manager.connect():
            raise Exception('数据库连接失败')
        db_manager.conn.row_factory = sqlite3.Row
    return db_manager.conn

@app.teardown_appcontext
def close_connection(exception):
    db_manager = getattr(g, '_db_manager', None)
    if db_manager is not None:
        db_manager.disconnect()

# 路由定义
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# 在文件顶部添加数据库连接
# 修复权限查询函数，使用正确的表名
import sqlite3

from db_manager import DatabaseManager

def get_user_modules(user_id):
    """获取用户有权限访问的模块列表，支持父子模块结构"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("数据库连接失败")
        return []
    cursor = db_manager.cursor
    try:
        # 获取用户角色
        cursor.execute('''
            SELECT r.name FROM User u
            JOIN Role r ON u.role_id = r.id
            WHERE u.id = ?
        ''', (user_id,))
        role_result = cursor.fetchone()
        
        if not role_result:
            return []
            
        role_name = role_result[0]
        
        # 获取所有有权限的模块
        if role_name == '超级管理员':
            cursor.execute('''
                SELECT id, name, display_name, route_name, icon_class, parent_id
                FROM modules 
                WHERE is_active = 1
                ORDER BY sort_order
            ''')
        else:
            cursor.execute('''
                SELECT m.id, m.name, m.display_name, m.route_name, m.icon_class, m.parent_id
                FROM modules m
                JOIN role_module_permissions rmp ON m.id = rmp.module_id
                JOIN User u ON u.id = ur.user_id
                JOIN UserRole ur ON ur.role_id = rmp.role_id
                WHERE u.id = ? AND rmp.can_view = 1 AND m.is_active = 1
                ORDER BY m.sort_order
            ''', (user_id,))
        
        # 构建模块字典和层次结构
        module_dict = {}
        root_modules = []
        
        for row in cursor.fetchall():
            module = {
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'route_name': row[3],
                'icon_class': row[4],
                'parent_id': row[5],
                'children': []
            }
            module_dict[module['id']] = module
            
            if module['parent_id'] is None:
                root_modules.append(module)
        
        # 添加子模块到父模块
        for module_id, module in module_dict.items():
            if module['parent_id'] is not None and module['parent_id'] in module_dict:
                module_dict[module['parent_id']]['children'].append(module)
        
        return root_modules
    except Exception as e:
        print(f"获取用户模块权限时出错: {e}")
        return []
    finally:
        db_manager.disconnect()

# 修复角色查询API
@app.route('/api/roles')
@login_required
def get_roles():
    """获取所有角色列表"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return jsonify({'error': '数据库连接失败'}), 500
        cursor = db_manager.cursor
        cursor.execute('SELECT id, name, description FROM Role ORDER BY id')
        roles = []
        for row in cursor.fetchall():
            roles.append({
                'id': row[0],
                'name': row[1],
                'description': row[2]
            })
        db_manager.disconnect()
        return jsonify(roles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 修复角色权限查询API
@app.route('/api/role-permissions/<int:role_id>')
@login_required
def get_role_permissions(role_id):
    """获取角色的模块权限配置"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return jsonify({'error': '数据库连接失败'}), 500
        cursor = db_manager.cursor
        cursor.execute('''
            SELECT m.id, m.name, m.display_name, 
                   COALESCE(rmp.can_view, 0) as can_view,
                   COALESCE(rmp.can_edit, 0) as can_edit,
                   COALESCE(rmp.can_delete, 0) as can_delete,
                   m.icon_class
            FROM modules m
            LEFT JOIN role_module_permissions rmp ON m.id = rmp.module_id AND rmp.role_id = ?
            WHERE m.is_active = 1
            ORDER BY m.sort_order
        ''', (role_id,))
        
        permissions = []
        for row in cursor.fetchall():
            permissions.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2],
                'can_view': bool(row[3]),
                'can_edit': bool(row[4]),
                'can_delete': bool(row[5]),
                'icon_class': row[6]
            })
        db_manager.disconnect()
        return jsonify(permissions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 修改 dashboard 路由
@app.route('/dashboard')
@login_required
def dashboard():
    user_modules = get_user_modules(current_user.id)
    return render_template('dashboard.html', user=current_user, user_modules=user_modules)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return '用户名和密码不能为空'
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('SELECT id, password, full_name FROM User WHERE username = ? AND is_active = 1', (username,))
            user = cursor.fetchone()
        except Exception as e:
            return f'数据库错误: {str(e)}'
        finally:
            cursor.close()
        
        if user and check_password_hash(user['password'], password):
            # 获取用户角色
            roles = db.execute('''
                SELECT r.name FROM Role r
                JOIN UserRole ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
            ''', (user['id'],)).fetchall()
            role_names = [role['name'] for role in roles]
            # 创建用户对象并添加角色信息
            user_obj = User(user['id'], username, user['full_name'], role_names)
            # 使用Flask-Login进行登录
            login_user(user_obj, remember=True)
            # 同步设置session['user_id']以兼容权限检查
            session['user_id'] = user['id']
            session['user_roles'] = role_names
            print(f"用户 {username} 登录成功，角色: {role_names}")  # 调试日志
            return redirect(url_for('dashboard'))
        
        return '用户名或密码错误'
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/debug/user')
@login_required
def debug_user():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'full_name': current_user.full_name,
        'roles': current_user.roles
    })

@app.route('/debug/user_roles')
@login_required
def debug_user_roles():
    db = get_db()
    user_roles = db.execute('''
        SELECT ur.user_id, u.username, ur.role_id, r.name as role_name
        FROM UserRole ur
        JOIN User u ON ur.user_id = u.id
        JOIN Role r ON ur.role_id = r.id
        ORDER BY ur.user_id
    ''').fetchall()
    result = []
    for row in user_roles:
        result.append({
            'user_id': row['user_id'],
            'username': row['username'],
            'role_id': row['role_id'],
            'role_name': row['role_name']
        })
    return jsonify(result)

@app.route('/under_development')
def under_development():
    return render_template('error.html', message='功能开发中')

# 错误处理
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message='页面不存在 (404)'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return '服务器内部错误 (500)', 500

@app.errorhandler(403)
def permission_denied(e):
    return '权限不足 (403)', 403

@app.errorhandler(jinja2.TemplateNotFound)
def handle_template_not_found(e):
    return render_template('error.html', message='模板未找到'), 404

# 数据库初始化
def init_db():
    """初始化数据库，创建所有必要的表结构"""
    try:
        db = get_db()
        cursor = db.cursor()
        db.execute('BEGIN TRANSACTION')

        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            company_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES Company (id)
        )
        ''')

        # 创建单位表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Company (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            bank_name TEXT,
            account_number TEXT,
            address TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建角色表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Role (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建权限表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Permission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            module TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建用户角色关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserRole (
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, role_id),
            FOREIGN KEY (user_id) REFERENCES User (id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES Role (id) ON DELETE CASCADE
        )
        ''')

        # 创建角色权限关联表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS RolePermission (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES Role (id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES Permission (id) ON DELETE CASCADE
        )
        ''')

        # 创建模块表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            route_name TEXT,
            icon_class TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES modules (id) ON DELETE SET NULL
        )
        ''')

        # 添加索引提升查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_username ON User(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_name ON Role(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permission_module ON Permission(module)')

        db.commit()
        app.logger.info('数据库表结构初始化成功')

    except Exception as e:
        db.rollback()
        app.logger.error(f'数据库初始化失败: {str(e)}')
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        # 不在这里关闭db，因为teardown_appcontext会处理

    # 插入默认数据
    try:
        insert_default_data()
    except Exception as e:
        app.logger.error(f'默认数据插入失败: {str(e)}')


def insert_default_data():
    """插入默认角色、权限和管理员用户"""
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor()
        db.execute('BEGIN TRANSACTION')
        app.logger.info('开始插入默认数据...')

        _insert_roles(cursor)
        _insert_permissions(cursor)
        _insert_default_modules(cursor)
        admin_user_id = _insert_admin_user(cursor)

        if admin_user_id:
            admin_role_id = _get_role_id(cursor, '超级管理员')
            if admin_role_id:
                _assign_all_permissions_to_role(cursor, admin_role_id)
                _assign_role_to_user(cursor, admin_user_id, admin_role_id)

        db.commit()
        app.logger.info('默认数据插入成功')
    except Exception as e:
        if db:
            db.rollback()
        app.logger.error(f'默认数据插入失败: {str(e)}', exc_info=True)
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                app.logger.warning(f'关闭游标时出错: {str(e)}')


def _insert_roles(cursor):
    """插入默认角色"""
    roles = [
        ('超级管理员', '系统最高权限管理员'),
        ('区域调度员', '负责区域内调度管理'),
        ('对账人员', '负责财务对账工作'),
        ('供应商', '外部供应商账户')
    ]
    cursor.executemany('INSERT OR IGNORE INTO Role (name, description) VALUES (?, ?)', roles)
    inserted = cursor.rowcount
    app.logger.debug(f'插入了 {inserted} 个新角色')
    return inserted


def _insert_permissions(cursor):
    """插入默认权限"""
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
    cursor.executemany('INSERT OR IGNORE INTO Permission (name, module, description) VALUES (?, ?, ?)', permissions)
    inserted = cursor.rowcount
    app.logger.debug(f'插入了 {inserted} 个新权限')
    return inserted

def _insert_default_modules(cursor):
    """插入默认模块"""
    modules = [
        ('dashboard', '控制面板', 'dashboard', 'fas fa-tachometer-alt', 1, 1, None),
        ('system_settings', '系统设置', 'system_bp.system_settings', 'fas fa-cog', 90, 1, None),
        ('user_management', '用户管理', 'system_bp.manage_users', 'fas fa-users', 95, 1, None),
        ('role_permissions', '角色权限配置', 'system_bp.role_permissions', 'fas fa-shield-alt', 99, 1, 10)  # 假设系统设置模块ID为10
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO modules 
        (name, display_name, route_name, icon_class, sort_order, is_active, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', modules)
    inserted = cursor.rowcount
    app.logger.debug(f'插入了 {inserted} 个新模块')
    return inserted


def _insert_admin_user(cursor):
    """插入默认管理员用户并返回用户ID"""
    admin_username = 'admin'
    admin_password = 'admin123'
    admin_fullname = '系统管理员'
    admin_email = 'admin@example.com'

    hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256')
    cursor.execute('''
    INSERT OR IGNORE INTO User (username, password, full_name, email, is_active)
    VALUES (?, ?, ?, ?, ?)
    ''', (admin_username, hashed_password, admin_fullname, admin_email, True))

    if cursor.rowcount > 0:
        app.logger.info(f'默认管理员用户 {admin_username} 创建成功')
        cursor.execute('SELECT id FROM User WHERE username = ?', (admin_username,))
        return cursor.fetchone()[0]
    else:
        app.logger.info(f'默认管理员用户 {admin_username} 已存在')
        cursor.execute('SELECT id FROM User WHERE username = ?', (admin_username,))
        result = cursor.fetchone()
        return result[0] if result else None


def _get_role_id(cursor, role_name):
    """根据角色名称获取角色ID"""
    cursor.execute('SELECT id FROM Role WHERE name = ?', (role_name,))
    result = cursor.fetchone()
    if not result:
        app.logger.error(f'角色 {role_name} 不存在')
        return None
    return result[0]


def _assign_all_permissions_to_role(cursor, role_id):
    """为角色分配所有权限"""
    cursor.execute('SELECT id FROM Permission')
    permission_ids = [row[0] for row in cursor.fetchall()]
    if not permission_ids:
        app.logger.warning('未找到任何权限，无法分配')
        return 0

    role_permissions = [(role_id, pid) for pid in permission_ids]
    cursor.executemany('INSERT OR IGNORE INTO RolePermission (role_id, permission_id) VALUES (?, ?)', role_permissions)
    assigned = cursor.rowcount
    app.logger.debug(f'为角色 {role_id} 分配了 {assigned} 个权限')
    return assigned


def _assign_role_to_user(cursor, user_id, role_id):
    """为用户分配角色"""
    cursor.execute('INSERT OR IGNORE INTO UserRole (user_id, role_id) VALUES (?, ?)', (user_id, role_id))
    if cursor.rowcount > 0:
        app.logger.debug(f'为用户 {user_id} 分配角色 {role_id} 成功')
        return True
    app.logger.debug(f'用户 {user_id} 已拥有角色 {role_id}')
    return False


# 导入并注册蓝图（如果存在）
try:
    # 延迟导入蓝图以避免循环依赖
    from modules.system import system_bp
    from modules.reconciliation import reconciliation_bp
    from modules.scheduling import scheduling_bp
    from modules.planning import planning_bp
    from modules.cost_analysis import cost_analysis_bp
    from modules.basic_data import basic_data_bp
    from modules.user_management import user_management_bp
    
    app.register_blueprint(system_bp, url_prefix='/system')
    app.register_blueprint(reconciliation_bp, url_prefix='/reconciliation')
    app.register_blueprint(scheduling_bp, url_prefix='/scheduling')
    app.register_blueprint(planning_bp, url_prefix='/planning')      
    app.register_blueprint(cost_analysis_bp, url_prefix='/cost_analysis')
    app.register_blueprint(basic_data_bp, url_prefix='/basic_data')
    app.register_blueprint(user_management_bp, url_prefix='/users')
except ImportError as e:
    print(f'蓝图模块导入失败: {str(e)}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
except Exception as e:
    print(f'蓝图注册错误: {str(e)}', file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

# 应用入口点
if __name__ == '__main__':
    print('=== 应用启动诊断 ===')
    print('1. 开始执行主入口代码')
    try:
        print('2. 创建应用上下文')
        with app.app_context():
            print('3. 初始化数据库')
            init_db()
            print('4. 数据库初始化完成')
        
        print('5. 获取端口号')
        port = int(os.environ.get('PORT', 5000))
        
        print('6. 准备启动服务器')
        app.logger.info(f'应用启动，访问地址: http://127.0.0.1:{port}')
        print(f'7. 启动服务器 on http://0.0.0.0:{port}')
        # 延迟导入用户管理蓝图避免循环依赖
        
        
        app.run(host='0.0.0.0', port=port, debug=True)
        print('8. 服务器启动成功')
    except Exception as e:
        print('应用初始化错误详情:')
        traceback.print_exc()
        print('错误类型:', type(e))
        print('错误信息:', str(e))
        exit(1)
