# 双轨派车API接口实现指南

## 🎯 实现概览

本指南提供从零开始实现双轨派车API接口的详细步骤，包括代码实现、测试验证和部署上线。

## 📁 第一步：创建API模块结构

### 1.1 创建API目录和基础文件

```bash
# 在d:\智能运力系统\45543672_backup\目录下执行
cd d:\智能运力系统\45543672_backup\

# 创建API模块目录
mkdir api
cd api

# 创建必要的Python文件
echo "" > __init__.py
echo "" > dispatch.py
echo "" > decorators.py
echo "" > utils.py
```

### 1.2 检查当前项目结构

确保项目结构如下：
```
d:\智能运力系统\45543672_backup\
├── app.py
├── db_manager.py
├── api/
│   ├── __init__.py
│   ├── dispatch.py
│   ├── decorators.py
│   └── utils.py
└── ...其他文件
```

## 🔧 第二步：实现基础工具函数

### 2.1 创建权限装饰器 (api/decorators.py)

```python
from functools import wraps
from flask import jsonify, session

def require_role(allowed_roles):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': '未登录或权限不足'
                    }
                }), 401
            
            user_role = session['user_role']
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 4002,
                        'message': f'需要权限: {allowed_roles}, 当前权限: {user_role}'
                    }
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def create_response(success=True, data=None, error=None):
    """创建统一响应格式"""
    response = {'success': success}
    if data is not None:
        response['data'] = data
    if error is not None:
        response['error'] = error
    return jsonify(response)
```

### 2.2 创建工具函数 (api/utils.py)

```python
import sqlite3
from datetime import datetime

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
    return conn

def validate_dispatch_data(data):
    """验证派车任务数据"""
    required_fields = ['title', 'vehicle_type', 'purpose', 'start_location', 'end_location']
    
    for field in required_fields:
        if not data.get(field):
            return False, f'缺少必填字段: {field}'
    
    # 验证dispatch_track
    if data.get('dispatch_track') not in ['轨道A', '轨道B']:
        return False, 'dispatch_track必须是"轨道A"或"轨道B"'
    
    # 验证时间格式
    try:
        if data.get('expected_start_time'):
            datetime.strptime(data['expected_start_time'], '%Y-%m-%d %H:%M')
        if data.get('expected_end_time'):
            datetime.strptime(data['expected_end_time'], '%Y-%m-%d %H:%M')
    except ValueError:
        return False, '时间格式错误，应为YYYY-MM-DD HH:MM'
    
    return True, None

def generate_task_id():
    """生成任务ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y%m%d')
    cursor.execute("SELECT COUNT(*) FROM manual_dispatch_tasks WHERE task_id LIKE ?", 
                   [f'T{today}%'])
    count = cursor.fetchone()[0]
    
    conn.close()
    return f'T{today}{str(count + 1).zfill(3)}'
```

## 🚀 第三步：实现核心API接口

### 3.1 创建派车任务接口（提交车辆需求） (api/dispatch.py)

