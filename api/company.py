"""
公司相关API接口
"""

from flask import Blueprint, request, jsonify
from api.decorators import require_role, create_response
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
from services.error_handler import error_handler, APIError, ValidationError, PermissionError, NotFoundError, api_response

# 创建蓝图
company_bp = Blueprint('company', __name__)

@company_bp.route('/api/companies', methods=['GET'])
@require_role(['超级管理员', '区域调度员'])
@error_handler
def get_companies():
    """获取所有公司列表"""
    # 获取数据库连接
    db_manager = DatabaseManager()
    if not db_manager.connect():
        raise APIError('数据库连接失败', 500)
    
    cursor = db_manager.cursor
    
    # 查询所有公司
    cursor.execute('SELECT id, name FROM Company ORDER BY name')
    companies = []
    for row in cursor.fetchall():
        companies.append({
            'id': row[0],
            'name': row[1]
        })
    
    db_manager.disconnect()
    return api_response(data=companies)

@company_bp.route('/api/companies/id/<company_name>', methods=['GET'])
@require_role(['超级管理员', '区域调度员'])
@error_handler
def get_company_id_by_name(company_name):
    """根据公司名称获取公司ID"""
    # 获取数据库连接
    db_manager = DatabaseManager()
    if not db_manager.connect():
        raise APIError('数据库连接失败', 500)
    
    # 获取公司ID
    company_id = db_manager.get_company_id_by_name(company_name)
    
    db_manager.disconnect()
    
    if company_id is not None:
        return api_response(data={'id': company_id})
    else:
        raise NotFoundError('未找到指定公司')