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
            # 准备任务数据
            task_data = {
                'required_date': data.get('required_time'),
                'start_bureau': data.get('start_location'),
                'route_direction': f"{data.get('start_location')}-{data.get('end_location')}",
                'carrier_company': data.get('carrier_company'),
                'route_name': data.get('end_location'),
                'transport_type': data.get('transport_type'),
                'requirement_type': data.get('requirement_type'),
                'volume': data.get('volume'),
                'weight': data.get('weight'),
                'special_requirements': data.get('special_requirements', ''),
                'initiator_role': initiator_role,
                'initiator_user_id': current_user_id,
                'current_handler_user_id': current_user_id,
                'operator': current_user_id  # 用于状态历史记录
            }
            
            # 调用数据库管理类的方法创建任务
            result = db_manager.create_dispatch_task(task_data)
            
            if not result['success']:
                return create_response(success=False, error={
                    'code': 5001,
                    'message': f'创建任务失败: {result.get("error", "未知错误")}'
                }), 500
                
            # 使用数据库生成的任务ID
            task_id = result['task_id']
            
        finally:
            db_manager.disconnect()
        
        # 获取创建的任务详情，以确保返回正确的状态信息
        task_detail = db_manager.get_dispatch_task_detail(task_id)
        
        return create_response(data={
            'task_id': task_id,
            'status': task_detail['status'] if task_detail else '未知',
            'dispatch_track': task_detail['dispatch_track'] if task_detail else dispatch_track,
            'current_handler_role': task_detail['current_handler_role'] if task_detail else current_handler_role
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'创建任务失败: {str(e)}'
        }), 500

