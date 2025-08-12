# 人工派车功能数据库设计文档

## 双轨派车流程设计

### 流程概述
系统支持两种派车流程：
- **轨道A**：车间地调发起 → 区域调度审核 → 承运商响应 → 车间发车 → 承运商确认 → 车间最终确认
- **轨道B**：区域调度/超级管理员直接派车 → 承运商响应 → 车间发车 → 承运商确认 → 车间最终确认

### 数据库表结构

### 1. manual_dispatch_tasks - 派车任务表

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| task_id | TEXT | 任务ID（主键） | PRIMARY KEY |
| required_date | TEXT | 用车时间（日期） | NOT NULL |
| start_bureau | TEXT | 始发局 | NOT NULL |
| route_direction | TEXT | 路向 | NOT NULL |
| carrier_company | TEXT | 委办承运公司 | NOT NULL |
| route_name | TEXT | 邮路名称 | NOT NULL |
| transport_type | TEXT | 运输类型（单程/往返） | CHECK IN ('单程', '往返') |
| requirement_type | TEXT | 需求类型（正班/加班） | CHECK IN ('正班', '加班') |
| volume | INTEGER | 容积 | NOT NULL |
| weight | REAL | 重量 | NOT NULL |
| special_requirements | TEXT | 特殊要求 | 可选 |
| status | TEXT | 任务状态 | DEFAULT '待派车' |
| created_at | TEXT | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TEXT | 更新时间 | DEFAULT CURRENT_TIMESTAMP |
| **双轨派车字段** | | | |
| dispatch_track | TEXT | 流程轨道（轨道A/轨道B） | NOT NULL |
| initiator_role | TEXT | 发起者角色 | NOT NULL |
| initiator_user_id | INTEGER | 发起者用户ID | NOT NULL |
| initiator_department | TEXT | 发起者部门 | NOT NULL |
| audit_required | BOOLEAN | 是否需要审核 | NOT NULL |
| auditor_role | TEXT | 审核人角色 | 可选 |
| auditor_user_id | INTEGER | 审核人用户ID | 可选 |
| audit_status | TEXT | 审核状态 | DEFAULT '待审核' |
| audit_time | TEXT | 审核时间 | 可选 |
| audit_note | TEXT | 审核备注 | 可选 |
| current_handler_role | TEXT | 当前处理人角色 | 可选 |
| current_handler_user_id | INTEGER | 当前处理人用户ID | 可选 |

### 2. vehicles - 车辆信息表

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| task_id | TEXT | 关联任务ID | FOREIGN KEY REFERENCES manual_dispatch_tasks(task_id) |
| manifest_number | TEXT | 路单流水号 | NOT NULL |
| manifest_serial | TEXT | 路单流水号 | NOT NULL |
| dispatch_number | TEXT | 派车单号 | NOT NULL |
| license_plate | TEXT | 车牌号 | 可选 |
| carriage_number | TEXT | 车厢号 | NOT NULL |
| created_at | TEXT | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

### 3. dispatch_status_history - 派车状态历史表

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| task_id | TEXT | 关联任务ID | FOREIGN KEY REFERENCES manual_dispatch_tasks(task_id) |
| status_change | TEXT | 状态变更 | NOT NULL |
| operator | TEXT | 操作人 | NOT NULL |
| timestamp | TEXT | 时间戳 | DEFAULT CURRENT_TIMESTAMP |
| note | TEXT | 备注 | 可选 |

### 4. 用户权限相关表

#### 4.1 User - 用户表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 用户ID（主键） | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | 用户名 | UNIQUE NOT NULL |
| email | TEXT | 邮箱 | UNIQUE NOT NULL |
| password_hash | TEXT | 密码哈希 | NOT NULL |
| company_id | INTEGER | 公司ID | FOREIGN KEY REFERENCES Company(id) |
| is_active | BOOLEAN | 是否激活 | DEFAULT 1 |
| created_at | TEXT | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

#### 4.2 Role - 角色表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 角色ID（主键） | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | 角色名称 | UNIQUE NOT NULL |
| description | TEXT | 角色描述 | 可选 |
| created_at | TEXT | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

#### 4.3 UserRole - 用户角色关联表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | 用户ID | FOREIGN KEY REFERENCES User(id) |
| role_id | INTEGER | 角色ID | FOREIGN KEY REFERENCES Role(id) |
| assigned_at | TEXT | 分配时间 | DEFAULT CURRENT_TIMESTAMP |