```python
from flask import Blueprint, request, jsonify
from api.decorators import require_role, create_response
from api.utils import validate_dispatch_data, generate_task_id
from db_manager import DatabaseManager
import datetime

dispatch_bp = Blueprint('dispatch', __name__, url_prefix='/api/dispatch')

@dispatch_bp.route('/tasks', methods=['POST'])
@require_role(['车间地调', '区域调度员', '超级管理员'])
def create_task():
    """
    创建派车任务（提交车辆需求）
    
    业务场景：
    - 车间地调：提交车辆需求 → 创建轨道A任务
    - 区域调度员：直接创建派车任务 → 创建轨道B任务
    """
    try:
        data = request.get_json()
        
        # 验证数据
        is_valid, error_msg = validate_dispatch_data(data)
        if not is_valid:
            return create_response(success=False, error={
                'code': 4001,
                'message': error_msg
            }), 400
        
        # 生成任务ID
        task_id = generate_task_id()
        
        # 确定初始状态和处理者（基于用户角色和轨道类型）
        user_role = session.get('user_role')
        dispatch_track = data.get('dispatch_track', '轨道A')
        
        if user_role == '车间地调':
            # 车间地调只能创建轨道A任务
            dispatch_track = '轨道A'
            status = '待提交'
            current_handler_role = '车间地调'
            message = '车辆需求提交成功，请在任务列表中提交审核'
        elif user_role in ['区域调度员', '超级管理员']:
            # 区域调度员和超级管理员可以选择轨道
            if dispatch_track == '轨道A':
                status = '待区域调度员审核'
                current_handler_role = '区域调度员'
                message = '派车任务创建成功，等待区域调度员审核'
            else:  # 轨道B
                status = '待供应商响应'
                current_handler_role = '供应商'
                message = '派车任务创建成功，等待供应商响应'
        else:
            return create_response(success=False, error={
                'code': 4002,
                'message': '无权限创建派车任务'
            }), 403
        
        # 插入数据库
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            db_manager.cursor.execute('''
                INSERT INTO manual_dispatch_tasks (
                    task_id, required_date, start_bureau, route_direction, carrier_company,
                    route_name, transport_type, requirement_type, volume, weight,
                    special_requirements, status, dispatch_track, initiator_role,
                    current_handler_role, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                task_id, 
                data.get('required_time', '').split('T')[0],  # 提取日期部分
                data.get('start_location'),
                data.get('end_location'),  # 路向
                data.get('carrier_company'),
                data.get('route_name', data.get('end_location')),  # 邮路名称
                data.get('transport_type'),
                data.get('requirement_type'),
                data.get('volume'),
                data.get('weight'),
                data.get('special_requirements'),
                status,
                dispatch_track,
                user_role,
                current_handler_role,
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        conn.commit()
        conn.close()
        
        return create_response(data={
            'task_id': task_id,
            'status': status,
            'dispatch_track': dispatch_track,
            'current_handler_role': current_handler_role
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'创建任务失败: {str(e)}'
        }), 500

@dispatch_bp.route('/tasks', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def get_tasks():
    """获取任务列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status = request.args.get('status')
        dispatch_track = request.args.get('dispatch_track')
        
        # 计算分页
        offset = (page - 1) * limit
        
        # 构建查询
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM manual_dispatch_tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if dispatch_track:
            query += " AND dispatch_track = ?"
            params.append(dispatch_track)
        
        # 获取总数
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return create_response(data={
            'list': tasks,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取任务列表失败: {str(e)}'
        }), 500
```

### 3.2 创建任务审核接口

继续在 `api/dispatch.py` 中添加：

