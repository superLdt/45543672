#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统常量定义
统一所有字段值的标准定义，避免硬编码
"""

from enum import Enum
from typing import List

class DispatchStatus(Enum):
    """派车任务状态枚举"""
    PENDING_SUBMIT = "待提交"
    PENDING_AUDIT = "待调度员审核"
    PENDING_SUPPLIER_RESPONSE = "待供应商响应"
    SUPPLIER_RESPONDED = "供应商已响应"
    WORKSHOP_VERIFIED = "车间已核查"
    SUPPLIER_CONFIRMED = "供应商已确认"
    TASK_COMPLETED = "任务结束"
    TASK_CANCELLED = "已取消"
    
    @classmethod
    def all_values(cls):
        return [status.value for status in cls]
        
    @classmethod
    def is_valid(cls, value):
        return value in cls.all_values()

class DispatchTrack(Enum):
    """派车轨道枚举"""
    TRACK_A = "轨道A"
    TRACK_B = "轨道B"
    
    @classmethod
    def all_values(cls):
        return [track.value for track in cls]
        
    @classmethod
    def is_valid(cls, value):
        return value in cls.all_values()

class UserRole(Enum):
    """用户角色枚举"""
    WORKSHOP_DISPATCHER = "车间地调"
    REGIONAL_DISPATCHER = "区域调度员"
    SUPER_ADMIN = "超级管理员"
    SUPPLIER = "供应商"
    ACCOUNTANT = "对账人员"
    
    @classmethod
    def all_values(cls):
        return [role.value for role in cls]
        
    @classmethod
    def is_valid(cls, value):
        return value in cls.all_values()

class TransportType(Enum):
    """运输类型枚举"""
    ONE_WAY = "单程"
    ROUND_TRIP = "往返"
    
    @classmethod
    def all_values(cls):
        return [t_type.value for t_type in cls]

class RequirementType(Enum):
    """需求类型枚举"""
    REGULAR = "正班"
    OVERTIME = "加班"
    
    @classmethod
    def all_values(cls):
        return [r_type.value for r_type in cls]

class AuditStatus(Enum):
    """审核状态枚举"""
    PENDING = "待审核"
    APPROVED = "已通过"
    REJECTED = "已拒绝"
    
    @classmethod
    def all_values(cls):
        return [status.value for status in cls]

class DatabaseTables(Enum):
    """数据库表名枚举"""
    USER = "User"
    ROLE = "Role"
    USER_ROLE = "UserRole"
    PERMISSION = "Permission"
    ROLE_PERMISSION = "RolePermission"
    COMPANY = "Company"
    MANUAL_DISPATCH_TASKS = "manual_dispatch_tasks"
    VEHICLES = "vehicles"
    DISPATCH_STATUS_HISTORY = "dispatch_status_history"

class PermissionModules(Enum):
    """权限模块枚举"""
    USER_MANAGEMENT = "user_management"
    BASIC_DATA = "basic_data"
    PLANNING = "planning"
    COST_ANALYSIS = "cost_analysis"
    SCHEDULING = "scheduling"
    RECONCILIATION = "reconciliation"
    SYSTEM = "system"

# 标准SQL约束定义
SQL_CONSTRAINTS = {
    'manual_dispatch_tasks': {
        'status': {
            'type': 'TEXT',
            'check': "status IN ('待提交', '待调度员审核', '待供应商响应', '供应商已响应', '车间已核查', '供应商已确认', '任务结束', '已取消')",
            'default': DispatchStatus.PENDING_SUBMIT.value
        },
        'dispatch_track': {
            'type': 'TEXT',
            'check': "dispatch_track IN ('轨道A', '轨道B')",
            'default': DispatchTrack.TRACK_A.value
        },
        'initiator_role': {
            'type': 'TEXT',
            'check': "initiator_role IN ('车间地调', '区域调度员', '超级管理员', '供应商', '对账人员')",
            'default': UserRole.WORKSHOP_DISPATCHER.value
        }
    },
    'User': {
        'email': {
            'type': 'TEXT',
            'unique': True,
            'not_null': True
        },
        'username': {
            'type': 'TEXT',
            'unique': True,
            'not_null': True
        }
    }
}

# 标准字段映射
FIELD_MAPPINGS = {
    'manual_dispatch_tasks': {
        'status': DispatchStatus,
        'dispatch_track': DispatchTrack,
        'initiator_role': UserRole,
        'transport_type': TransportType,
        'requirement_type': RequirementType,
        'audit_status': AuditStatus
    }
}

# 外键关系定义
FOREIGN_KEY_RELATIONS = {
    'User': {
        'company_id': {'references': 'Company(id)', 'on_delete': 'SET NULL'}
    },
    'UserRole': {
        'user_id': {'references': 'User(id)', 'on_delete': 'CASCADE'},
        'role_id': {'references': 'Role(id)', 'on_delete': 'CASCADE'}
    },
    'RolePermission': {
        'role_id': {'references': 'Role(id)', 'on_delete': 'CASCADE'},
        'permission_id': {'references': 'Permission(id)', 'on_delete': 'CASCADE'}
    },
    'manual_dispatch_tasks': {
        'initiator_user_id': {'references': 'User(id)', 'on_delete': 'SET NULL'},
        'auditor_user_id': {'references': 'User(id)', 'on_delete': 'SET NULL'}
    }
}

# 默认数据配置
DEFAULT_DATA = {
    'roles': [
        (UserRole.SUPER_ADMIN.value, '系统最高权限管理员'),
        (UserRole.REGIONAL_DISPATCHER.value, '负责区域内调度管理'),
        (UserRole.ACCOUNTANT.value, '负责财务对账工作'),
        (UserRole.SUPPLIER.value, '外部供应商账户'),
        (UserRole.WORKSHOP_DISPATCHER.value, '负责车间车辆需求与供应商车辆审批')
    ],
    'permissions': [
        ('user_manage', PermissionModules.USER_MANAGEMENT.value, '用户管理权限'),
        ('role_manage', PermissionModules.USER_MANAGEMENT.value, '角色管理权限'),
        ('permission_manage', PermissionModules.SYSTEM.value, '权限管理权限'),
        ('basic_data_view', PermissionModules.BASIC_DATA.value, '基础数据查看权限'),
        ('basic_data_edit', PermissionModules.BASIC_DATA.value, '基础数据编辑权限'),
        ('planning_view', PermissionModules.PLANNING.value, '规划数据查看权限'),
        ('planning_edit', PermissionModules.PLANNING.value, '规划数据编辑权限'),
        ('cost_view', PermissionModules.COST_ANALYSIS.value, '成本数据查看权限'),
        ('cost_manage', PermissionModules.COST_ANALYSIS.value, '成本数据管理权限'),
        ('schedule_view', PermissionModules.SCHEDULING.value, '调度数据查看权限'),
        ('schedule_manage', PermissionModules.SCHEDULING.value, '调度数据管理权限'),
        ('reconciliation_view', PermissionModules.RECONCILIATION.value, '对账数据查看权限'),
        ('reconciliation_manage', PermissionModules.RECONCILIATION.value, '对账数据管理权限')
    ]
}

def get_valid_values(table_name: str, field_name: str) -> List[str]:
    """获取字段的有效值列表"""
    if table_name in FIELD_MAPPINGS and field_name in FIELD_MAPPINGS[table_name]:
        enum_class = FIELD_MAPPINGS[table_name][field_name]
        return enum_class.all_values()
    return []

def validate_field_value(table_name: str, field_name: str, value: str) -> bool:
    """验证字段值是否有效"""
    if table_name in FIELD_MAPPINGS and field_name in FIELD_MAPPINGS[table_name]:
        enum_class = FIELD_MAPPINGS[table_name][field_name]
        return enum_class.is_valid(value)
    return True