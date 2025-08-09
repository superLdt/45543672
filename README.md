# 智能运力系统

## 版本历史
- **1.01** (2023-10-01)：初始版本，包含基础数据、成本分析、规划、对账、调度、系统和用户管理模块。

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
- `role_id`: 角色ID
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