```python
@dispatch_bp.route('/tasks/<task_id>/audit', methods=['POST'])
@require_role(['区域调度员', '超级管理员', '供应商'])
def audit_task(task_id):
    """审核任务"""
    try:
        data = request.get_json()
        action = data.get('action')  # approve/reject
        comments = data.get('comments', '')
        
        if action not in ['approve', 'reject']:
            return create_response(success=False, error={
                'code': 4001,
                'message': 'action必须是approve或reject'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取任务信息
        cursor.execute("SELECT * FROM manual_dispatch_tasks WHERE task_id = ?", [task_id])
        task = cursor.fetchone()
        
        if not task:
            conn.close()
            return create_response(success=False, error={
                'code': 4003,
                'message': '任务不存在'
            }), 404
        
        task = dict(task)
        current_handler = session.get('user_role')
        
        # 验证当前用户是否有权限审核
        if task['current_handler_role'] != current_handler:
            conn.close()
            return create_response(success=False, error={
                'code': 4002,
                'message': f'当前需要{task["current_handler_role"]}审核'
            }), 403
        
        # 根据轨道和当前状态确定下一个状态
        new_status = None
        next_handler = None
        
        if task['dispatch_track'] == '轨道A':
            if task['status'] == '待区域调度员审核' and current_handler == '区域调度员':
                if action == 'approve':
                    new_status = '待供应商响应'
                    next_handler = '供应商'
                else:
                    new_status = '区域调度员驳回'
                    next_handler = '车间地调'
            elif task['status'] == '待供应商响应' and current_handler == '供应商':
                if action == 'approve':
                    new_status = '已响应'
                    next_handler = '车间'
                # 供应商不允许驳回，只能确认接单
            elif task['status'] == '待供应商响应' and current_handler == '供应商':
                if action == 'approve':
                    new_status = '待司机接单'
                    next_handler = '司机'
                else:
                    new_status = '供应商驳回'
                    next_handler = '区域调度员'
        
        else:  # 轨道B
            if task['status'] == '待供应商响应' and current_handler == '供应商':
                if action == 'approve':
                    new_status = '已响应'
                    next_handler = '车间'
                # 供应商不允许驳回，只能确认接单
            elif task['status'] == '待供应商响应' and current_handler == '供应商':
                if action == 'approve':
                    new_status = '待司机接单'
                    next_handler = '司机'
                else:
                    new_status = '供应商驳回'
                    next_handler = '区域调度员'
        
        if new_status and next_handler:
            cursor.execute('''
                UPDATE manual_dispatch_tasks 
                SET status = ?, current_handler_role = ?, updated_at = ?
                WHERE task_id = ?
            ''', [new_status, next_handler, datetime.datetime.now(), task_id])
            
            # 记录审核历史
            cursor.execute('''
                INSERT INTO dispatch_status_history (task_id, status, handler_role, 
                                                   handler_name, comments, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [task_id, new_status, current_handler, 
                  session.get('username', current_handler), comments, datetime.datetime.now()])
            
            conn.commit()
        
        conn.close()
        
        return create_response(data={
            'task_id': task_id,
            'status': new_status,
            'current_handler_role': next_handler
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'审核失败: {str(e)}'
        }), 500
```

## 🔗 第四步：集成到主应用

### 4.1 修改app.py注册API路由

在 `app.py` 中添加：

```python
# 在文件顶部添加导入
from api.dispatch import dispatch_bp

# 在create_app函数中注册蓝图
app.register_blueprint(dispatch_bp)
```

### 4.2 测试API接口

创建测试脚本 `test_api.py`：

```python
import requests
import json

# 测试创建任务
def test_create_task():
    url = "http://localhost:5000/api/dispatch/tasks"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "title": "测试API创建任务",
        "vehicle_type": "货车",
        "purpose": "测试",
        "start_location": "起点",
        "end_location": "终点",
        "dispatch_track": "轨道A",
        "expected_start_time": "2024-01-15 08:00",
        "expected_end_time": "2024-01-15 18:00"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print("创建任务响应:", response.json())

if __name__ == "__main__":
    test_create_task()
```

## ✅ 第五步：验证和测试

### 5.1 启动服务测试

```bash
# 启动Flask应用
python app.py

# 在浏览器中访问测试
# http://localhost:5000/api/dispatch/tasks
```

### 5.2 使用curl测试

```bash
# 测试获取任务列表
curl -X GET http://localhost:5000/api/dispatch/tasks

# 测试创建任务
curl -X POST http://localhost:5000/api/dispatch/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"测试任务","vehicle_type":"货车","purpose":"测试","start_location":"A","end_location":"B","dispatch_track":"轨道A"}'
```

## 📊 第六步：性能优化建议

### 6.1 数据库优化
- 为常用查询字段添加索引
- 使用连接池管理数据库连接

### 6.2 缓存策略
- 对频繁查询的数据使用Redis缓存
- 实现接口级别的缓存

### 6.3 监控和日志
- 添加API调用日志
- 实现性能监控指标

## 🎯 部署检查清单

- [ ] 所有API接口测试通过
- [ ] 权限验证正常工作
- [ ] 数据库连接稳定
- [ ] 错误处理机制完善
- [ ] 文档已更新
- [ ] 性能测试完成

## 📞 技术支持

如有问题，请参考：
- API_DESIGN.md - 详细接口设计
- DATABASE_DESIGN.md - 数据库设计
- 开发日志.docx - 开发记录