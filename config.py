# 配置文件 - 存储应用程序的配置参数
import os
from secrets import token_hex

# 数据库配置 - 集中管理数据库路径
# 根据环境变量决定使用的数据库路径
# 在 config.py 开头添加
print("=== config.py 环境变量调试 ===")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"SECRET_KEY 存在吗: {os.environ.get('SECRET_KEY') is not None}")  # 应显示 True
print(f"DATABASE_TYPE: {os.environ.get('DATABASE_TYPE') or 'sqlite'}")

if os.environ.get('FLASK_ENV') == 'production':
    DATABASE = '/var/www/flask_app/database.db'  # 服务器环境
else:
    DATABASE = 'database.db'  # 本地开发环境 (默认)

# 多数据库支持配置
DATABASE_CONFIG = {
    'type': os.environ.get('DATABASE_TYPE') or 'sqlite',  # sqlite | mysql | postgresql
    'sqlite': {
        'database': DATABASE
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

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY') or token_hex(32)  # 32字节的随机密钥

print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"当前数据库路径: {DATABASE}")
