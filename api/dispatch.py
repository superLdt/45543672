from flask import Blueprint, request, jsonify
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
        
        # 确定初始状态和处理者
        initiator_role = session.get('user_role')
        dispatch_track = data.get('dispatch_track', '轨道A')
        
        if initiator_role == '车间地调':
            # 车间地调只能创建轨道A任务
            dispatch_track = '轨道A'
            status = '待提交'
            current_handler_role = '车间地调'
        elif initiator_role in ['区域调度员', '超级管理员']:
            # 区域调度员和超级管理员可以选择轨道
            if dispatch_track == '轨道A':
                status = '待区域调度员审核'
                current_handler_role = '区域调度员'
            else:  # 轨道B
                status = '待供应商响应'
                current_handler_role = '供应商'
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
                    task_id, title, vehicle_type, purpose, start_location, end_location,
                    expected_start_time, expected_end_time, dispatch_track, initiator_role,
                    current_handler_role, status, passenger_count, cargo_weight, cargo_volume,
                    special_requirements, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                task_id, data['title'], data['vehicle_type'], data['purpose'],
                data['start_location'], data['end_location'],
                data.get('expected_start_time'), data.get('expected_end_time'),
                dispatch_track, initiator_role, current_handler_role, status,
                data.get('passenger_count'), data.get('cargo_weight'),
                data.get('cargo_volume'), data.get('special_requirements'),
                datetime.datetime.now(), datetime.datetime.now()
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
        status = request.args.get('status')
        dispatch_track = request.args.get('dispatch_track')
        
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
            db_manager.cursor.execute(count_query, params)
            total = db_manager.cursor.fetchone()[0]
            
            # 获取分页数据
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            db_manager.cursor.execute(query, params)
            tasks = [dict(row) for row in db_manager.cursor.fetchall()]
            
        finally:
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
            'message': f'获取任务列表失败: {str(e)}'
        }), 500