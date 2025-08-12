# 数据库迁移指南：从SQLite到MySQL

## 概述

本项目已完成数据库管理系统的统一重构，将所有数据库操作集中到 `db_manager.py` 中，为从SQLite迁移到MySQL做好了准备。

## 已完成的工作

### 1. 数据库管理统一化
- ✅ **创建了 DatabaseManager 类**：统一管理所有数据库操作
- ✅ **整合了初始化逻辑**：将 `init_db()` 和 `insert_default_data()` 整合到 DatabaseManager
- ✅ **移除了重复代码**：从 app.py 中移除了 200+ 行的数据库初始化代码
- ✅ **标准化了表创建**：所有表创建逻辑集中在 `db_manager.py`
- ✅ **整合了权限配置**：将 `init_permissions.py` 中的权限配置功能整合到 DatabaseManager
  - ✅ 新增 `_configure_role_permissions` 方法配置角色权限
  - ✅ 新增 `check_and_fix_permissions` 方法检查和修复权限
  - ✅ 删除 `init_permissions.py` 文件

### 2. 当前数据库结构

#### 用户管理相关表
- `User` - 用户表
- `Company` - 单位/公司表
- `Role` - 角色表
- `Permission` - 权限表
- `UserRole` - 用户角色关联表
- `RolePermission` - 角色权限关联表
- `modules` - 系统模块表

#### 人工派车相关表
- `manual_dispatch_tasks` - 人工派车任务表
- `vehicles` - 车辆信息表
- `dispatch_status_history` - 派车状态历史表

## MySQL迁移准备步骤

### 步骤1：修改数据库连接配置

**当前SQLite配置（db_manager.py）：**
```python
self.db_path = "database.db"
```

**修改为MySQL配置：**
```python
import pymysql

# MySQL配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'transport_system',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```

### 步骤2：修改连接方法

**当前SQLite连接：**
```python
import sqlite3
self.conn = sqlite3.connect(self.db_path)
```

**修改为MySQL连接：**
```python
import pymysql
self.conn = pymysql.connect(**MYSQL_CONFIG)
```

### 步骤3：SQL语法适配

#### 3.1 数据类型映射
| SQLite | MySQL |
|--------|--------|
| INTEGER | INT |
| TEXT | VARCHAR(255) |
| BOOLEAN | TINYINT(1) |
| TIMESTAMP | DATETIME |
| REAL | DECIMAL(10,2) |

#### 3.2 语法差异
- **主键自增**：`INTEGER PRIMARY KEY AUTOINCREMENT` → `INT AUTO_INCREMENT PRIMARY KEY`
- **外键约束**：SQLite使用 `FOREIGN KEY`，MySQL需要确保使用InnoDB引擎
- **索引创建**：语法相同，无需修改

### 步骤4：更新表创建SQL

**示例修改（User表）：**

**SQLite版本：**
```sql
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    company_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES Company (id)
)
```

**MySQL版本：**
```sql
CREATE TABLE IF NOT EXISTS User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    company_id INT,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES Company(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 步骤5：依赖库更新

**安装MySQL依赖：**
```bash
pip install pymysql
# 或者
pip install mysql-connector-python
```

**更新requirements.txt：**
```
# 移除SQLite依赖
# sqlite3

# 添加MySQL依赖
PyMySQL>=1.0.2
# 或
mysql-connector-python>=8.0.0
```

## 迁移执行计划

### 阶段1：开发环境迁移
1. 安装MySQL并创建数据库
2. 修改db_manager.py的MySQL配置
3. 更新所有CREATE TABLE语句
4. 运行测试验证功能

### 阶段2：生产环境迁移
1. 备份现有SQLite数据库
2. 数据迁移脚本开发
3. 生产环境MySQL配置
4. 数据导入验证

### 阶段3：代码优化
1. 添加连接池管理
2. 优化查询性能
3. 添加数据库监控

## 数据迁移脚本示例

### 创建迁移脚本：migrate_sqlite_to_mysql.py

```python
import sqlite3
import pymysql
import logging

class DataMigrator:
    def __init__(self, sqlite_path, mysql_config):
        self.sqlite_path = sqlite_path
        self.mysql_config = mysql_config
        
    def migrate_all_tables(self):
        """迁移所有表数据"""
        # 1. 连接SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # 2. 连接MySQL
        mysql_conn = pymysql.connect(**self.mysql_config)
        
        try:
            # 3. 逐表迁移数据
            tables = ['User', 'Company', 'Role', 'Permission', 
                     'UserRole', 'RolePermission', 'modules',
                     'manual_dispatch_tasks', 'vehicles', 'dispatch_status_history']
            
            for table in tables:
                self.migrate_table(sqlite_conn, mysql_conn, table)
                
            mysql_conn.commit()
            logging.info("数据迁移完成")
            
        except Exception as e:
            mysql_conn.rollback()
            logging.error(f"数据迁移失败: {e}")
            raise
        finally:
            sqlite_conn.close()
            mysql_conn.close()
```

## 测试验证

### 1. 功能测试
```python
# 测试数据库连接
from db_manager import DatabaseManager
db = DatabaseManager()
assert db.connect() is True

# 测试表创建
db.initialize_all_tables()

# 测试数据插入
db.insert_default_data()
```

### 2. 性能测试
- 连接性能测试
- 查询性能测试
- 并发连接测试

## 注意事项

### 1. 字符编码
- 确保MySQL使用utf8mb4字符集
- 检查表和字段的字符集设置

### 2. 时区处理
- 配置MySQL时区与应用程序一致
- 考虑使用UTC时间存储

### 3. 外键约束
- MySQL需要InnoDB引擎支持外键
- 确保所有关联表使用相同存储引擎

### 4. 性能优化
- 为常用查询字段添加索引
- 考虑使用连接池
- 监控慢查询日志

## 迁移后验证清单

- [ ] 所有表结构正确创建
- [ ] 所有索引正确创建
- [ ] 外键约束正常工作
- [ ] 默认数据正确插入
- [ ] 应用程序正常运行
- [ ] 性能指标符合预期
- [ ] 数据完整性验证通过

## 回滚方案

如果迁移出现问题：
1. 保留SQLite数据库备份
2. 快速切换回SQLite配置
3. 修复问题后重新迁移

## 支持联系

如有迁移问题，请参考：
- MySQL官方文档
- PyMySQL文档
- 项目Issue跟踪