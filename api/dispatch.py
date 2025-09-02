from flask import Blueprint, request, jsonify, session
from api.decorators import require_role, create_response
from api.utils import validate_dispatch_data, generate_task_id
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
import datetime
import sqlite3

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
                'assigned_supplier_id': data.get('assigned_supplier_id'),
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
                # 供应商只能看到分配给自己的任务或与自己公司相关的任务
                # 首先获取供应商所属的公司ID
                db_manager.cursor.execute("SELECT company_id FROM User WHERE id = ?", [current_user_id])
                company_row = db_manager.cursor.fetchone()
                if company_row:
                    company_id = company_row[0]
                    total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE assigned_supplier_id = ? OR carrier_company = (SELECT name FROM Company WHERE id = ?)"
                    query = """
                        SELECT task_id, required_date, start_bureau, route_name, carrier_company, 
                               transport_type, requirement_type, volume, weight, status, 
                               created_at, updated_at, special_requirements
                        FROM manual_dispatch_tasks 
                        WHERE assigned_supplier_id = ? OR carrier_company = (SELECT name FROM Company WHERE id = ?)
                        ORDER BY created_at DESC 
                        LIMIT ? OFFSET ?
                    """
                    params = [current_user_id, company_id, limit, offset]
                else:
                    # 如果没有找到公司信息，则只显示直接分配给供应商的任务
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
                # 车间地调可以看到所有状态为'供应商已响应'的任务
                total_query = "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE status = '供应商已响应'"
                query = """
                    SELECT task_id, required_date, start_bureau, route_name, carrier_company, 
                           transport_type, requirement_type, volume, weight, status, 
                           created_at, updated_at, special_requirements
                    FROM manual_dispatch_tasks 
                    WHERE status = '供应商已响应' 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """
                params = [limit, offset]
            
            # 执行总数查询
            if current_user_role in ['超级管理员', '区域调度员']:
                db_manager.cursor.execute(total_query)
            elif current_user_role == '供应商':
                # 为供应商角色正确传递参数
                if company_row and company_row[0]:
                    # 当有公司信息时，传递两个参数
                    db_manager.cursor.execute(total_query, [current_user_id, company_id])
                else:
                    # 当无公司信息时，只传递一个参数
                    db_manager.cursor.execute(total_query, [current_user_id])
            elif current_user_role == '车间地调':
                # 车间地调角色查询不需要参数
                db_manager.cursor.execute(total_query)
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
                SELECT h.status_change as status, h.timestamp, h.operator as updated_by_id, h.note as notes, u.full_name as updated_by_name
                FROM dispatch_status_history h
                LEFT JOIN User u ON h.operator = u.id
                WHERE h.task_id = ?
                ORDER BY h.timestamp DESC
            ''', (task_id,))
            
            # 手动构建状态历史字典
            history = []
            for row in db_manager.cursor.fetchall():
                history.append({
                    'status': row[0],
                    'timestamp': row[1],
                    'updated_by': row[4] or f'用户{row[2]}',  # 使用用户名，如果没有则使用ID
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
        
        return create_response(data={'message': '任务更新成功'})
        
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'更新任务失败: {str(e)}'
        }), 500

@dispatch_bp.route('/tasks/<task_id>/confirm', methods=['POST'])
@require_role(['供应商'])
def confirm_supplier_response(task_id):
    """供应商确认响应派车"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 检查任务是否存在
            db_manager.cursor.execute('''
                SELECT * FROM manual_dispatch_tasks 
                WHERE task_id = ?
            ''', (task_id,))
            
            task = db_manager.cursor.fetchone()
            if not task:
                return create_response(success=False, error={
                    'code': 4041,
                    'message': '任务不存在'
                }), 404
            
            # 检查任务状态是否为"待供应商响应"
            if task['status'] != '待供应商响应':
                return create_response(success=False, error={
                    'code': 4042,
                    'message': f'任务状态不正确，当前状态为: {task["status"]}'
                }), 404
            
            # 检查是否已经存在车辆信息
            db_manager.cursor.execute('''
                SELECT COUNT(*) as count FROM vehicles 
                WHERE task_id = ?
            ''', (task_id,))
            
            vehicle_count = db_manager.cursor.fetchone()['count']
            if vehicle_count > 0:
                return create_response(success=False, error={
                    'code': 4003,
                    'message': '该任务已存在车辆信息，不能重复提交'
                }), 400
            
            # 获取当前用户信息
            current_user_id = session.get('user_id')
            if not current_user_id:
                return create_response(success=False, error={
                    'code': 4002,
                    'message': '未登录用户'
                }), 401
                
            # 获取当前用户名
            db_manager.cursor.execute('''
                SELECT username FROM User WHERE id = ?
            ''', (current_user_id,))
            user_result = db_manager.cursor.fetchone()
            current_username = user_result['username'] if user_result else str(current_user_id)
            
            # 更新任务状态为"供应商已响应"
            new_status = '供应商已响应'
            # 获取旧状态，注意task是sqlite3.Row对象，可以通过列名访问
            old_status = task['status']
            
            db_manager.cursor.execute('''
                UPDATE manual_dispatch_tasks 
                SET status = ?, current_handler_user_id = ?, updated_at = ?
                WHERE task_id = ?
            ''', (new_status, current_user_id, datetime.datetime.now(), task_id))
            
            # 记录状态变更历史
            db_manager.cursor.execute('''
                INSERT INTO dispatch_status_history (task_id, status_change, operator, note)
                VALUES (?, ?, ?, ?)
            ''', (task_id, f"{old_status}→{new_status}", current_username, '供应商确认响应'))
            
            db_manager.conn.commit()
            
            return create_response(data={
                'message': '供应商响应成功',
                'task_id': task_id,
                'new_status': new_status
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'供应商响应失败: {str(e)}'
        }), 500

@dispatch_bp.route('/tasks/<task_id>/confirm-with-vehicle', methods=['POST'])
@require_role(['供应商'])
def confirm_supplier_response_with_vehicle(task_id):
    """供应商确认响应并填写车辆信息"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'数据库连接异常: {str(e)}'
        }), 500
        
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return create_response(success=False, error={
                'code': 4001,
                'message': '请求数据格式错误'
            }), 400
            
        # 验证必填字段
        required_fields = ['manifest_number', 'dispatch_number', 'license_plate']
        for field in required_fields:
            if not data.get(field):
                return create_response(success=False, error={
                    'code': 4001,
                    'message': f'{field}不能为空'
                }), 400
        
        # 检查任务是否存在且状态为"待供应商响应"
        db_manager.cursor.execute('''
            SELECT * FROM manual_dispatch_tasks 
            WHERE task_id = ? AND status = ?
        ''', (task_id, '待供应商响应'))
        
        task = db_manager.cursor.fetchone()
        if not task:
            return create_response(success=False, error={
                'code': 4041,
                'message': '任务不存在或状态不正确'
            }), 404
        
        # 检查是否已经存在车辆信息，避免重复提交
        db_manager.cursor.execute('''
            SELECT COUNT(*) as count FROM vehicles 
            WHERE task_id = ?
        ''', (task_id,))
        
        vehicle_count = db_manager.cursor.fetchone()['count']
        if vehicle_count > 0:
            return create_response(success=False, error={
                'code': 4003,
                'message': '该任务已存在车辆信息，不能重复提交'
            }), 400
        
        # 获取当前用户信息
        current_user_id = session.get('user_id')
        if not current_user_id:
            return create_response(success=False, error={
                'code': 4002,
                'message': '未登录用户'
            }), 401
            
        # 获取当前用户名
        db_manager.cursor.execute('''
            SELECT username FROM User WHERE id = ?
        ''', (current_user_id,))
        user_result = db_manager.cursor.fetchone()
        current_username = user_result['username'] if user_result else str(current_user_id)
        
        # 更新任务状态为"供应商已响应"
        new_status = '供应商已响应'
        old_status = task['status']
        
        db_manager.cursor.execute('''
            UPDATE manual_dispatch_tasks 
            SET status = ?, current_handler_user_id = ?, updated_at = ?
            WHERE task_id = ?
        ''', (new_status, current_user_id, datetime.datetime.now(), task_id))
        
        # 获取任务的默认需求容积
        db_manager.cursor.execute('''
            SELECT volume FROM manual_dispatch_tasks WHERE task_id = ?
        ''', (task_id,))
        task_volume = db_manager.cursor.fetchone()
        required_volume = task_volume['volume'] if task_volume else None
        
        # 获取车辆的确认容积默认值,c
        confirmed_volume = None
        db_manager.cursor.execute('''
            SELECT standard_volume FROM vehicle_capacity_reference 
            WHERE license_plate = ?
        ''', (data['license_plate'],))
        capacity_result = db_manager.cursor.fetchone()
        if capacity_result:
            confirmed_volume = capacity_result['standard_volume']
        elif required_volume:
            confirmed_volume = required_volume
            
        # 插入车辆信息，处理唯一约束冲突
        try:
            db_manager.cursor.execute('''
                INSERT INTO vehicles (task_id, manifest_number, dispatch_number, license_plate, 
                                    carriage_number, notes, actual_volume, required_volume, 
                                    confirmed_volume, volume_photo_url, volume_modified_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                data['manifest_number'],
                data['dispatch_number'],
                data['license_plate'],
                data.get('carriage_number'),
                data.get('notes'),
                data.get('actual_volume'),
                required_volume,
                confirmed_volume,
                data.get('volume_photo_url'),
                current_user_id,  # volume_modified_by设置为当前用户ID
                datetime.datetime.now()
            ))
        except sqlite3.IntegrityError as e:
            # 处理唯一约束冲突
            db_manager.conn.rollback()  # 回滚事务
            if 'manifest_number' in str(e):
                return create_response(success=False, error={
                    'code': 4003,
                    'message': f'路单流水号 "{data["manifest_number"]}" 已存在，请使用新的号码'
                }), 400
            elif 'dispatch_number' in str(e):
                return create_response(success=False, error={
                    'code': 4004,
                    'message': f'派车单号 "{data["dispatch_number"]}" 已存在，请使用新的号码'
                }), 400
            else:
                raise
        
        # 记录状态变更历史
        db_manager.cursor.execute('''
            INSERT INTO dispatch_status_history (task_id, status_change, operator, note)
            VALUES (?, ?, ?, ?)
        ''', (task_id, f"{old_status}→{new_status}", current_username, 
              f"供应商确认响应，车辆信息已登记：{data['license_plate']}"))
        
        db_manager.conn.commit()
        
        return create_response(data={
            'message': '车辆信息提交成功，任务已确认响应',
            'task_id': task_id,
            'new_status': new_status,
            'vehicle_info': {
                'manifest_number': data['manifest_number'],
                'dispatch_number': data['dispatch_number'],
                'license_plate': data['license_plate']
            }
        })
            
    except Exception as e:
        db_manager.disconnect()
        return create_response(success=False, error={
            'code': 5001,
            'message': f'车辆信息确认失败: {str(e)}'
        }), 500
    finally:
        db_manager.disconnect()


