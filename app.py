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
# 从配置文件导入数据库路径
from config import DATABASE
# 使用db_manager统一管理数据库初始化
from db_manager import DatabaseManager

# 应用初始化
from flask_login import LoginManager, UserMixin, login_required, current_user,login_user,logout_user    

class User(UserMixin):
    def __init__(self, user_id, username, full_name, roles=None):
        self.id = user_id
        self.username = username
        self.full_name = full_name
        self.roles = roles or []
        # 支持单一角色访问
        self.role = roles[0] if roles and roles[0] else None
from config import SECRET_KEY
app = Flask(__name__)
app.secret_key = SECRET_KEY

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面路由
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
# 加载配置到 app 中（关键步骤）
app.config['DATABASE'] = DATABASE  # 确保这行代码存在

# 再次打印调试，确认应用中已加载
print("=== Flask 应用配置 ===")
print(f"应用中的数据库路径: {app.config['DATABASE']}")  # 必须显示正确路径
print(f"SECRET_KEY 是否设置: {bool(app.config['SECRET_KEY'])}")




# 日志配置
app.logger.setLevel(logging.DEBUG)



# 在应用启动时初始化数据库
with app.app_context():
    DatabaseManager.init_database()


# 数据库操作函数
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT id, username, full_name FROM User WHERE id = ? AND is_active = 1', (user_id,)).fetchone()
    if user:
        # 获取用户单一角色
        role = db.execute('''
            SELECT r.name FROM Role r
            JOIN UserRole ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
        ''', (user_id,)).fetchone()
        user_role = role['name'] if role else None
        # 使用单一角色创建用户对象
        return User(user['id'], user['username'], user['full_name'], [user_role])
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
        # 获取用户单一角色
        cursor.execute('''
            SELECT r.name FROM User u
            JOIN UserRole ur ON u.id = ur.user_id
            JOIN Role r ON ur.role_id = r.id
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
                JOIN UserRole ur ON ur.role_id = rmp.role_id
                WHERE ur.user_id = ? AND rmp.can_view = 1 AND m.is_active = 1
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
            # 获取用户角色（单一角色）
            role = db.execute('''
                SELECT r.name FROM Role r
                JOIN UserRole ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
            ''', (user['id'],)).fetchone()
            user_role = role['name'] if role else None
            
            # 创建用户对象并添加角色信息
            user_obj = User(user['id'], username, user['full_name'], [user_role])
            # 使用Flask-Login进行登录
            login_user(user_obj, remember=True)
            # 同步设置session以兼容权限检查
            session['user_id'] = user['id']
            session['user_role'] = user_role
            print(f"用户 {username} 登录成功，角色: {user_role}")  # 调试日志
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
    """统一的数据库初始化入口，使用DatabaseManager"""
    try:
        from db_manager import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.initialize_all_tables()
        app.logger.info('数据库初始化完成')
    except Exception as e:
        app.logger.error(f'数据库初始化失败: {str(e)}')
        raise





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

# 新增 AJAX 演示路由
@app.route('/ajax-demo')
def ajax_demo():
    return render_template('ajax-demo.html')



@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        db = get_db()
        
        # 获取统计数据
        total_tasks = db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        pending_tasks = db.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', ('pending',)).fetchone()[0]
        completed_tasks = db.execute('SELECT COUNT(*) FROM tasks WHERE status = ?', ('completed',)).fetchone()[0]
        
        # 获取收入数据（假设有revenue字段）
        total_revenue = db.execute('SELECT COALESCE(SUM(revenue), 0) FROM tasks WHERE status = ?', ('completed',)).fetchone()[0]
        
        stats = {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'total_revenue': total_revenue or 0,
            'today_tasks': 12,  # 模拟数据
            'active_vehicles': 8  # 模拟数据
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks')
@login_required
def api_tasks():
    """获取任务列表API"""
    try:
        db = get_db()
        status = request.args.get('status')
        limit = request.args.get('limit', 10, type=int)
        
        query = 'SELECT id, title, status, priority, created_at FROM tasks'
        params = []
        
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        tasks = db.execute(query, params).fetchall()
        
        return jsonify([{
            'id': task['id'],
            'title': task['title'],
            'status': task['status'],
            'priority': task['priority'],
            'created_at': task['created_at']
        } for task in tasks])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    """创建新任务API"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('title'):
            return jsonify({'error': '任务标题不能为空'}), 400
            
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (title, description, priority, status, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data.get('description', ''),
            data.get('priority', 'medium'),
            data.get('status', 'pending'),
            current_user.id
        ))
        
        task_id = cursor.lastrowid
        db.commit()
        
        return jsonify({
            'id': task_id,
            'message': '任务创建成功'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
@login_required
def update_task_status(task_id):
    """更新任务状态API"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': '状态不能为空'}), 400
            
        db = get_db()
        db.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
        db.commit()
        
        return jsonify({
            'message': '状态更新成功'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 注册API蓝图
from api import init_api_routes
init_api_routes(app)

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
