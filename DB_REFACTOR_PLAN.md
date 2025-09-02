# 数据库重构计划

## 概述
本计划旨在安全地将现有的 `db_manager.py` 功能迁移到新的 services 架构中，确保系统稳定性和功能完整性。

## 当前架构分析

### 现有 db_manager.py 功能模块
1. **数据库连接管理** - 连接池、连接状态管理
2. **事务处理** - 事务上下文管理器
3. **表结构管理** - 表创建、验证、更新
4. **数据操作** - CRUD 操作、查询执行
5. **权限管理** - 角色权限配置
6. **默认数据** - 初始化数据插入

### 目标 services 架构
- <mcfile name="db_connection_manager.py" path="services/db_connection_manager.py"></mcfile> - 连接管理
- <mcfile name="db_table_manager.py" path="services/db_table_manager.py"></mcfile> - 表结构管理  
- <mcfile name="db_data_manager.py" path="services/db_data_manager.py"></mcfile> - 数据操作
- <mcfile name="database_service.py" path="services/database_service.py"></mcfile> - 统一服务入口

## 重构阶段

### 第一阶段：依赖关系分析（1-2天）

#### 任务 1.1：识别外部依赖
```bash
# 查找所有引用 db_manager.py 的文件
grep -r "db_manager" . --include="*.py"
grep -r "DatabaseManager" . --include="*.py"
```

#### 任务 1.2：创建兼容层接口
在 <mcfile name="db_manager_compat.py" path="services/db_manager_compat.py"></mcfile> 中实现：

```python
"""
数据库管理器兼容层 - 提供与旧版 db_manager.py 相同的接口
"""
from services.database_service import DatabaseService
from services.db_connection_manager import DBConnectionManager
from services.db_table_manager import DBTableManager
from services.db_data_manager import DBDataManager

class DatabaseManagerCompat:
    """兼容层类，提供与旧版 DatabaseManager 相同的接口"""
    
    def __init__(self):
        self.connection_manager = DBConnectionManager()
        self.table_manager = DBTableManager()
        self.data_manager = DBDataManager()
    
    def connect(self):
        """建立数据库连接"""
        return self.connection_manager.initialize()
    
    def disconnect(self):
        """关闭数据库连接"""
        return self.connection_manager.release_all_connections()
    
    # 实现所有旧版接口方法...
```

### 第二阶段：逐步功能迁移（3-5天）

#### 任务 2.1：连接管理迁移
- ✅ 已完成：<mcfile name="db_connection_manager.py" path="services/db_connection_manager.py"></mcfile>
- 测试验证连接池功能

#### 任务 2.2：表结构管理迁移
- ✅ 已完成：<mcfile name="db_table_manager.py" path="services/db_table_manager.py"></mcfile>
- 验证表创建、更新功能

#### 任务 2.3：数据操作迁移  
- ✅ 已完成：<mcfile name="db_data_manager.py" path="services/db_data_manager.py"></mcfile>
- 测试 CRUD 操作兼容性

#### 任务 2.4：创建迁移测试脚本
```python
# tests/test_migration.py
"""迁移测试脚本"""

def test_connection_migration():
    """测试连接管理迁移"""
    # 旧版
    from db_manager import DatabaseManager
    old_db = DatabaseManager()
    old_connected = old_db.connect()
    
    # 新版
    from services.db_connection_manager import DBConnectionManager
    new_conn_mgr = DBConnectionManager()
    new_connected = new_conn_mgr.initialize()
    
    assert old_connected == new_connected
    print("✅ 连接管理迁移测试通过")

def test_table_operations():
    """测试表操作迁移"""
    # 测试代码...
```

### 第三阶段：全面替换和测试（2-3天）

#### 任务 3.1：更新引用文件
逐个修改引用 `db_manager.py` 的文件：

1. **优先修改测试文件**
2. **修改 API 模块**
3. **修改业务模块**
4. **最后修改核心应用文件**

#### 任务 3.2：创建回滚方案
```python
# backup/rollback.py
"""回滚脚本"""

def create_backup():
    """创建数据库备份"""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"database_backup_{timestamp}.db"
    
    shutil.copy2("database.db", backup_file)
    print(f"✅ 数据库备份已创建: {backup_file}")
    return backup_file

def rollback_migration():
    """执行回滚操作"""
    # 恢复旧版代码
    # 恢复数据库备份
    print("🔄 执行回滚操作")
```

#### 任务 3.3：性能对比测试
```python
# tests/performance_test.py
"""性能对比测试"""
import time

def benchmark_old_vs_new():
    """新旧版本性能对比"""
    
    # 测试查询性能
    test_query = "SELECT * FROM manual_dispatch_tasks LIMIT 100"
    
    # 旧版性能
    start_time = time.time()
    # 执行旧版查询
    old_time = time.time() - start_time
    
    # 新版性能  
    start_time = time.time()
    # 执行新版查询
    new_time = time.time() - start_time
    
    print(f"旧版查询时间: {old_time:.4f}s")
    print(f"新版查询时间: {new_time:.4f}s")
    print(f"性能提升: {(old_time - new_time)/old_time*100:.1f}%")
```

## 执行时间表

| 阶段 | 任务 | 预计时间 | 状态 |
|------|------|----------|------|
| 第一阶段 | 依赖分析 | 2天 | ⏳ 待开始 |
| 第二阶段 | 功能迁移 | 5天 | ⏳ 待开始 |  
| 第三阶段 | 全面替换 | 3天 | ⏳ 待开始 |
| 验收阶段 | 最终测试 | 2天 | ⏳ 待开始 |

## 风险评估和应对措施

### 风险 1：接口不兼容
- **影响**：功能异常
- **应对**：保持兼容层，逐步迁移

### 风险 2：性能下降
- **影响**：系统响应变慢  
- **应对**：性能监控和优化

### 风险 3：数据一致性
- **影响**：数据错误或丢失
- **应对**：定期备份，测试数据验证

## 验收标准

1. ✅ 所有现有功能正常工作
2. ✅ 性能不低于原有水平
3. ✅ 数据一致性验证通过
4. ✅ 单元测试覆盖率100%
5. ✅ 集成测试通过
6. ✅ 用户验收测试通过

## 下一步行动

1. **立即执行**：创建数据库备份
2. **今天完成**：分析外部依赖关系
3. **明天计划**：开始功能迁移测试

---

*最后更新: 2024-12-19*  
*负责人: 系统架构师*