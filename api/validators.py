"""
验证器模块 - 专门负责数据格式和业务规则验证
确保进入系统的数据都是合法有效的
"""

from datetime import datetime
import re

class DispatchValidators:
    """派车任务验证器类"""
    
    @staticmethod
    def validate_create_task(data):
        """验证创建派车任务的数据"""
        required_fields = [
            'required_date',      # 用车时间（日期）
            'start_bureau',       # 始发局
            'route_direction',    # 路向
            'carrier_company',    # 委办承运公司
            'route_name',         # 邮路名称
            'transport_type',     # 运输类型
            'requirement_type',   # 需求类型
            'volume',             # 容积
            'weight',             # 重量
            'initiator_role',     # 发起者角色
            'initiator_user_id',  # 发起者用户ID
            'initiator_department' # 发起者部门
        ]
        
        # 检查必填字段
        for field in required_fields:
            if field not in data or not data.get(field):
                return False, f'缺少必填字段: {field}'
        
        # 验证枚举值
        if data.get('transport_type') not in ['单程', '往返']:
            return False, '运输类型必须是"单程"或"往返"'
        
        if data.get('requirement_type') not in ['正班', '加班']:
            return False, '需求类型必须是"正班"或"加班"'
        
        # 验证流程轨道
        dispatch_track = data.get('dispatch_track', '轨道A')
        if dispatch_track not in ['轨道A', '轨道B']:
            return False, '流程轨道必须是"轨道A"或"轨道B"'
        
        # 验证重量范围
        try:
            weight = float(data.get('weight', 0))
            if weight <= 0 or weight > 100:
                return False, '重量必须大于0且不超过100吨'
        except (ValueError, TypeError):
            return False, '重量必须是有效数字'
        
        # 验证容积
        try:
            volume = int(data.get('volume', 0))
            if volume <= 0 or volume > 200:
                return False, '容积必须大于0且不超过200立方米'
        except (ValueError, TypeError):
            return False, '容积必须是有效整数'
        
        # 验证日期格式
        try:
            required_date = data.get('required_date')
            datetime.strptime(required_date, '%Y-%m-%d')
            
            # 检查日期不能早于今天
            today = datetime.now().date()
            task_date = datetime.strptime(required_date, '%Y-%m-%d').date()
            if task_date < today:
                return False, '用车时间不能早于当前日期'
                
        except ValueError:
            return False, '日期格式错误，应为YYYY-MM-DD'
        
        # 验证角色权限
        valid_roles = ['车间地调', '区域调度员', '超级管理员', '供应商']
        if data.get('initiator_role') not in valid_roles:
            return False, f'发起者角色必须是以下之一: {", ".join(valid_roles)}'
        
        # 验证轨道权限
        initiator_role = data.get('initiator_role')
        dispatch_track = data.get('dispatch_track', '轨道A')
        
        if initiator_role == '车间地调' and dispatch_track == '轨道B':
            return False, '车间地调只能创建轨道A任务'
        
        if initiator_role == '供应商':
            return False, '供应商不能创建派车任务'
        
        return True, None
    
    @staticmethod
    def validate_audit_data(data):
        """验证审核数据"""
        required_fields = ['task_id', 'audit_result', 'auditor_role', 'auditor_user_id']
        
        for field in required_fields:
            if field not in data or not data.get(field):
                return False, f'缺少必填字段: {field}'
        
        # 验证审核结果
        if data.get('audit_result') not in ['通过', '拒绝']:
            return False, '审核结果必须是"通过"或"拒绝"'
        
        # 验证审核人角色
        valid_roles = ['区域调度员', '超级管理员']
        if data.get('auditor_role') not in valid_roles:
            return False, f'审核人角色必须是以下之一: {", ".join(valid_roles)}'
        
        # 验证备注长度
        audit_note = data.get('audit_note', '')
        if len(audit_note) > 500:
            return False, '审核备注不能超过500字符'
        
        return True, None
    
    @staticmethod
    def validate_status_update(data):
        """验证状态更新数据"""
        required_fields = ['task_id', 'new_status', 'operator_role', 'operator_user_id']
        
        for field in required_fields:
            if field not in data or not data.get(field):
                return False, f'缺少必填字段: {field}'
        
        # 验证状态值
        valid_statuses = [
            '待提交', '待区域调度员审核', '待供应商响应',
            '已响应', '已发车', '已到达', '已完成'
        ]
        
        new_status = data.get('new_status')
        if new_status not in valid_statuses:
            return False, f'状态必须是以下之一: {", ".join(valid_statuses)}'
        
        # 验证操作人角色
        valid_roles = ['车间地调', '区域调度员', '超级管理员', '供应商']
        if data.get('operator_role') not in valid_roles:
            return False, f'操作人角色必须是以下之一: {", ".join(valid_roles)}'
        
        # 验证备注
        note = data.get('note', '')
        if len(note) > 200:
            return False, '备注不能超过200字符'
        
        return True, None
    
    @staticmethod
    def validate_vehicle_assignment(data):
        """验证车辆分配数据"""
        required_fields = [
            'task_id', 'manifest_number', 'manifest_serial', 
            'dispatch_number', 'license_plate'
        ]
        
        for field in required_fields:
            if field not in data or not data.get(field):
                return False, f'缺少必填字段: {field}'
        
        # 验证车牌号格式
        license_plate = data.get('license_plate', '')
        if not re.match(r'^[\u4e00-\u9fa5][A-Z][0-9A-Z]{5,6}$', license_plate):
            return False, '车牌号格式不正确（如：京A12345）'
        
        # 验证单号格式
        for field in ['manifest_number', 'manifest_serial', 'dispatch_number']:
            value = data.get(field, '')
            if len(value) < 5 or len(value) > 20:
                return False, f'{field}长度必须在5-20字符之间'
        
        return True, None
    
    @staticmethod
    def validate_task_query(params):
        """验证任务查询参数"""
        # 验证分页参数
        try:
            page = int(params.get('page', 1))
            limit = int(params.get('limit', 20))
            
            if page < 1:
                return False, '页码必须大于0'
            
            if limit < 1 or limit > 100:
                return False, '每页数量必须在1-100之间'
                
        except (ValueError, TypeError):
            return False, '分页参数必须是有效数字'
        
        # 验证筛选参数
        valid_statuses = [
            '待提交', '待区域调度员审核', '待供应商响应',
            '已响应', '已发车', '已到达', '已完成'
        ]
        
        status = params.get('status')
        if status and status not in valid_statuses:
            return False, f'状态筛选值无效'
        
        dispatch_track = params.get('dispatch_track')
        if dispatch_track and dispatch_track not in ['轨道A', '轨道B']:
            return False, '流程轨道筛选值必须是"轨道A"或"轨道B"'
        
        return True, None

# 创建全局验证器实例
validators = DispatchValidators()