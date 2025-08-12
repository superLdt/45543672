# 智能运力系统

## 版本历史
- **1.01** (2023-10-01)：初始版本，包含基础数据、成本分析、规划、对账、调度、系统和用户管理模块。
- **1.02** (2024-08-12)：数据库管理系统重构，统一权限配置，MySQL迁移准备
- **1.0.2.1** (2025-08-12)：用户管理功能优化，添加账户状态控制
- **1.0.3.0** (2025-08-12)：双轨派车系统重构，基于实际业务需求优化派车流程
  - ✅ 角色体系标准化：车间地调、区域调度员、超级管理员、供应商
  - 🛤️ 轨道流程优化：轨道A/B流程重构，移除司机角色
  - 🔐 权限控制细化：明确各角色操作范围
  - 📊 数据库结构更新：统一角色命名和状态流转
  - 📋 文档同步更新：API_DESIGN.md、API_IMPLEMENTATION_GUIDE.md、DATABASE_DESIGN.md

## 项目概述
智能运力系统是一个集成了多种功能模块的综合管理系统，旨在优化运输资源调度、成本分析和路线规划等业务流程。

## 模块结构

### 1. 基础数据模块 (basic_data)
- 车辆信息管理
- 路线基础数据
- 数据维护更新
- 单位信息管理（包括添加、编辑、删除和Excel导出功能）

### 2. 成本分析模块 (cost_analysis)
- 邮路成本分析
- 成本报表生成
- 成本优化建议

### 3. 规划模块 (planning)
- 路线规划
- 路径优化
- 运力预测

### 4. 对账模块 (reconciliation)
- 交易记录查询
- 财务对账
- 报表生成
- 数据导入
- 审批流程
- 异常处理
- 飞书协作
- 结算单据管理
- 数据查询

### 5. 调度模块 (scheduling)
- 车辆管理
- 任务分配
- 实时监控

### 6. 系统模块 (system)
- 用户管理
- 系统设置
- 角色权限配置
- 页面配置

### 7. 用户管理模块 (user_management)
- 用户列表与搜索
- 用户创建与编辑
- 角色管理
- 权限控制

## 技术栈
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript

## 数据库架构
系统使用SQLite数据库，包含以下主要表结构：

### 1. Company (公司信息表)
- `id`: 主键，公司ID
- `name`: 公司名称
- `bank_account`: 银行账户
- `bank_name`: 银行名称
- `address`: 公司地址
- `contact_person`: 联系人
- `contact_phone`: 联系电话
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 2. Role (角色表)
- `id`: 主键，角色ID
- `name`: 角色名称
- `description`: 角色描述
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 3. Permission (权限表)
- `id`: 主键，权限ID
- `name`: 权限名称
- `module`: 所属模块
- `description`: 权限描述
- `created_at`: 创建时间

### 4. UserRole (用户-角色关联表)
- `user_id`: 主键，用户ID
- `role_id`: 主键，角色ID

### 5. RolePermission (角色-权限关联表)
- `role_id`: 主键，角色ID
- `permission_id`: 主键，权限ID

### 6. modules (模块表)
- `id`: 主键，模块ID
- `name`: 模块名称
- `display_name`: 显示名称
- `route_name`: 路由名称
- `icon_class`: 图标类名
- `sort_order`: 排序序号
- `is_active`: 是否激活
- `parent_id`: 父模块ID

### 7. role_module_permissions (角色-模块权限关联表)
- `id`: 主键，记录ID
# 已移除: role_id (现在通过UserRole关联表管理)
- `module_id`: 模块ID
- `can_view`: 查看权限
- `can_edit`: 编辑权限
- `can_delete`: 删除权限

### 8. User (用户表)
- `id`: 主键，用户ID
- `username`: 用户名
- `password`: 密码(加密存储)
- `full_name`: 姓名
- `email`: 邮箱
- `phone`: 电话
- `company_id`: 公司ID
- `role_id`: 角色ID
- `is_active`: 是否激活
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 运行说明
1. 安装依赖：`pip install -r requirements.txt`
2. 运行应用：`python app.py`

## 2024年8月12日更新内容

### 🔧 数据库管理系统重构
- **统一数据库管理**：创建综合`DatabaseManager`类，集中管理所有数据库操作
- **权限配置整合**：将`init_permissions.py`功能整合到`DatabaseManager`，删除冗余文件
- **职责分离**：将数据库初始化逻辑从`app.py`迁移到`db_manager.py`，减少代码重复
- **MySQL迁移准备**：创建`DATABASE_MIGRATION_GUIDE.md`，提供完整的SQLite到MySQL迁移方案

### 📊 代码优化成果
- **代码量减少**：从`app.py`中移除约300行数据库初始化代码
- **功能增强**：新增权限检查和修复功能
- **扩展性提升**：预留接口支持未来业务表扩展
- **维护简化**：所有数据库操作统一入口，便于维护

### 🎯 新增功能
- **权限管理**：自动配置角色权限关系
- **数据验证**：检查并修复权限配置问题
- **一键初始化**：支持应用启动和手动两种数据库初始化方式

### 📁 文件变更
- **新增**：`DATABASE_MIGRATION_GUIDE.md` - MySQL迁移指南
- **新增**：`test_permissions.py` - 权限配置测试脚本
- **删除**：`init_permissions.py` - 功能已整合到db_manager.py
- **更新**：`db_manager.py` - 新增权限配置和检查功能
- **更新**：`app.py` - 简化数据库初始化调用