#### 4.4 Permission - 权限表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 权限ID（主键） | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | 权限名称 | UNIQUE NOT NULL |
| resource | TEXT | 资源标识 | NOT NULL |
| action | TEXT | 操作类型 | NOT NULL |
| description | TEXT | 权限描述 | 可选 |

#### 4.5 RolePermission - 角色权限关联表
| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| role_id | INTEGER | 角色ID | FOREIGN KEY REFERENCES Role(id) |
| permission_id | INTEGER | 权限ID | FOREIGN KEY REFERENCES Permission(id) |
| granted_at | TEXT | 授权时间 | DEFAULT CURRENT_TIMESTAMP |

### 2. vehicles - 车辆信息表

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| task_id | TEXT | 关联任务ID | FOREIGN KEY |
| manifest_number | TEXT | 路单流水号 | - |
| manifest_serial | TEXT | 路单流水号 | - |
| dispatch_number | TEXT | 派车单号 | - |
| license_plate | TEXT | 车牌号 | NOT NULL |
| carriage_number | TEXT | 车厢号 | 可选 |
| created_at | TEXT | 创建时间 | DEFAULT CURRENT_TIMESTAMP |

### 3. dispatch_status_history - 派车状态历史表

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 记录ID（主键） | PRIMARY KEY AUTOINCREMENT |
| task_id | TEXT | 关联任务ID | FOREIGN KEY |
| status_change | TEXT | 状态变更 | NOT NULL |
| operator | TEXT | 操作人 | NOT NULL |
| timestamp | TEXT | 时间戳 | DEFAULT CURRENT_TIMESTAMP |
| note | TEXT | 备注 | 可选 |

## 双轨派车状态流转

### 轨道A状态流转（车间地调发起）
1. **待提交** - 车间地调创建需求，待提交审核
2. **待区域调度员审核** - 已提交，等待区域调度员审核
3. **待供应商响应** - 审核通过，等待供应商响应
4. **已响应** - 供应商确认接单，等待车间发车
5. **已发车** - 车间确认发车，等待供应商确认
6. **已到达** - 供应商确认到达，等待车间最终确认
7. **已完成** - 车间最终确认，流程结束

### 轨道B状态流转（区域调度/超级管理员直接派车）
1. **待供应商响应** - 区域调度/超级管理员直接派车
2. **已响应** - 供应商确认接单，等待车间发车
3. **已发车** - 车间确认发车，等待供应商确认
4. **已到达** - 供应商确认到达，等待车间最终确认
5. **已完成** - 车间最终确认，流程结束

### 实际数据库状态字段
基于实际数据库查询，状态字段支持以下值：
- 待提交
- 待区域调度员审核
- 待供应商响应
- 已响应
- 已发车
- 已到达
- 已完成

### 角色权限矩阵

| 角色 | 轨道A权限 | 轨道B权限 |
|------|-----------|-----------|
| **车间地调** | 发起任务 | 无 |
| **区域调度员** | 审核任务 | 直接派车 |
| **超级管理员** | 审核任务 | 直接派车 |
| **供应商** | 响应/确认 | 响应/确认 |

## 数据库管理

使用 `DatabaseManager` 类统一管理数据库操作：

### 自动创建表
- 应用启动时自动检查并创建缺失的表
- 自动添加双轨派车所需字段
- 位于 `app.py` 中的 `init_database()` 函数

### 核心方法

#### 创建任务（支持双轨派车）
```python
# 轨道A：车间地调发起
task_data = {
    'required_date': '2024-01-15',
    'start_bureau': '北京局',
    'route_direction': '北京-上海',
    'carrier_company': '中国邮政',
    'route_name': '京沪线',
    'transport_type': '单程',
    'requirement_type': '正班',
    'volume': 45,
    'weight': 8.5,
    'special_requirements': '需要冷链',
    'initiator_role': '车间地调',
    'initiator_user_id': 1,
    'initiator_department': '北京中心局',
    'audit_required': True,
    'auditor_role': '区域调度员',
    'auditor_user_id': 2
}

# 轨道B：区域调度直接派车
task_data = {
    'required_date': '2024-01-15',
    'start_bureau': '北京局',
    'route_direction': '北京-上海',
    'carrier_company': '中国邮政',
    'route_name': '京沪线',
    'transport_type': '单程',
    'requirement_type': '正班',
    'volume': 45,
    'weight': 8.5,
    'special_requirements': '需要冷链',
    'initiator_role': '区域调度员',
    'initiator_user_id': 2,
    'initiator_department': '北京中心局',
    'audit_required': False
}

result = db.create_dispatch_task(task_data)
```