@dispatch_bp.route('/tasks', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def get_tasks():
    """获取任务列表 - 根据用户角色返回不同的任务范围"""
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
            current_user_role = session.get('user_role')
            
            if not current_user_id:
                return create_response(success=False, error={
                    'code': 4002,
                    'message': '未登录用户'
                }), 401
            
            # 根据用户角色确定查询条件 - 优化查询性能
            if current_user_role in ['超级管理员', '区域调度员']:
                # 超级管理员和区域调度员可以看到所有任务
                total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks"
                query = """
                    SELECT task_id, required_date, start_bureau, route_name, carrier_company, 
                           transport_type, requirement_type, volume, weight, status, 
                           created_at, updated_at, special_requirements
                    FROM manual_dispatch_tasks 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """
                params = [limit, offset]
            elif current_user_role == '供应商':
                # 供应商只能看到分配给自己的任务
                total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE assigned_supplier_id = ?"
                query = """
                    SELECT task_id, required_date, start_bureau, route_name, carrier_company, 
                           transport_type, requirement_type, volume, weight, status, 
                           created_at, updated_at, special_requirements
                    FROM manual_dispatch_tasks 
                    WHERE assigned_supplier_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """
                params = [current_user_id, limit, offset]
            else:
                # 车间地调只能看到自己创建的任务
                total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE initiator_user_id = ?"
                query = """
                    SELECT task_id, required_date, start_bureau, route_name, carrier_company, 
                           transport_type, requirement_type, volume, weight, status, 
                           created_at, updated_at, special_requirements
                    FROM manual_dispatch_tasks 
                    WHERE initiator_user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """
                params = [current_user_id, limit, offset]
            
            # 执行总数查询
            if current_user_role in ['超级管理员', '区域调度员']:
                db_manager.cursor.execute(total_query)
            elif current_user_role == '供应商':
                db_manager.cursor.execute(total_query, [current_user_id])
            else:
                db_manager.cursor.execute(total_query, [current_user_id])
            total = db_manager.cursor.fetchone()[0]
            
            # 执行任务查询
            db_manager.cursor.execute(query, params)
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
            
            # 获取列名并构建任务数据字典
            columns = [description[0] for description in db_manager.cursor.description]
            task_data = dict(zip(columns, task))
            
            # 获取状态历史
            db_manager.cursor.execute('''
                SELECT status_change as status, timestamp, operator as updated_by, note as notes
                FROM dispatch_status_history
                WHERE task_id = ?
                ORDER BY timestamp DESC
            ''', (task_id,))
            
            # 手动构建状态历史字典
            history = []
            for row in db_manager.cursor.fetchall():
                history.append({
                    'status': row[0],
                    'timestamp': row[1],
                    'updated_by': row[2],
                    'notes': row[3]
                })
            
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

@dispatch_bp.route('/statistics', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def get_statistics():
    """获取任务统计信息"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 获取当前用户信息
            current_user_id = session.get('user_id')
            current_user_role = session.get('user_role')
            
            if not current_user_id:
                return create_response(success=False, error={
                    'code': 4002,
                    'message': '未登录用户'
                }), 401
            
            # 根据用户角色确定查询条件
            base_where = ""
            params = []
            
            if current_user_role == '供应商':
                base_where = "WHERE assigned_supplier_id = ?"
                params = [current_user_id]
            elif current_user_role == '车间地调':
                base_where = "WHERE initiator_user_id = ?"
                params = [current_user_id]
            
            # 获取总任务数
            query = f"SELECT COUNT(*) FROM manual_dispatch_tasks {base_where}" if base_where else "SELECT COUNT(*) FROM manual_dispatch_tasks"
            db_manager.cursor.execute(query, params)
            total_tasks = db_manager.cursor.fetchone()[0]
            
            # 获取各状态任务数
            status_counts = {}
            for status in ['待提交', '待调度员审核', '待供应商响应', '供应商已响应', 
                          '车间已核查', '供应商已确认', '任务结束', '已取消']:
                if base_where:
                    query = f"SELECT COUNT(*) FROM manual_dispatch_tasks {base_where} AND status = ?"
                    db_manager.cursor.execute(query, params + [status])
                else:
                    query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE status = ?"
                    db_manager.cursor.execute(query, [status])
                status_counts[status] = db_manager.cursor.fetchone()[0]
            
            # 获取今日新增任务数
            today = datetime.date.today()
            if base_where:
                query = f"SELECT COUNT(*) FROM manual_dispatch_tasks {base_where} AND DATE(created_at) = ?"
                db_manager.cursor.execute(query, params + [today.isoformat()])
            else:
                query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE DATE(created_at) = ?"
                db_manager.cursor.execute(query, [today.isoformat()])
            today_new_tasks = db_manager.cursor.fetchone()[0]
            
            # 获取即将超时任务（24小时内需要处理的任务）
            tomorrow = today + datetime.timedelta(days=1)
            if base_where:
                query = f"""
                    SELECT COUNT(*) FROM manual_dispatch_tasks 
                    {base_where} AND status IN ('待提交', '待调度员审核', '待供应商响应') 
                    AND required_date <= ?
                """
                db_manager.cursor.execute(query, params + [tomorrow.isoformat()])
            else:
                query = """
                    SELECT COUNT(*) FROM manual_dispatch_tasks 
                    WHERE status IN ('待提交', '待调度员审核', '待供应商响应') 
                    AND required_date <= ?
                """
                db_manager.cursor.execute(query, [tomorrow.isoformat()])
            urgent_tasks = db_manager.cursor.fetchone()[0]
            
            # 获取轨道类型分布
            track_counts = {}
            for track in ['轨道A', '轨道B']:
                if base_where:
                    query = f"SELECT COUNT(*) FROM manual_dispatch_tasks {base_where} AND dispatch_track = ?"
                    db_manager.cursor.execute(query, params + [track])
                else:
                    query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE dispatch_track = ?"
                    db_manager.cursor.execute(query, [track])
                track_counts[track] = db_manager.cursor.fetchone()[0]
            
        finally:
            db_manager.disconnect()
        
        return create_response(data={
            'total_tasks': total_tasks,
            'status_counts': status_counts,
            'today_new_tasks': today_new_tasks,
            'urgent_tasks': urgent_tasks,
            'track_counts': track_counts
        })
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500