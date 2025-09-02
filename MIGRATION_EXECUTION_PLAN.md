# 数据库迁移执行计划

## 迁移状态总览

### 📊 依赖分析结果
- **总文件数**: 32 个 Python 文件
- **有依赖的文件数**: 9 个文件 (28.1%)
- **高风险文件**: 3 个 (app.py, api/dispatch.py, api/audit.py)
- **中风险文件**: 4 个 (api/company.py, api/utils.py, modules/system/__init__.py)
- **低风险文件**: 2 个 (scripts/analyze_dependencies.py, services/db_manager_compat.py)

## 🎯 迁移优先级排序

### 第一阶段：低风险文件 (1天)
| 文件 | 风险等级 | 状态 | 负责人 | 预计完成时间 |
|------|----------|------|--------|-------------|
| scripts/analyze_dependencies.py | 🟢 低风险 | ⏳ 待开始 | 开发团队 | 2024-12-20 |
| services/db_manager_compat.py | 🟢 低风险 | ✅ 已完成 | 系统架构师 | 2024-12-19 |

### 第二阶段：中风险文件 (2-3天)
| 文件 | 风险等级 | 状态 | 负责人 | 预计完成时间 |
|------|----------|------|--------|-------------|
| api/utils.py | 🟡 中风险 | ⏳ 待开始 | 开发团队 | 2024-12-22 |
| modules/system/__init__.py | 🟡 中风险 | ⏳ 待开始 | 开发团队 | 2024-12-22 |
| api/company.py | 🟡 中风险 | ⏳ 待开始 | 开发团队 | 2024-12-23 |

### 第三阶段：高风险文件 (3-4天)
| 文件 | 风险等级 | 状态 | 负责人 | 预计完成时间 |
|------|----------|------|--------|-------------|
| api/audit.py | 🔴 高风险 | ⏳ 待开始 | 资深开发 | 2024-12-26 |
| api/dispatch.py | 🔴 高风险 | ⏳ 待开始 | 资深开发 | 2024-12-27 |
| app.py | 🔴 高风险 | ⏳ 待开始 | 系统架构师 | 2024-12-28 |

## 🔧 迁移执行步骤

### 步骤 1：环境准备 (已完成)
- ✅ 创建兼容层文件: `services/db_manager_compat.py`
- ✅ 创建迁移测试脚本: `tests/test_migration.py`
- ✅ 创建依赖分析脚本: `scripts/analyze_dependencies.py`
- ✅ 生成依赖分析报告

### 步骤 2：测试验证
```bash
# 运行迁移测试
python tests/test_migration.py

# 创建数据库备份
python -c "
import shutil, datetime
shutil.copy2('database.db', f'database_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')
print('✅ 备份完成')
"
```

### 步骤 3：逐个文件迁移

#### 3.1 迁移 api/utils.py
```python
# 修改前:
# from db_manager import DatabaseManager

# 修改后:
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
```

#### 3.2 迁移 modules/system/__init__.py
```python
# 修改前:
# from db_manager import DatabaseManager

# 修改后:  
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager
```

#### 3.3 迁移 api/company.py
```python
# 修改前:
# 使用全局 db_manager 实例

# 修改后:
from services.db_manager_compat import DatabaseManagerCompat

def set_db_manager(db_manager):
    """设置数据库管理器"""
    global global_db_manager
    global_db_manager = db_manager

# 初始化全局实例
global_db_manager = DatabaseManagerCompat()
```

#### 3.4 迁移 api/audit.py
```python
# 修改前:
# from db_manager import DatabaseManager

# 修改后:
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager

# 注意：需要测试所有审核相关的功能
```

#### 3.5 迁移 api/dispatch.py
```python
# 修改前:
# from db_manager import DatabaseManager

# 修改后:
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager

# 注意：这是核心业务模块，需要充分测试
```

#### 3.6 迁移 app.py (最后进行)
```python
# 修改前:
# from db_manager import DatabaseManager

# 修改后:
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager

# 修改数据库初始化部分
def init_database():
    """统一的数据库初始化入口"""
    from services.db_manager_compat import DatabaseManagerCompat
    db_manager = DatabaseManagerCompat()
    return db_manager.create_tables()
```

### 步骤 4：最终清理
```python
# 移除兼容层，直接使用新的 services 架构
from services.database_service import DatabaseService
from services.db_connection_manager import DBConnectionManager
from services.db_data_manager import DBDataManager

# 替换所有 DatabaseManager 的使用
```

## 🧪 测试策略

### 单元测试
```bash
# 运行所有单元测试
python -m pytest tests/ -v

# 运行迁移相关测试
python tests/test_migration.py
```

### 集成测试
1. ✅ 测试数据库连接功能
2. ✅ 测试表操作功能  
3. ✅ 测试数据查询功能
4. ✅ 测试数据一致性
5. ✅ 测试性能表现

### 用户验收测试
1. 人工派车流程测试
2. 审核流程测试
3. 车辆管理测试
4. 报表功能测试

## 🔄 回滚方案

### 自动回滚脚本
```python
# backup/rollback.py
def rollback_migration():
    """执行回滚操作"""
    # 1. 恢复数据库备份
    # 2. 恢复代码文件
    # 3. 重启应用服务
    print("🔄 执行回滚操作")
```

### 手动回滚步骤
1. **停止应用服务**
2. **恢复数据库备份**
3. **恢复代码到上一个稳定版本**
4. **重启应用服务**
5. **验证系统功能**

## 📈 进度跟踪

### 每日检查点
1. **晨会**: 检查前日进度和问题
2. **午间检查**: 验证已迁移功能
3. **晚间报告**: 总结当日进展

### 质量门禁
1. ✅ 所有测试必须通过
2. ✅ 代码审查必须完成
3. ✅ 性能指标必须达标
4. ✅ 用户验收必须通过

## 🚨 风险应对措施

### 风险 1: 接口不兼容
- **应对**: 保持兼容层，逐步迁移
- **监控**: 每日接口兼容性测试

### 风险 2: 性能下降  
- **应对**: 性能监控和优化
- **阈值**: 性能下降不超过20%

### 风险 3: 数据不一致
- **应对**: 数据一致性验证
- **工具**: 自动化数据对比脚本

### 风险 4: 功能异常
- **应对**: 全面功能测试
- **流程**: 测试->修复->验证循环

## 📞 沟通计划

### 内部沟通
- **每日站会**: 9:00 AM
- **技术评审**: 每周三 2:00 PM  
- **进度报告**: 每日 6:00 PM

### 外部沟通
- **用户通知**: 迁移前24小时
- **服务窗口**: 迁移期间提供支持
- **问题反馈**: 专属支持通道

---

**最后更新**: 2024-12-19  
**版本**: v1.0  
**状态**: 🟡 进行中

## 🎯 下一步行动

1. **立即执行**: 运行迁移测试验证当前状态
2. **今天目标**: 完成中风险文件的迁移
3. **明日计划**: 开始高风险文件的迁移准备
4. **本周目标**: 完成所有文件的迁移和测试

> 💡 提示: 每次迁移一个文件后立即运行测试，确保系统稳定性。