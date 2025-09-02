"""
审核流程API模块 - 专门处理双轨派车的审核相关功能
"""

from flask import Blueprint, request, jsonify, session
from api.decorators import require_role, create_response
from api.validators import validators
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
from datetime import datetime

audit_bp = Blueprint('audit', __name__, url_prefix='/api/dispatch')

@audit_bp.route('/tasks/<task_id>/submit', methods=['POST'])
@require_role(['车间地调', '区域调度员', '超级管理员'])
def submit_for_audit(task_id):
    """提交任务进行审核（轨道A专用）"""
    try:
        # 获取当前用户信息
        current_role = session.get('user_role')
        current_user_id = session.get('user_id')
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询任务详情
            db_manager.cursor.execute(
                "SELECT * FROM manual_dispatch_tasks WHERE task_id = ?", 
                [task_id]
            )
            task = db_manager.cursor.fetchone()
            
            if not task:
                return create_response(success=False, error={
                    'code': 4004,
                    'message': '任务不存在'
                }), 404
            
            task_dict = dict(task)
            
            # 权限检查
            if task_dict['initiator_user_id'] != current_user_id:
                return create_response(success=False, error={
                    'code': 4002,
                    'message': '只能提交自己创建的任务'
                }), 403
            
            # 状态检查 - 必须是待提交状态
            if task_dict['status'] != '待提交':
                return create_response(success=False, error={
                    'code': 4003,
                    'message': f'当前状态为{task_dict["status"]}，无法提交审核'
                }), 400
            
            # 轨道检查 - 必须是轨道A
            if task_dict['dispatch_track'] != '轨道A':
                return create_response(success=False, error={
                    'code': 4003,
                    'message': '轨道B任务无需提交审核'
                }), 400
            
            # 更新任务状态
            db_manager.cursor.execute("""
                UPDATE manual_dispatch_tasks 
                SET status = '待区域调度员审核',
                    current_handler_role = '区域调度员',
                    updated_at = ?
                WHERE task_id = ?
            """, [datetime.now(), task_id])
            
            # 记录状态变更历史
            db_manager.cursor.execute("""
                INSERT INTO dispatch_status_history (task_id, status_change, operator, timestamp, note)
                VALUES (?, ?, ?, ?, ?)
            """, [task_id, '待提交→待区域调度员审核', current_role, datetime.now(), '提交审核'])
            
            db_manager.conn.commit()
            
            return create_response(data={
                'task_id': task_id,
                'status': '待区域调度员审核',
                'current_handler_role': '区域调度员',
                'message': '任务已成功提交审核'
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'提交审核失败: {str(e)}'
        }), 500