### 🚀 后续计划
- 完成MySQL数据库迁移
- 优化数据库连接池管理
- 添加数据库迁移脚本
- 完善数据库备份和恢复机制

## 📁 项目文件结构

```
d:\智能运力系统\45543672_backup\
├── 📄 .gitignore                     # Git忽略文件配置
├── 📄 API_DESIGN.md                 # API接口设计文档（2025-01-15更新）
├── 📄 API_IMPLEMENTATION_GUIDE.md   # API实现指南（2025-01-15更新）
├── 📄 CHANGELOG.md                  # 版本更新日志
├── 📄 DATABASE_DESIGN.md            # 数据库设计文档（2025-01-15更新）
├── 📄 DATABASE_INIT_GUIDE.md       # 数据库初始化指南
├── 📄 DATABASE_MIGRATION_GUIDE.md   # 数据库迁移指南
├── 📄 README.md                     # 项目说明文档（当前文件）
├── 📄 analyze_database.py           # 数据库分析工具
├── 📄 app.py                        # 主应用入口文件
├── 📄 config.py                     # 配置文件
├── 📄 db_manager.py                 # 数据库管理器
├── 📄 requirements.txt              # Python依赖列表
├── 📄 test_api_integration.py       # API集成测试
├── 📄 test_new_dispatch_tables.py  # 新派车表测试
├── 📄 test_permissions.py          # 权限测试脚本
├── 📄 transport_management.db      # SQLite数据库文件
├── 📄 开发日志.docx               # 开发过程记录

├── 📁 api/                         # API接口模块
│   ├── __init__.py
│   ├── decorators.py               # 权限装饰器
│   ├── dispatch.py                 # 派车API路由（2025-01-15更新）
│   └── utils.py                    # API工具函数

├── 📁 modules/                     # 业务功能模块
│   ├── basic_data/                 # 基础数据模块
│   │   ├── __init__.py
│   │   └── templates/
│   ├── cost_analysis/               # 成本分析模块
│   │   ├── __init__.py
│   │   └── templates/
│   ├── planning/                    # 规划模块
│   │   ├── __init__.py
│   │   └── templates/
│   ├── reconciliation/              # 对账模块
│   │   ├── __init__.py
│   │   └── templates/
│   ├── scheduling/                  # 调度模块
│   │   ├── __init__.py
│   │   └── templates/
│   ├── system/                      # 系统管理模块
│   │   ├── __init__.py
│   │   └── templates/
│   └── user_management/             # 用户管理模块
│       ├── __init__.py
│       └── templates/

├── 📁 static/                      # 静态资源
│   ├── FEISHU_STYLES_GUIDE.md      # 飞书样式指南
│   ├── example-usage.html          # 使用示例
│   ├── feishu-styles.css           # 飞书样式文件
│   ├── script.js                   # JavaScript脚本
│   └── styles.css                  # 样式文件

└── 📁 templates/                   # HTML模板
    ├── base.html
    ├── dashboard.html
    ├── error.html
    ├── login.html
    ├── partials/
    │   └── full_menu.html
    └── under_development.html
```

## 📅 2025年1月15日重要更新

### 🔄 双轨派车系统重构
基于实际业务需求，全面重构派车业务流程，统一角色体系和状态流转：

#### ✅ 角色体系标准化
- **车间地调**：负责轨道A任务发起和本角色任务管理
- **区域调度员**：负责轨道A/B任务审核和直接派车
- **超级管理员**：拥有系统全部权限
- **供应商**：负责车辆分配、司机分配和任务响应确认

#### 🛤️ 轨道流程优化
**轨道A流程**：
车间地调(发起) → 区域调度员(审核) → 供应商(响应) → 车间(发车) → 供应商(确认) → 车间(最终确认)

**轨道B流程**：
区域调度员(直接派车) → 供应商(响应) → 车间(发车) → 供应商(确认) → 车间(最终确认)

#### 📝 文档同步更新
- **API_DESIGN.md**：更新接口设计、权限矩阵、状态流转
- **API_IMPLEMENTATION_GUIDE.md**：修正实现逻辑，移除司机角色
- **DATABASE_DESIGN.md**：更新数据库表结构和角色权限定义
- **api/dispatch.py**：修正权限装饰器和状态设置

#### 🔐 权限控制细化
新增权限控制矩阵，明确各角色操作范围：
- 车间地调：仅轨道A任务创建和本角色任务管理
- 区域调度员：轨道A/B任务审核和直接派车
- 供应商：仅响应确认（不允许驳回），车辆分配和司机分配
- 超级管理员：全权限管理

#### 📊 数据库结构更新
- 移除"运输处"和"车队派车"角色
- 统一使用"供应商"角色
- 更新状态字段值为：待提交、待区域调度员审核、待供应商响应、已响应、已发车、已到达、已完成

### 🎯 变更影响范围
本次更新涉及以下文件：
- `API_DESIGN.md` - 接口设计规范
- `API_IMPLEMENTATION_GUIDE.md` - 实现指南
- `DATABASE_DESIGN.md` - 数据库设计
- `api/dispatch.py` - API路由实现
- 相关权限验证逻辑