from flask import Blueprint, request, jsonify, session
from api.decorators import require_role, create_response
from api.utils import validate_dispatch_data, generate_task_id
from db_manager import DatabaseManager
import datetime

dispatch_bp = Blueprint('dispatch', __name__, url_prefix='/api/dispatch')

@dispatch_bp.route('/tasks', methods=['POST'])
@require_role(['车间地调', '区域调度员', '超级管理员'])
def create_task():
    """创建派车任务"""
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
        
        # 获取用户角色（单一角色）
        user_role = session.get('user_role')
        dispatch_track = data.get('dispatch_track', '轨道A')
        
        # 根据用户角色和轨道类型确定处理逻辑（严格遵循文档规范）
        if user_role == '车间地调':
            # 车间地调只能创建轨道A任务，需要区域调度员审核
            dispatch_track = '轨道A'  # 车间地调强制使用轨道A
            status = '待调度员审核'
            current_handler_role = '区域调度员'
            initiator_role = '车间地调'
        elif user_role == '区域调度员':
            # 区域调度员可以创建轨道A或轨道B任务
            if dispatch_track == '轨道A':
                # 轨道A：区域调度员创建后仍需审核（可能是为他人创建）
                status = '待调度员审核'
                current_handler_role = '区域调度员'
            else:  # 轨道B
                # 轨道B：区域调度员直接派车，跳过审核环节
                status = '待供应商响应'
                current_handler_role = '供应商'
            initiator_role = '区域调度员'
        elif user_role == '超级管理员':
            # 超级管理员可以创建轨道A或轨道B任务
            if dispatch_track == '轨道A':
                # 轨道A：超级管理员创建后仍需审核
                status = '待调度员审核'
                current_handler_role = '区域调度员'
            else:  # 轨道B
                # 轨道B：超级管理员直接派车，跳过审核环节
                status = '待供应商响应'
                current_handler_role = '供应商'
            initiator_role = '超级管理员'
        else:
            return create_response(success=False, error={
                'code': 4002,
                'message': '无权限创建派车任务'
            }), 403
        
        # 获取当前用户ID
        current_user_id = session.get('user_id')
        if not current_user_id:
            return create_response(success=False, error={
                'code': 4002,
                'message': '未登录用户'
            }), 401
            
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
                    status, dispatch_track, initiator_role, current_handler_role,
                    created_at, updated_at, special_requirements, initiator_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                task_id, data.get('required_time'), data.get('start_location'), 
                f"{data.get('start_location')}-{data.get('end_location')}", data.get('carrier_company'),
                data.get('end_location'), data.get('transport_type'), 
                data.get('requirement_type'), data.get('volume'), data.get('weight'),
                status, dispatch_track, initiator_role, current_handler_role,
                datetime.datetime.now(), datetime.datetime.now(), data.get('special_requirements', ''),
                current_user_id
            ])
            
            db_manager.conn.commit()
        finally:
            db_manager.disconnect()
        
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
        
        # 计算分页
        offset = (page - 1) * limit
        
        # 构建查询
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 获取当前用户信息
            current_user_id = session.get('user_id')
            if not current_user_id:
                return create_response(success=False, error={
                    'code': 4002,
                    'message': '未登录用户'
                }), 401
                
            # 获取当前用户创建的任务总数
            total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE initiator_user_id = ?"
            db_manager.cursor.execute(total_query, [current_user_id])
            total = db_manager.cursor.fetchone()[0]
            
            # 获取当前用户创建的任务 - 按创建时间倒序
            query = """
                SELECT * FROM manual_dispatch_tasks 
                WHERE initiator_user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            db_manager.cursor.execute(query, [current_user_id, limit, offset])
            rows = db_manager.cursor.fetchall()
                
            # 转换为字典列表
            tasks = []
            for row in rows:
                task = {}
                for i, col in enumerate(db_manager.cursor.description):
                    task[col[0]] = row[i]
                tasks.append(task)
            
        except Exception as e:
            db_manager.disconnect()
            raise e
            
        db_manager.disconnect()
        
        return create_response(data={
            'list': tasks,
            'total': total,
            'page': page,
            'limit': limit
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': str(e)
        }), 500

@dispatch_bp.route('/tasks/<task_id>', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def get_task_detail(task_id):
    """获取单个任务详情"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            db_manager.cursor.execute('SELECT * FROM manual_dispatch_tasks WHERE task_id = ?', (task_id,))
            task = db_manager.cursor.fetchone()
            
            if not task:
                return create_response(success=False, error={
                    'code': 4041,
                    'message': '任务不存在'
                }), 404
            
            # 获取状态历史
            db_manager.cursor.execute('''
                SELECT * FROM dispatch_status_history 
                WHERE task_id = ? 
                ORDER BY created_at DESC
            ''', (task_id,))
            history = [dict(row) for row in db_manager.cursor.fetchall()]
            
            task_data = dict(task)
            task_data['history'] = history
            
        finally:
            db_manager.disconnect()
        
        return create_response(data=task_data)
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取任务详情失败: {str(e)}'
        }), 500

@dispatch_bp.route('/user/info', methods=['GET'])
def get_user_info():
    """获取当前用户信息（用于登录状态检查）"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': {
                    'code': 4002,
                    'message': '未登录'
                }
            }), 401
        
        return create_response(data={
            'user_id': session['user_id'],
            'user_role': session.get('user_role'),
            'is_logged_in': True
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@dispatch_bp.route('/tasks/<task_id>', methods=['PUT'])
@require_role(['车间地调', '区域调度员', '超级管理员'])
def update_task(task_id):
    """更新任务信息"""
    try:
        data = request.get_json()
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查任务是否存在
            db_manager.cursor.execute('SELECT * FROM manual_dispatch_tasks WHERE task_id = ?', (task_id,))
            task = db_manager.cursor.fetchone()
            
            if not task:
                return create_response(success=False, error={
                    'code': 4041,
                    'message': '任务不存在'
                }), 404
            
            # 构建更新字段
            update_fields = []
            params = []
            
            allowed_fields = [
                'title', 'vehicle_type', 'purpose', 'start_location', 'end_location',
                'expected_start_time', 'expected_end_time', 'passenger_count',
                'cargo_weight', 'cargo_volume', 'special_requirements'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    params.append(data[field])
            
            if update_fields:
                update_fields.append("updated_at = ?")
                params.append(datetime.datetime.now())
                params.append(task_id)
                
                query = f"UPDATE manual_dispatch_tasks SET {', '.join(update_fields)} WHERE task_id = ?"
                db_manager.cursor.execute(query, params)
                db_manager.conn.commit()
            
        finally:
            db_manager.disconnect()
        
        return create_response(message='任务更新成功')
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'更新任务失败: {str(e)}'
        }), 500