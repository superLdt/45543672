"""
公司相关API接口
"""

from flask import Blueprint, jsonify, request
global_db_manager = None

def set_db_manager(db_manager):
    """设置全局数据库管理器实例"""
    global global_db_manager
    global_db_manager = db_manager

# 创建蓝图
company_bp = Blueprint('company', __name__)

@company_bp.route('/api/companies', methods=['GET'])
def get_companies():
    """获取所有公司列表"""
    try:
        # 获取数据库连接
        db_manager = global_db_manager
        if not db_manager or not db_manager.connect():
            return jsonify({'error': '数据库连接失败'}), 500
        
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
        return jsonify(companies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@company_bp.route('/api/companies/id/<company_name>', methods=['GET'])
def get_company_id_by_name(company_name):
    """根据公司名称获取公司ID"""
    try:
        # 获取数据库连接
        db_manager = global_db_manager
        if not db_manager or not db_manager.connect():
            return jsonify({'error': '数据库连接失败'}), 500
        
        # 获取公司ID
        company_id = db_manager.get_company_id_by_name(company_name)
        
        db_manager.disconnect()
        
        if company_id is not None:
            return jsonify({'id': company_id})
        else:
            return jsonify({'error': '未找到指定公司'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500