@audit_bp.route('/tasks/<task_id>/audit', methods=['POST'])
@require_role(['区域调度员', '超级管理员'])
def audit_task(task_id):
    """审核任务（区域调度员/超级管理员）"""
    try:
        # 获取审核数据
        data = request.get_json()
        
        # 简单验证
        if not data or 'audit_result' not in data:
            return create_response(success=False, error={
                'code': 4001,
                'message': '缺少必填参数：audit_result'
            }), 400
        
        audit_result = data.get('audit_result')
        audit_note = data.get('audit_note', '')
        
        # 获取当前用户信息
        current_role = session.get('user_role')
        current_user_id = session.get('user_id')
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询任务详情
            db_manager.cursor.execute(
                "SELECT * FROM manual_dispatch_tasks WHERE task_id = ?", 
                [task_id]
            )
            task = db_manager.cursor.fetchone()
            
            if not task:
                return create_response(success=False, error={
                    'code': 4004,
                    'message': '任务不存在'
                }), 404
            
            task_dict = dict(task)
            
            # 状态检查 - 必须是待审核状态
            if task_dict['status'] != '待调度员审核':
                return create_response(success=False, error={
                    'code': 4003,
                    'message': f'当前状态为{task_dict["status"]}，无法审核'
                }), 400
            
            # 轨道检查 - 必须是轨道A
            if task_dict['dispatch_track'] != '轨道A':
                return create_response(success=False, error={
                    'code': 4003,
                    'message': '轨道B任务无需审核'
                }), 400
            
            # 根据审核结果更新状态
            if audit_result == '通过':
                new_status = '待供应商响应'
                current_handler_role = '供应商'
                audit_status = '已通过'
            else:  # 拒绝
                new_status = '已取消'
                current_handler_role = None
                audit_status = '已拒绝'
            
            # 更新任务状态
            db_manager.cursor.execute("""
                UPDATE manual_dispatch_tasks 
                SET status = ?,
                    audit_status = ?,
                    auditor_role = ?,
                    auditor_user_id = ?,
                    audit_time = ?,
                    audit_note = ?,
                    current_handler_role = ?,
                    updated_at = ?
                WHERE task_id = ?
            """, [
                new_status, audit_status, current_role, current_user_id, 
                datetime.now(), audit_note, current_handler_role, datetime.now(), task_id
            ])
            
            # 记录状态变更历史
            status_change = f'待区域调度员审核→{new_status}'
            db_manager.cursor.execute("""
                INSERT INTO dispatch_status_history (task_id, status_change, operator, timestamp, note)
                VALUES (?, ?, ?, ?, ?)
            """, [task_id, status_change, current_role, datetime.now(), audit_note])
            
            db_manager.conn.commit()
            
            return create_response(data={
                'task_id': task_id,
                'status': new_status,
                'audit_status': audit_status,
                'current_handler_role': current_handler_role,
                'message': f'任务已{audit_result}'
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'审核失败: {str(e)}'
        }), 500

