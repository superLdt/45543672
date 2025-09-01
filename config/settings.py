# -*- coding: utf-8 -*-
"""
配置管理
支持多环境配置
"""
import os
from secrets import token_hex

class Config:
    """基础配置"""
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or token_hex(32)
    
    # 数据库配置
    DATABASE = os.environ.get('DATABASE_PATH') or 'database.db'
    
    # 多数据库支持配置
    DATABASE_CONFIG = {
        'type': os.environ.get('DATABASE_TYPE') or 'sqlite',  # sqlite | mysql | postgresql
        'sqlite': {
            'database': os.environ.get('DATABASE_PATH') or 'database.db'
        },
        'mysql': {
            'host': os.environ.get('MYSQL_HOST') or 'localhost',
            'port': int(os.environ.get('MYSQL_PORT') or 3306),
            'user': os.environ.get('MYSQL_USER') or 'root',
            'password': os.environ.get('MYSQL_PASSWORD') or '',
            'database': os.environ.get('MYSQL_DATABASE') or 'smart_transport',
            'charset': os.environ.get('MYSQL_CHARSET') or 'utf8mb4'
        },
        'postgresql': {
            'host': os.environ.get('POSTGRESQL_HOST') or 'localhost',
            'port': int(os.environ.get('POSTGRESQL_PORT') or 5432),
            'user': os.environ.get('POSTGRESQL_USER') or 'postgres',
            'password': os.environ.get('POSTGRESQL_PASSWORD') or '',
            'database': os.environ.get('POSTGRESQL_DATABASE') or 'smart_transport',
            'sslmode': os.environ.get('POSTGRESQL_SSLMODE') or 'prefer'
        }
    }
    
    # Flask配置
    PERMANENT_SESSION_LIFETIME = 3600
    SESSION_TYPE = 'filesystem'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        # 开发环境特定初始化
        print(f"🚀 开发模式启动")
        print(f"📁 数据库路径: {app.config['DATABASE']}")
        print(f"🔧 数据库类型: {app.config['DATABASE_CONFIG']['type']}")

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境数据库路径
    DATABASE = os.environ.get('DATABASE_PATH') or '/var/www/flask_app/database.db'
    
    # 生产环境多数据库配置
    DATABASE_CONFIG = {
        'type': os.environ.get('DATABASE_TYPE') or 'sqlite',
        'sqlite': {
            'database': os.environ.get('DATABASE_PATH') or '/var/www/flask_app/database.db'
        },
        'mysql': {
            'host': os.environ.get('MYSQL_HOST') or 'localhost',
            'port': int(os.environ.get('MYSQL_PORT') or 3306),
            'user': os.environ.get('MYSQL_USER') or 'root',
            'password': os.environ.get('MYSQL_PASSWORD') or '',
            'database': os.environ.get('MYSQL_DATABASE') or 'smart_transport',
            'charset': os.environ.get('MYSQL_CHARSET') or 'utf8mb4'
        },
        'postgresql': {
            'host': os.environ.get('POSTGRESQL_HOST') or 'localhost',
            'port': int(os.environ.get('POSTGRESQL_PORT') or 5432),
            'user': os.environ.get('POSTGRESQL_USER') or 'postgres',
            'password': os.environ.get('POSTGRESQL_PASSWORD') or '',
            'database': os.environ.get('POSTGRESQL_DATABASE') or 'smart_transport',
            'sslmode': os.environ.get('POSTGRESQL_SSLMODE') or 'prefer'
        }
    }
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # 配置日志到文件
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/intelligent_logistics.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('智能运力系统启动')

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DATABASE = ':memory:'  # 使用内存数据库进行测试

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前环境配置"""
    return config[os.environ.get('FLASK_ENV') or 'default']