@dispatch_bp.route('/vehicle-capacity', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员'])
def get_vehicle_capacity_reference():
    """获取车辆容积参考数据（支持分页）"""
    try:
        # 获取查询参数
        vehicle_type = request.args.get('vehicle_type')
        license_plate = request.args.get('license_plate')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # 参数验证
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
            
        offset = (page - 1) * limit
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 调用数据库管理类的方法获取分页数据
            result = db_manager.get_vehicle_capacity_reference_paginated(
                vehicle_type, license_plate, page, limit, offset
            )
            
            if not result['success']:
                return create_response(success=False, error={
                    'code': 5001,
                    'message': f'获取车辆容积参考数据失败: {result.get("error", "未知错误")}'
                }), 500
                
            return create_response(data=result)
            
        finally:
            db_manager.disconnect()
            
    except ValueError as e:
        return create_response(success=False, error={
            'code': 4001,
            'message': '分页参数格式错误'
        }), 400
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取车辆容积参考数据失败: {str(e)}'
        }), 500


@dispatch_bp.route('/vehicle-capacity', methods=['POST'])
@require_role(['区域调度员', '超级管理员'])
def upsert_vehicle_capacity_reference():
    """更新或插入车辆容积参考数据"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['license_plate', 'vehicle_type', 'standard_volume']
        for field in required_fields:
            if field not in data:
                return create_response(success=False, error={
                    'code': 4001,
                    'message': f'{field}不能为空'
                }), 400
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 调用数据库管理类的方法更新或插入车辆容积参考数据
            result = db_manager.upsert_vehicle_capacity_reference(
                data['vehicle_type'],
                data['standard_volume'],
                data['license_plate'],
                data.get('suppliers', [])
            )
            
            if not result['success']:
                return create_response(success=False, error={
                    'code': 5001,
                    'message': f'更新或插入车辆容积参考数据失败: {result.get("error", "未知错误")}'
                }), 500
                
            return create_response(data={
                'message': result['message']
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'更新或插入车辆容积参考数据失败: {str(e)}'
        }), 500


@dispatch_bp.route('/vehicle-capacity/<license_plate>', methods=['DELETE'])
@require_role(['区域调度员', '超级管理员'])
def delete_vehicle_capacity_reference(license_plate):
    """删除车辆容积参考数据"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 调用数据库管理类的方法删除车辆容积参考数据
            result = db_manager.delete_vehicle_capacity_reference(license_plate)
            
            if not result['success']:
                return create_response(success=False, error={
                    'code': 5001,
                    'message': f'删除车辆容积参考数据失败: {result.get("error", "未知错误")}'
                }), 500
                
            return create_response(data={
                'message': result['message']
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'删除车辆容积参考数据失败: {str(e)}'
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
                # 供应商可以看到分配给自己的任务或与自己公司相关的任务
                # 首先获取供应商所属的公司ID
                db_manager.cursor.execute("SELECT company_id FROM User WHERE id = ?", [current_user_id])
                company_row = db_manager.cursor.fetchone()
                if company_row:
                    company_id = company_row[0]
                    base_where = "WHERE assigned_supplier_id = ? OR carrier_company = (SELECT name FROM Company WHERE id = ?)"
                    params = [current_user_id, company_id]
                else:
                    # 如果没有找到公司信息，则只显示直接分配给供应商的任务
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
            'message': f'批量导入失败: {str(e)}'
        }), 500


