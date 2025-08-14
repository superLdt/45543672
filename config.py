# 配置文件 - 存储应用程序的配置参数
import os
from secrets import token_hex

# 数据库配置 - 集中管理数据库路径
# 根据环境变量决定使用的数据库路径
# 在 config.py 开头添加
print("=== config.py 环境变量调试 ===")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"SECRET_KEY 存在吗: {os.environ.get('SECRET_KEY') is not None}")  # 应显示 True
if os.environ.get('FLASK_ENV') == 'production':
    DATABASE = '/var/www/flask_app/database.db'  # 服务器环境
else:
    DATABASE = 'database.db'  # 本地开发环境 (默认)

# 安全配置
SECRET_KEY = os.environ.get('SECRET_KEY') or token_hex(32)  # 32字节的随机密钥

print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"当前数据库路径: {DATABASE}")
