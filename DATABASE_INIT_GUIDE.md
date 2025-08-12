# 数据库初始化优化指南

## 优化后的结构

### 1. 数据库初始化职责分离

**之前（app.py中）：**
- 直接在app.py中定义初始化函数
- 数据库操作逻辑分散在多个文件

**现在（db_manager统一管理）：**
- 所有数据库初始化逻辑集中在`db_manager.py`
- app.py只需调用静态方法

### 2. 使用方法

#### 应用启动时初始化
```python
# app.py 中简化为一行代码
from db_manager import DatabaseManager

with app.app_context():
    DatabaseManager.init_database()  # 静态方法调用
```

#### 手动初始化
```python
# 命令行或脚本中
from db_manager import DatabaseManager

# 方法1：静态方法
DatabaseManager.init_database()

# 方法2：实例方法
db = DatabaseManager()
db.initialize_all_tables()
```

#### 扩展其他表
在`db_manager.py`中添加：
```python
def initialize_all_tables(self):
    """初始化所有需要的表"""
    if not self.connect():
        return False
    
    try:
        # 人工派车表
        self.create_manual_dispatch_tables()
        
        # 可以在这里添加其他表的创建
        # self.create_user_tables()
        # self.create_permission_tables()
        # self.create_log_tables()
        
        return True
    except Exception as e:
        print(f"初始化表失败: {e}")
        return False
    finally:
        self.disconnect()
```

### 3. 优势

- **单一职责**：所有数据库相关操作集中在db_manager
- **代码复用**：静态方法可在任何地方调用
- **易于维护**：修改表结构只需改db_manager.py
- **可扩展**：支持添加更多表的初始化
- **解耦**：app.py不再关心具体的数据库实现细节

### 4. 文件结构

```
db_manager.py          # 数据库管理核心
├── init_database()    # 静态初始化方法
├── initialize_all_tables()  # 实例初始化方法
├── create_manual_dispatch_tables()  # 具体表创建
└── 其他业务方法...

app.py                 # 应用入口
└── DatabaseManager.init_database()  # 一行调用
```

### 5. 测试验证

```bash
# 测试新的初始化方法
python -c "from db_manager import DatabaseManager; DatabaseManager.init_database()"
```

预期输出：
```
✅ 数据库初始化完成
```