#### 查询任务列表（支持双轨筛选）
```python
tasks = db.get_dispatch_tasks()
tasks = db.get_dispatch_tasks(dispatch_track='轨道A')
tasks = db.get_dispatch_tasks(initiator_role='车间地调')
tasks = db.get_dispatch_tasks(audit_status='待审核')
```

#### 更新任务状态（支持审核流程）
```python
# 审核任务（轨道A）
result = db.update_task_status(task_id, '已通过', '区域调度员', '审核通过，请尽快安排')

# 更新当前处理人
result = db.update_task_current_handler(task_id, '承运商', 4)
```

#### 分配车辆
```python
vehicle_data = {
    'manifest_number': 'LD20240115001',
    'manifest_serial': 'LD20240115001',
    'dispatch_number': 'PC20240115001',
    'license_plate': '京A12345',
    'carriage_number': '1号车厢'
}
result = db.assign_vehicle(task_id, vehicle_data)
```

#### 查询任务详情（包含双轨信息）
```python
task_detail = db.get_dispatch_task_detail(task_id)
# 返回包含：任务基本信息 + 双轨流程信息 + 当前处理人信息
```

#### 查询状态历史
```python
history = db.get_task_status_history(task_id)
```

## 测试验证

### 基础测试
运行测试脚本验证功能：
```bash
python test_new_dispatch_tables.py
```

测试内容包括：
- ✅ 表结构创建（包含双轨派车字段）
- ✅ 示例数据插入（包含轨道A和轨道B示例）
- ✅ 任务创建（支持双轨流程）
- ✅ 任务查询（支持双轨筛选）
- ✅ 状态更新（支持审核流程）
- ✅ 车辆分配
- ✅ 详情查询（包含双轨信息）
- ✅ 历史记录查询

### 双轨派车专项测试
```bash
# 测试轨道A：车间地调发起 → 区域调度审核
python -c "from db_manager import DatabaseManager; db = DatabaseManager(); db.connect(); result = db.create_dispatch_task({'required_date': '2024-01-20', 'start_bureau': '测试局', 'route_direction': '测试-路线', 'carrier_company': '测试公司', 'route_name': '测试线路', 'transport_type': '单程', 'requirement_type': '正班', 'volume': 50, 'weight': 10.0, 'initiator_role': '车间地调', 'initiator_user_id': 1, 'initiator_department': '测试部门', 'audit_required': True}); print('轨道A任务创建成功:', result); db.disconnect()"

# 测试轨道B：区域调度直接派车
python -c "from db_manager import DatabaseManager; db = DatabaseManager(); db.connect(); result = db.create_dispatch_task({'required_date': '2024-01-21', 'start_bureau': '测试局', 'route_direction': '测试-路线', 'carrier_company': '测试公司', 'route_name': '测试线路', 'transport_type': '单程', 'requirement_type': '加班', 'volume': 60, 'weight': 12.0, 'initiator_role': '区域调度员', 'initiator_user_id': 2, 'initiator_department': '测试部门', 'audit_required': False}); print('轨道B任务创建成功:', result); db.disconnect()"
```

### 字段验证
```bash
# 验证双轨派车字段
python -c "import sqlite3; conn = sqlite3.connect('database.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM pragma_table_info(\"manual_dispatch_tasks\") WHERE name LIKE \"%dispatch_track%\" OR name LIKE \"%initiator_%\" OR name LIKE \"%audit_%\" OR name LIKE \"%current_handler_%\"'); print('双轨派车字段数量:', cursor.fetchone()[0]); conn.close()"
```

## 文件说明

- `db_manager.py` - 数据库管理类，包含所有表结构和操作方法（已支持双轨派车）
- `app.py` - 应用入口，包含自动创建表的逻辑
- `test_new_dispatch_tables.py` - 测试脚本，验证所有功能
- `DATABASE_DESIGN.md` - 本设计文档（已更新双轨派车设计）
- `DATABASE_MIGRATION_GUIDE.md` - 数据库迁移指南

## 版本更新记录

### v2.0 - 双轨派车功能
- ✅ 新增11个双轨派车相关字段
- ✅ 支持轨道A（车间地调→区域调度审核）流程
- ✅ 支持轨道B（区域调度/超级管理员直接派车）流程
- ✅ 自动数据库迁移和字段添加
- ✅ 角色权限矩阵实现
- ✅ 状态流转机制优化