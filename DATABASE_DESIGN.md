# 人工派车功能数据库设计文档

## 数据库表结构

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

## 数据库管理

使用 `DatabaseManager` 类统一管理数据库操作：

### 自动创建表
- 应用启动时自动检查并创建缺失的表
- 位于 `app.py` 中的 `init_database()` 函数

### 核心方法

#### 创建任务
```python
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
    'operator': '管理员'
}
result = db.create_dispatch_task(task_data)
```

#### 查询任务列表
```python
tasks = db.get_dispatch_tasks()
tasks = db.get_dispatch_tasks(status='待派车')
tasks = db.get_dispatch_tasks(date_from='2024-01-01', date_to='2024-01-31')
```

#### 更新任务状态
```python
result = db.update_task_status(task_id, '已分配', '管理员', '车辆已安排')
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

#### 查询任务详情
```python
task_detail = db.get_dispatch_task_detail(task_id)
```

#### 查询状态历史
```python
history = db.get_task_status_history(task_id)
```

## 测试验证

运行测试脚本验证功能：
```bash
python test_new_dispatch_tables.py
```

测试内容包括：
- ✅ 表结构创建
- ✅ 示例数据插入
- ✅ 任务创建
- ✅ 任务查询
- ✅ 状态更新
- ✅ 车辆分配
- ✅ 详情查询
- ✅ 历史记录查询

## 文件说明

- `db_manager.py` - 数据库管理类，包含所有表结构和操作方法
- `app.py` - 应用入口，包含自动创建表的逻辑
- `test_new_dispatch_tables.py` - 测试脚本，验证所有功能
- `DATABASE_DESIGN.md` - 本设计文档