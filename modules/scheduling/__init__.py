from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

def require_role(allowed_roles):
    """装饰器：检查用户是否拥有指定角色之一"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_roles = current_user.roles if hasattr(current_user, 'roles') else []
            if not any(role in allowed_roles for role in user_roles):
                return render_template('error.html', 
                                     message='权限不足', 
                                     description=f'此功能仅对以下角色开放：{", ".join(allowed_roles)}',
                                     code=403), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

scheduling_bp = Blueprint('scheduling_bp', __name__, template_folder='templates')

@scheduling_bp.route('/')
@login_required
def index():
    return render_template('scheduling/index.html', user=current_user)

@scheduling_bp.route('/vehicles')
@login_required
def vehicle_management():
    return render_template('scheduling/vehicles.html', title='车辆管理', user=current_user)

@scheduling_bp.route('/tasks')
@login_required
def task_assignment():
    return render_template('scheduling/tasks.html', title='任务分配', user=current_user)

@scheduling_bp.route('/manual-dispatch')
@login_required
def manual_dispatch():
    user_roles = current_user.roles if hasattr(current_user, 'roles') else []
    
    if '车间地调' in user_roles:
        # 车间地调进入车辆需求页面
        return render_template('scheduling/vehicle_requirements.html', title='车辆需求', user=current_user)
    elif any(role in ['超级管理员', '区域调度员'] for role in user_roles):
        # 区域调度员和超级管理员进入人工派车页面
        return render_template('scheduling/manual_dispatch.html', title='人工派车', user=current_user)
    else:
        # 其他用户无权限访问
        return render_template('error.html', 
                             message='权限不足', 
                             description='您没有权限访问人工派车功能。请联系系统管理员获取相应权限。',
                             code=403), 403

@scheduling_bp.route('/task-management')
@login_required
def task_management():
    """任务管理页面"""
    return render_template('scheduling/task_management.html', title='任务管理', user=current_user)

@scheduling_bp.route('/submit-requirement', methods=['POST'])
@login_required
def submit_requirement():
    """处理车辆需求提交"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['requirement_type', 'start_location', 'end_location', 
                          'carrier_company', 'transport_type', 'weight', 'volume', 'required_time']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} 为必填字段'}), 400
        
        # 验证重量和容积的对应关系
        weight_volume_map = {
            '5': 35,
            '8': 45,
            '12': 55,
            '20': 100,
            '30': 130,
            '40A': 150,
            '40B': 180
        }
        
        weight = str(data['weight'])
        volume = int(data['volume'])
        
        if weight not in weight_volume_map:
            return jsonify({'error': '无效的重量选择'}), 400
        
        min_volume = weight_volume_map[weight]
        if volume < min_volume:
            return jsonify({'error': f'容积必须大于等于 {min_volume} 立方米'}), 400
        
        # 检查下一个重量等级的容积限制
        next_weight_limits = {
            '5': 45,
            '8': 55,
            '12': 100,
            '20': 130,
            '30': 150,
            '40A': 180,
            '40B': None
        }
        
        max_volume = next_weight_limits[weight]
        if max_volume and volume >= max_volume:
            return jsonify({'error': f'容积必须小于 {max_volume} 立方米'}), 400
        
        # 这里应该保存到数据库
        # 模拟保存成功
        requirement_data = {
            'requirement_type': data.get('requirement_type'),
            'start_location': data.get('start_location'),
            'end_location': data.get('end_location'),
            'carrier_company': data.get('carrier_company'),
            'transport_type': data.get('transport_type'),
            'weight': weight,
            'volume': volume,
            'required_time': data.get('required_time'),
            'special_requirements': data.get('special_requirements'),
            'status': '待处理',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': current_user.full_name if hasattr(current_user, 'full_name') else '未知用户'
        }
        
        return jsonify({
            'success': True,
            'message': '车辆需求申请已提交成功！',
            'data': requirement_data
        })
        
    except ValueError as e:
        return jsonify({'error': '容积必须为数字'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
