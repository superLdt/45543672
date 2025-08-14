# 双轨派车API文档

## 概述
本API实现了双轨派车系统的核心功能，支持轨道A（内部审核流程）和轨道B（供应商响应流程）两种派车模式。

## 目录结构
```
api/
├── __init__.py      # API蓝图注册
├── dispatch.py      # 派车任务API
├── audit.py         # 审核流程API
├── validators.py    # 数据验证器
├── decorators.py    # 权限装饰器
└── utils.py         # 工具函数
```

## API端点

### 1. 派车任务管理

#### 创建任务
```
POST /api/dispatch/tasks
```
**权限**: 车间地调、区域调度员、超级管理员

**请求体**:
```json
{
  "title": "任务标题",
  "vehicle_type": "小型货车",
  "purpose": "货物运输",
  "start_location": "起点",
  "end_location": "终点",
  "expected_start_time": "2024-01-15T09:00:00",
  "expected_end_time": "2024-01-15T17:00:00",
  "dispatch_track": "轨道A",
  "cargo_weight": 2.5,
  "cargo_volume": 15,
  "special_requirements": "特殊要求"
}
```

#### 获取任务列表
```
GET /api/dispatch/tasks
```
**权限**: 所有角色

**查询参数**:
- `status`: 任务状态
- `dispatch_track`: 派车轨道(A/B)
- `page`: 页码(默认1)
- `limit`: 每页条数(默认20)

#### 获取任务详情
```
GET /api/dispatch/tasks/{task_id}
```
**权限**: 所有角色

#### 更新任务信息
```
PUT /api/dispatch/tasks/{task_id}
```
**权限**: 车间地调、区域调度员、超级管理员

### 2. 审核流程

#### 提交审核
```
POST /api/dispatch/tasks/{task_id}/submit
```
**权限**: 根据当前处理者角色自动判断

#### 审核任务
```
POST /api/dispatch/tasks/{task_id}/audit
```
**权限**: 根据当前处理者角色自动判断

**请求体**:
```json
{
  "audit_result": "approved",
  "comments": "审核意见"
}
```

#### 更新任务状态
```
PUT /api/dispatch/tasks/{task_id}/status
```
**权限**: 当前处理者

**请求体**:
```json
{
  "status": "已派车",
  "comments": "状态更新说明"
}
```

#### 获取任务历史
```
GET /api/dispatch/tasks/{task_id}/history
```
**权限**: 所有角色

## 状态流转

### 轨道A流程
```
待提交 → 待区域调度员审核 → 待派车 → 已派车 → 已完成
```

### 轨道B流程
```
待供应商响应 → 待派车 → 已派车 → 已完成
```

## 权限矩阵

| 角色 | 创建任务 | 提交审核 | 审核任务 | 查看任务 | 更新任务 |
|------|----------|----------|----------|----------|----------|
| 车间地调 | ✓ | ✓ | ✗ | ✓ | ✓ |
| 区域调度员 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 超级管理员 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 供应商 | ✗ | ✗ | ✓ | ✓ | ✗ |

## 错误码说明

- `4001`: 数据验证失败
- `4002`: 权限不足
- `4041`: 任务不存在
- `5001`: 数据库错误

## 使用示例

### 创建任务并提交审核

```python
import requests

# 1. 登录
session = requests.Session()
session.post('http://localhost:5000/login', data={
    'username': 'test_user',
    'password': 'test_password'
})

# 2. 创建任务
task_data = {
    'title': '测试任务',
    'vehicle_type': '小型货车',
    'start_location': '北京',
    'end_location': '天津',
    'dispatch_track': '轨道A'
}
response = session.post('http://localhost:5000/api/dispatch/tasks', json=task_data)
task_id = response.json()['data']['task_id']

# 3. 提交审核
session.post(f'http://localhost:5000/api/dispatch/tasks/{task_id}/submit')

# 4. 审核任务
audit_data = {
    'audit_result': 'approved',
    'comments': '同意派车'
}
session.post(f'http://localhost:5000/api/dispatch/tasks/{task_id}/audit', json=audit_data)
```

## 测试

系统已集成测试，可直接通过浏览器访问测试：
1. 访问 http://localhost:5000 登录系统
2. 通过前端界面创建和测试派车流程
3. 使用浏览器开发者工具查看API调用

## 注意事项

1. 所有API端点都需要登录会话
2. 权限验证基于用户角色自动判断
3. 数据库操作使用统一的DatabaseManager管理
4. 时间格式使用ISO 8601标准
5. 所有响应都使用统一的JSON格式