@dispatch_bp.route('/vehicle-info/search', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def search_vehicle_info():
    """车辆信息搜索接口 - 支持车牌号和车厢号模糊查询
    
    功能说明：
    - 支持车牌号（license_plate）模糊查询
    - 支持车厢号（carriage_number）模糊查询
    - 返回简化格式的车辆信息，用于前端自动完成
    - 结果按车牌号排序，限制返回数量
    
    查询参数：
    - query: 搜索关键词
    - type: 搜索类型 ('license_plate' 或 'carriage_number', 默认 'license_plate')
    - limit: 返回结果数量限制 (默认10, 最大50)
    """
    try:
        # 获取查询参数
        # 从请求参数中获取搜索关键词，去除首尾空格，默认为空字符串
        query = request.args.get('query', '').strip()
        # 从请求参数中获取搜索类型，默认为 'license_plate'
        search_type = request.args.get('type', 'license_plate')
        # 从请求参数中获取返回结果数量限制，默认为10，最大不超过50
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # 检查搜索关键词是否为空，若为空则返回错误响应
        if not query:
            return create_response(success=False, error={
                'code': 4001,
                'message': '搜索关键词不能为空'
            }), 400
        
        # 验证搜索类型
        # 若搜索类型不在允许的范围内，则将其重置为默认值 'license_plate'
        if search_type not in ['license_plate', 'carriage_number']:
            search_type = 'license_plate'
        
        # 连接数据库
        # 创建数据库管理对象
        db_manager = DatabaseManager()
        # 尝试连接数据库，若连接失败则返回错误响应
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 构建搜索SQL
            if search_type == 'license_plate':
                # 搜索车牌号（只搜索单车类型）
                # 构建查询单车车牌号的SQL语句，使用模糊查询，按车牌号排序并限制返回数量
                sql = """
                    SELECT DISTINCT 
                        v.license_plate,
                        v.vehicle_type,
                        v.standard_volume as actual_volume,
                        COALESCE(c.name, '未知供应商') as supplier,
                        v.suppliers
                    FROM vehicle_capacity_reference v
                    LEFT JOIN Company c ON c.name IN (
                        SELECT value FROM json_each(v.suppliers)
                        LIMIT 1
                    )
                    WHERE v.license_plate LIKE ? AND v.vehicle_type = '单车'
                    ORDER BY v.license_plate
                    LIMIT ?
                """
                # 构建查询参数，包含模糊查询关键词和返回数量限制
                params = [f'%{query}%', limit]
            else:
                # 搜索车厢号（从vehicle_capacity_reference表中查询，只搜索挂车类型）
                # 构建查询挂车车厢号的SQL语句，使用模糊查询，按车牌号排序并限制返回数量
                sql = """
                    SELECT DISTINCT 
                        v.license_plate,
                        v.license_plate as carriage_number,
                        v.standard_volume as actual_volume,
                        v.vehicle_type,
                        COALESCE(c.name, '未知供应商') as supplier,
                        v.suppliers
                    FROM vehicle_capacity_reference v
                    LEFT JOIN Company c ON c.name IN (
                        SELECT value FROM json_each(v.suppliers)
                        LIMIT 1
                    )
                    WHERE v.vehicle_type = '挂车' AND v.license_plate LIKE ?
                    ORDER BY v.license_plate
                    LIMIT ?
                """
                # 构建查询参数，包含模糊查询关键词和返回数量限制
                params = [f'%{query}%', limit]
            
            # 执行查询
            # 使用数据库游标执行SQL查询
            db_manager.cursor.execute(sql, params)
            # 获取查询结果的所有行
            rows = db_manager.cursor.fetchall()
            
            # 处理结果
            # 初始化结果列表
            results = []
            # 遍历查询结果的每一行
            for row in rows:
                if search_type == 'license_plate':
                    # 当搜索类型为车牌号时，构建单车信息字典
                    result = {
                        'license_plate': row[0],
                        'vehicle_type': row[1],
                        # 将标准容积转换为浮点数，若为空则设为0.0
                        'actual_volume': float(row[2]) if row[2] else 0.0,
                        'supplier': row[3],
                        'carriage_number': ''  # 主车牌搜索时车厢号为空
                    }
                else:
                    # 解析供应商信息
                    # 获取供应商信息字符串，若为空则设为 '[]'
                    suppliers_str = row[5] or '[]'
                    try:
                        # 导入json模块用于解析JSON字符串
                        import json
                        # 将供应商信息字符串解析为列表
                        suppliers = json.loads(suppliers_str)
                        # 获取列表中的第一个供应商，若列表为空则设为 '未知供应商'
                        supplier = suppliers[0] if suppliers else '未知供应商'
                    except:
                        # 若解析失败，则设为 '未知供应商'
                        supplier = '未知供应商'
                    
                    # 当搜索类型为车厢号时，构建挂车信息字典
                    result = {
                        'license_plate': row[0],
                        'carriage_number': row[1] or '',
                        # 将标准容积转换为浮点数，若为空则设为0.0
                        'actual_volume': float(row[2]) if row[2] else 0.0,
                        'vehicle_type': row[3] or '挂车',
                        'supplier': supplier
                    }
                # 将处理后的车辆信息添加到结果列表中
                results.append(result)
            
            # 如果没有找到结果，尝试从车辆容积参考表中获取基础信息
            if not results and search_type == 'license_plate':
                # 从车辆容积参考表中查找
                # 构建从车辆容积参考表中查询基础信息的SQL语句
                sql = """
                    SELECT license_plate, vehicle_type, standard_volume, suppliers
                    FROM vehicle_capacity_reference
                    WHERE license_plate LIKE ?
                    ORDER BY license_plate
                    LIMIT ?
                """
                # 执行SQL查询
                db_manager.cursor.execute(sql, [f'%{query}%', limit])
                # 获取查询结果的所有行
                rows = db_manager.cursor.fetchall()
                
                # 遍历查询结果的每一行
                for row in rows:
                    # 解析供应商信息
                    # 获取供应商信息字符串，若为空则设为 '[]'
                    suppliers_str = row[3] or '[]'
                    try:
                        # 导入json模块用于解析JSON字符串
                        import json
                        # 将供应商信息字符串解析为列表
                        suppliers = json.loads(suppliers_str)
                        # 获取列表中的第一个供应商，若列表为空则设为 '未知供应商'
                        supplier = suppliers[0] if suppliers else '未知供应商'
                    except:
                        # 若解析失败，则设为 '未知供应商'
                        supplier = '未知供应商'
                    
                    # 构建基础车辆信息字典并添加到结果列表中
                    results.append({
                        'license_plate': row[0],
                        'vehicle_type': row[1],
                        # 将标准容积转换为浮点数，若为空则设为0.0
                        'actual_volume': float(row[2]) if row[2] else 0.0,
                        'supplier': supplier,
                        'carriage_number': ''
                    })
            
            # 返回包含处理结果的响应
            return create_response(data=results)
            
        finally:
            # 无论查询是否成功，都断开数据库连接
            db_manager.disconnect()
            
    except Exception as e:
        # 若发生异常，返回包含错误信息的响应
        return create_response(success=False, error={
            'code': 5001,
            'message': f'搜索失败: {str(e)}'
        }), 500

@dispatch_bp.route('/vehicle-capacity/batch-import', methods=['POST'])
@require_role(['区域调度员', '超级管理员'])
def batch_import_vehicle_capacity():
    """批量导入车辆容积参考数据"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return create_response(success=False, error={
                'code': 4001,
                'message': '未选择文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return create_response(success=False, error={
                'code': 4001,
                'message': '未选择文件'
            }), 400
        
        # 验证文件类型
        if not file.filename.endswith('.xlsx'):
            return create_response(success=False, error={
                'code': 4001,
                'message': '请上传.xlsx格式的Excel文件'
            }), 400
        
        # 读取Excel文件
        import pandas as pd
        import io
        
        try:
            # 读取Excel文件到DataFrame
            df = pd.read_excel(io.BytesIO(file.read()))
            
            # 验证必要的列
            required_columns = ['车辆类型', '标准容积', '车牌号']
            # 兼容模板中的列名"标准容积(m³)"
            if '标准容积(m³)' in df.columns and '标准容积' not in df.columns:
                df.rename(columns={'标准容积(m³)': '标准容积'}, inplace=True)
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return create_response(success=False, error={
                    'code': 4001,
                    'message': f'Excel缺少必要列: {", ".join(missing_columns)}'
                }), 400
            
            # 数据验证和转换
            errors = []
            valid_records = []
            
            for index, row in df.iterrows():
                row_num = index + 2  # Excel行号（从2开始，因为第1行是表头）
                
                # 验证必填字段
                if pd.isna(row['车辆类型']) or str(row['车辆类型']).strip() == '':
                    errors.append(f'第{row_num}行: 车辆类型不能为空')
                    continue
                
                if pd.isna(row['车牌号']) or str(row['车牌号']).strip() == '':
                    errors.append(f'第{row_num}行: 车牌号不能为空')
                    continue
                
                try:
                    standard_volume = float(row['标准容积'])
                    if standard_volume <= 0:
                        errors.append(f'第{row_num}行: 标准容积必须是正数')
                        continue
                except (ValueError, TypeError):
                    errors.append(f'第{row_num}行: 标准容积格式错误')
                    continue
                
                # 处理供应商字段（可选）
                suppliers = []
                if '供应商' in df.columns and not pd.isna(row['供应商']):
                    suppliers_str = str(row['供应商']).strip()
                    if suppliers_str:
                        suppliers = [s.strip() for s in suppliers_str.split(',') if s.strip()]
                
                valid_records.append({
                    'vehicle_type': str(row['车辆类型']).strip(),
                    'standard_volume': standard_volume,
                    'license_plate': str(row['车牌号']).strip().upper(),
                    'suppliers': suppliers
                })
            
            if errors:
                return create_response(success=False, error={
                    'code': 4001,
                    'message': '数据验证失败',
                    'details': errors
                }), 400
            
            if not valid_records:
                return create_response(success=False, error={
                    'code': 4001,
                    'message': '没有有效的数据需要导入'
                }), 400
            
            # 批量导入数据
            db_manager = DatabaseManager()
            if not db_manager.connect():
                return create_response(success=False, error={
                    'code': 5001,
                    'message': '数据库连接失败'
                }), 500
            
            try:
                success_count = 0
                error_count = 0
                import_errors = []
                
                for record in valid_records:
                    try:
                        result = db_manager.upsert_vehicle_capacity_reference(
                            record['vehicle_type'],
                            record['standard_volume'],
                            record['license_plate'],
                            record['suppliers']
                        )
                        
                        if result['success']:
                            success_count += 1
                        else:
                            error_count += 1
                            import_errors.append(f"车牌号 {record['license_plate']}: {result.get('error', '导入失败')}")
                    
                    except Exception as e:
                        error_count += 1
                        import_errors.append(f"车牌号 {record['license_plate']}: {str(e)}")
                
                db_manager.conn.commit()
                
                return create_response(data={
                    'message': f'批量导入完成: 成功{success_count}条, 失败{error_count}条',
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': import_errors,
                    'total_records': len(valid_records)
                })
                
            except Exception as e:
                db_manager.conn.rollback()
                raise
            finally:
                db_manager.disconnect()
        
        except Exception as e:
            return create_response(success=False, error={
                'code': 5001,
                'message': f'文件读取失败: {str(e)}'
            }), 500
    
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'批量导入失败: {str(e)}'
        }), 500
