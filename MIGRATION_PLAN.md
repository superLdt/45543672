# 数据库架构迁移计划

## 当前状态

✅ **已完成**: DatabaseManager 到 DatabaseManagerCompat 的兼容层迁移
- 所有文件中的 DatabaseManager 引用已替换为兼容层
- 应用启动正常，数据库初始化正常
- 迁移测试全部通过

## 第一阶段：系统稳定性监控 (1-2周)

### 目标
监控迁移后的系统稳定性，确保生产环境正常运行

### 实施步骤

1. **部署监控脚本**
   ```bash
   python scripts/monitor_stability.py
   ```

2. **监控指标**
   - 数据库连接成功率
   - 查询执行时间
   - 错误率统计
   - 响应时间分布

3. **告警阈值**
   - 错误率 > 5% → 警告
   - 平均响应时间 > 100ms → 警告
   - 最大响应时间 > 1s → 严重警告

## 第二阶段：业务逻辑迁移到 Services 架构 (2-4周)

### 迁移优先级

#### 高优先级 (第1周)
1. **用户管理模块** (`modules/user_management/`)
   - 迁移用户查询、权限验证逻辑
   - 使用 DatabaseService.get_db_manager() 上下文管理器

2. **派车任务模块** (`api/dispatch.py`)
   - 迁移任务创建、状态更新逻辑
   - 实现事务性操作

#### 中优先级 (第2周)
3. **审核模块** (`api/audit.py`)
   - 迁移审核流程逻辑
   - 实现审核状态跟踪

4. **系统模块** (`modules/system/`)
   - 迁移模块权限管理
   - 使用新的数据库服务接口

#### 低优先级 (第3-4周)
5. **其他业务模块**
   - 成本分析、规划、对账等模块
   - 逐步迁移剩余业务逻辑

### 迁移模式

```python
# 旧模式 (逐步淘汰)
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
db = DatabaseManager()
db.connect()
try:
    # 业务逻辑
    result = db.execute_query("SELECT ...")
finally:
    db.disconnect()

# 新模式 (推荐)
from services.database_service import DatabaseService

with DatabaseService.get_db_manager() as db:
    # 业务逻辑 - 自动管理连接
    result = db.execute_query("SELECT ...")

# 或者使用事务
with DatabaseService.transaction() as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT ...")
```

## 第三阶段：移除兼容层 (1周)

### 迁移完成标准
- 所有业务模块已使用 DatabaseService
- 无直接使用 DatabaseManagerCompat 的代码
- 稳定性监控显示正常

### 移除步骤

1. **删除兼容层导入**
   ```python
   # 删除这行
   from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
   ```

2. **更新数据库服务**
   ```python
   # 在 database_service.py 中
   from services.db_connection_manager import DBConnectionManager
   from services.db_table_manager import DBTableManager
   from services.db_data_manager import DBDataManager
   
   # 直接使用新的服务组件
   ```

3. **清理兼容层文件**
   - 删除 `services/db_manager_compat.py`
   - 更新相关测试用例

## 风险控制

### 回滚方案
1. 保持 git 版本控制，便于回退
2. 分阶段部署，每个模块迁移后单独测试
3. 生产环境先部署监控，再执行迁移

### 监控重点
1. 数据库连接池状态
2. 事务处理正确性
3. 性能指标变化
4. 错误日志分析

## 时间安排

| 阶段 | 时间 | 状态 |
|------|------|------|
| 稳定性监控 | 第1-2周 | 🟡 进行中 |
| 业务逻辑迁移 | 第3-6周 | ⚪ 未开始 |
| 兼容层移除 | 第7周 | ⚪ 未开始 |

## 责任分工

- **开发团队**: 实施代码迁移，编写测试用例
- **测试团队**: 验证功能正确性，性能测试
- **运维团队**: 部署监控，生产环境部署

## 成功标准

1. ✅ 零宕机迁移
2. ✅ 性能指标不下降
3. ✅ 功能完整性保持
4. ✅ 代码可维护性提升
5. ✅ 系统稳定性提高

---

*最后更新: {update_date}*