"""
API蓝图注册模块
负责注册所有API路由蓝图
"""

from flask import Flask
from api.dispatch import dispatch_bp
from api.audit import audit_bp
from api.company import company_bp

def init_api_routes(app):
    """初始化所有API路由"""
    # 注册派车API
    app.register_blueprint(dispatch_bp)
    
    # 注册审核API
    app.register_blueprint(audit_bp)
    
    # 注册公司API
    app.register_blueprint(company_bp)
    
    # 打印注册成功的路由
    if app.config.get('DEBUG', False):
        print("✅ API路由注册完成")
        print("📋 已注册的路由：")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('dispatch.') or rule.endpoint.startswith('audit.') or rule.endpoint.startswith('company.'):
                print(f"  - {rule.rule} [{', '.join(rule.methods)}]")