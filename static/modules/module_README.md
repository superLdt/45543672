# 模块目录说明文档

## 目录结构

```
static/modules/
├── index.js              # 主入口模块
├── TaskManager.js        # 任务管理核心模块
├── TaskRenderer.js       # 任务渲染模块
├── Pagination.js         # 分页管理模块
├── SupplierVehicleModal.js  # 供应商车辆信息确认模态框
├── companySelector.js    # 承运公司选择器
├── manualDispatch.js     # 人工派车页面逻辑
└── vehicleManagement.js  # 车辆管理模块
```

## 模块详细说明

### 1. index.js - 主入口模块
**功能描述**: 任务管理系统的主入口，负责模块初始化和通信协调。

**主要功能**:
- 导入所有核心模块和工具类
- 定义TaskManagementApp主类
- 提供模块间通信机制
- 导出初始化函数供外部调用

**导出内容**:
- `initTaskManagement()` - 初始化任务管理
- `initVehicleManagement()` - 初始化车辆管理
- 所有模块类供外部使用

### 2. TaskManager.js - 任务管理核心模块
**功能描述**: 负责任务数据的加载、搜索、分页等核心功能。

**核心类**: `TaskManager`

**主要方法**:
- `loadTasks(filters)` - 加载任务列表
- `searchTasks(searchParams)` - 搜索任务
- `getTaskDetail(taskId)` - 获取任务详情
- `getCurrentUserInfo()` - 获取当前用户信息

**特性**:
- 支持超时控制和重试机制
- 自动处理401未认证错误
- 兼容新旧API返回格式
- 事件驱动的数据更新

### 3. TaskRenderer.js - 任务渲染模块
**功能描述**: 负责任务数据的UI渲染和样式管理。

**核心类**: `TaskRenderer`

**主要方法**:
- `renderTasks(tasks)` - 渲染任务列表
- `renderTaskRow(task, index)` - 渲染单个任务行
- `renderPagination(paginationInfo)` - 渲染分页控件
- `showEmptyState(message)` - 显示空状态
- `showLoading(isLoading)` - 显示加载状态

**特性**:
- 响应式设计
- 状态徽章和时间优先级显示
- 鼠标悬停效果
- 空状态和加载状态处理

### 4. Pagination.js - 分页管理模块
**功能描述**: 提供独立的分页功能管理。

**核心类**: `Pagination`

**主要方法**:
- `setData(totalItems, currentPage)` - 设置分页数据
- `goToPage(page)` - 跳转到指定页
- `render()` - 渲染分页控件
- `getPaginationInfo()` - 获取当前分页信息

**特性**:
- 智能页码生成（最多显示7页）
- 事件回调机制
- 响应式按钮状态
- 分页信息显示

### 5. SupplierVehicleModal.js - 供应商车辆信息确认模态框
**功能描述**: 处理供应商车辆信息确认的UI显示和数据提交。

**核心类**: `SupplierVehicleModal` (单例模式)

**主要方法**:
- `show(task, context, options)` - 显示模态框
- `close()` - 关闭模态框
- `submit()` - 提交表单数据
- `renderModal()` - 渲染模态框内容

**特性**:
- 单例模式确保唯一实例
- 动态样式注入
- 表单验证和错误提示
- 动画效果支持

### 6. companySelector.js - 承运公司选择器
**功能描述**: 提供从数据库获取公司列表、搜索和选择功能。

**主要功能**:
- 从API加载公司数据
- 提供输入联想功能
- 验证公司选择的有效性
- 缓存公司数据

**导出方法**:
- `initializeCompanySelector(inputElementId)` - 初始化选择器
- `getSelectedCompany()` - 获取当前选择的公司
- `validateCompanySelection()` - 验证公司选择

### 7. manualDispatch.js - 人工派车页面逻辑
**功能描述**: 人工派车页面的核心逻辑，基于ES6模块重构。

**核心类**: `ManualDispatchApp`

**主要功能**:
- 初始化派车任务管理
- 处理表单提交和验证
- 重量与容积的自动映射
- 登录状态检查

**特性**:
- 模块化架构
- 错误处理和用户提示
- 重量-容积映射关系
- 表单验证机制

### 8. vehicleManagement.js - 车辆管理模块
**功能描述**: 提供车辆信息的CRUD操作、搜索筛选等功能。

**核心类**: `VehicleManager`

**主要方法**:
- `init()` - 初始化车辆管理器
- `loadVehicles()` - 加载车辆数据
- `searchVehicles(term)` - 搜索车辆
- `addVehicle(vehicleData)` - 添加车辆
- `updateVehicle(vehicleData)` - 更新车辆
- `deleteVehicle(vehicleId)` - 删除车辆

**特性**:
- 完整的CRUD操作
- 分页和搜索功能
- 权限检查
- 统一的响应处理

## 使用方式

### 基础初始化
```javascript
// 在HTML页面中引入
import { initTaskManagement } from './modules/index.js';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initTaskManagement();
});
```

### 模块使用示例
```javascript
// 使用TaskManager
import { TaskManager } from './modules/TaskManager.js';

const taskManager = new TaskManager({
    apiEndpoint: '/api/tasks',
    pageSize: 20
});

await taskManager.loadTasks({ status: 'pending' });

// 使用SupplierVehicleModal
import { SupplierVehicleModal } from './modules/SupplierVehicleModal.js';

SupplierVehicleModal.show(taskData, null, {
    returnUrl: '/tasks'
});
```

## 设计特点

1. **模块化架构**: 每个模块职责单一，易于维护和扩展
2. **事件驱动**: 使用事件机制实现模块间通信
3. **错误处理**: 统一的错误处理和用户提示
4. **响应式设计**: 适配不同屏幕尺寸
5. **缓存机制**: 合理使用缓存提高性能
6. **权限控制**: 内置权限检查和认证处理
7. **兼容性**: 支持新旧API格式的兼容处理

## 依赖关系

所有模块都依赖于以下工具类：
- `Debug.js` - 调试工具
- `ErrorHandler.js` - 错误处理

模块间的依赖关系：
- `index.js` → 所有其他模块
- `TaskManager.js` → `Debug.js`, `ErrorHandler.js`
- `TaskRenderer.js` → `Debug.js`
- `Pagination.js` → `Debug.js`
- `SupplierVehicleModal.js` → `Debug.js`, `ErrorHandler.js`
- `vehicleManagement.js` → `Debug.js`, `ErrorHandler.js`
- `manualDispatch.js` → 多个核心模块