@audit_bp.route('/tasks/<task_id>/status', methods=['PUT'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def update_task_status(task_id):
    """更新任务状态（通用接口）"""
    try:
        # 获取状态数据
        data = request.get_json()
        
        # 验证数据
        is_valid, error_msg = validators.validate_status_update(data)
        if not is_valid:
            return create_response(success=False, error={
                'code': 4001,
                'message': error_msg
            }), 400
        
        new_status = data.get('new_status')
        note = data.get('note', '')
        
        # 获取当前用户信息
        current_role = session.get('user_role')
        current_user_id = session.get('user_id')
        
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询任务详情
            db_manager.cursor.execute(
                "SELECT * FROM manual_dispatch_tasks WHERE task_id = ?", 
                [task_id]
            )
            task = db_manager.cursor.fetchone()
            
            if not task:
                return create_response(success=False, error={
                    'code': 4004,
                    'message': '任务不存在'
                }), 404
            
            task_dict = dict(task)
            old_status = task_dict['status']
            
            # 权限和状态流转检查
            is_allowed, error_msg = check_status_transition(
                old_status, new_status, current_role, task_dict
            )
            if not is_allowed:
                return create_response(success=False, error={
                    'code': 4003,
                    'message': error_msg
                }), 400
            
            # 确定下一个处理人角色
            next_handler_role = get_next_handler(new_status, task_dict)
            
            # 更新任务状态
            db_manager.cursor.execute("""
                UPDATE manual_dispatch_tasks 
                SET status = ?,
                    current_handler_role = ?,
                    current_handler_user_id = ?,
                    updated_at = ?
                WHERE task_id = ?
            """, [
                new_status, next_handler_role, 
                current_user_id if next_handler_role == current_role else None,
                datetime.now(), task_id
            ])
            
            # 记录状态变更历史
            status_change = f'{old_status}→{new_status}'
            db_manager.cursor.execute("""
                INSERT INTO dispatch_status_history (task_id, status_change, operator, timestamp, note)
                VALUES (?, ?, ?, ?, ?)
            """, [task_id, status_change, current_role, datetime.now(), note])
            
            db_manager.conn.commit()
            
            return create_response(data={
                'task_id': task_id,
                'old_status': old_status,
                'new_status': new_status,
                'current_handler_role': next_handler_role,
                'message': '状态更新成功'
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'状态更新失败: {str(e)}'
        }), 500

@audit_bp.route('/tasks/<task_id>/history', methods=['GET'])
@require_role(['车间地调', '区域调度员', '超级管理员', '供应商'])
def get_task_history(task_id):
    """获取任务状态变更历史"""
    try:
        db_manager = DatabaseManager()
        if not db_manager.connect():
            return create_response(success=False, error={
                'code': 5001,
                'message': '数据库连接失败'
            }), 500
        
        try:
            # 查询任务是否存在
            db_manager.cursor.execute(
                "SELECT COUNT(*) FROM manual_dispatch_tasks WHERE task_id = ?", 
                [task_id]
            )
            if db_manager.cursor.fetchone()[0] == 0:
                return create_response(success=False, error={
                    'code': 4004,
                    'message': '任务不存在'
                }), 404
            
            # 查询状态历史
            db_manager.cursor.execute("""
                SELECT * FROM dispatch_status_history 
                WHERE task_id = ? 
                ORDER BY timestamp DESC
            """, [task_id])
            
            history = [dict(row) for row in db_manager.cursor.fetchall()]
            
            return create_response(data={
                'task_id': task_id,
                'history': history,
                'total': len(history)
            })
            
        finally:
            db_manager.disconnect()
            
    except Exception as e:
        return create_response(success=False, error={
            'code': 5001,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500

def check_status_transition(old_status, new_status, current_role, task_dict):
    """检查状态流转是否合法"""
    
    # 定义状态流转规则（清晰命名版）
    transition_rules = {
        # 轨道A流转规则
        '轨道A': {
            '待提交': {
                '允许操作': ['车间地调'],
                '允许目标': ['待调度员审核']
            },
            '待调度员审核': {
                '允许操作': ['区域调度员', '超级管理员'],
                '允许目标': ['待供应商响应', '已取消']
            },
            '待供应商响应': {
                '允许操作': ['供应商'],
                '允许目标': ['供应商已响应']
            },
            '供应商已响应': {
                '允许操作': ['车间地调'],
                '允许目标': ['车间已核查']
            },
            '车间已核查': {
                '允许操作': ['供应商'],
                '允许目标': ['供应商已确认']
            },
            '供应商已确认': {
                '允许操作': ['车间地调'],
                '允许目标': ['任务结束']
            }
        },
        # 轨道B流转规则
        '轨道B': {
            '待供应商响应': {
                '允许操作': ['供应商'],
                '允许目标': ['供应商已响应']
            },
            '供应商已响应': {
                '允许操作': ['区域调度员', '超级管理员'],
                '允许目标': ['车间已核查']
            },
            '车间已核查': {
                '允许操作': ['供应商'],
                '允许目标': ['供应商已确认']
            },
            '供应商已确认': {
                '允许操作': ['区域调度员', '超级管理员'],
                '允许目标': ['任务结束']
            }
        }
    }
    
    dispatch_track = task_dict['dispatch_track']
    
    # 检查是否有这个状态
    if old_status not in transition_rules[dispatch_track]:
        return False, f'无效的状态: {old_status}'
    
    rule = transition_rules[dispatch_track][old_status]
    
    # 检查角色权限
    if current_role not in rule['允许操作']:
        return False, f'角色{current_role}无权执行此操作'
    
    # 检查目标状态
    if new_status not in rule['允许目标']:
        return False, f'不能从{old_status}变更为{new_status}'
    
    return True, None

def get_next_handler(new_status, task_dict):
    """根据新状态确定下一个处理人角色"""
    
    next_handlers = {
        '待调度员审核': '区域调度员',
        '待供应商响应': '供应商',
        '供应商已响应': '车间地调' if task_dict['dispatch_track'] == '轨道A' else '区域调度员',
        '车间已核查': '供应商',
        '供应商已确认': '车间地调' if task_dict['dispatch_track'] == '轨道A' else '区域调度员',
        '任务结束': None,
        '已取消': None,
        '已拒绝': None
    }
    
    return next_handlers.get(new_status)

# 注册蓝图函数
def init_audit_routes(app):
    """初始化审核路由"""
    app.register_blueprint(audit_bp)