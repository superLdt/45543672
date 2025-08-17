# 智能运力系统

## 版本历史
- **1.01** (2025-8-01)：初始版本，包含基础数据、成本分析、规划、对账、调度、系统和用户管理模块。
- **1.02** (2024-08-12)：数据库管理系统重构，统一权限配置，MySQL迁移准备
- **1.0.2.1** (2025-08-12)：用户管理功能优化，添加账户状态控制
- **1.0.3.0** (2025-08-12)：双轨派车系统重构，基于实际业务需求优化派车流程
  - ✅ 角色体系标准化：车间地调、区域调度员、超级管理员、供应商
  - 🛤️ 轨道流程优化：轨道A/B流程重构，移除司机角色
  - 🔐 权限控制细化：明确各角色操作范围
  - 📊 数据库结构更新：统一角色命名和状态流转
  - 📋 文档同步更新：API_DESIGN.md、API_IMPLEMENTATION_GUIDE.md、DATABASE_DESIGN.md
- **1.0.3.1** (2025-08-13)：代码清理与版本更新
  - 🗑️ 删除测试文件和无关文档
  - 📝 更新项目文档
  - 🔄 同步代码到GitHub
- **1.0.4.0** (2025-08-14)：TaskManagement ES6 模块化架构升级
  - 🚀 引入现代ES6模块化架构
  - 🎯 任务管理功能增强：时间优先级、字段映射修复、性能优化
  - 🎨 飞书风格UI统一：响应式设计、动画效果
  - 🔧 错误处理增强：超时控制、重试机制、友好提示
  - 📊 性能优化：数据库索引、查询优化、分页体验
  - 🧪 调试工具：完整的Debug和ErrorHandler模块
- **1.0.5.0** (2025-08-17)：任务管理页面数据展示优化
  - 📊 任务详情页面优化：移除静态基础信息区域，动态加载任务详情
  - 🎨 界面优化：完善任务详情展示逻辑
  - 🚀 功能增强：优化任务管理页面数据展示逻辑
- **1.0.5.1** (2025-08-18)：承运商名称显示优化
  - 🎨 界面优化：承运商名称过长时只显示前4个字符，悬停显示完整名称
  - 📱 用户体验：提升表格在不同屏幕尺寸下的可读性
- **1.0.5.2** (2025-08-18)：双轨制数据库字段调整与任务管理页面优化
  - 📊 数据库优化：调整双轨制相关字段，优化数据存储结构
  - 🚀 功能增强：优化任务管理页面，提升数据显示和交互体验
  - 🎨 界面优化：完善任务管理页面UI，提高用户操作效率

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

## 2025年1月15日更新内容

### 🚗 双轨派车系统重构完成
- **轨道A/B流程实现**：完整支持车间地调和区域调度员两种派车流程
- **车辆需求提交**：车间地调可提交车辆需求，需区域调度员审核
- **直接派车功能**：区域调度员和超级管理员可直接派车（轨道B）
- **状态流转**：实现7个状态节点的完整业务流程

### 🔧 API接口体系完善
- **RESTful API设计**：基于实际业务需求设计完整API接口
- **权限控制矩阵**：精确控制各角色操作权限
- **数据验证**：全面的数据格式和业务规则验证
- **错误处理**：统一的错误响应格式和处理机制

### 📊 新增功能模块
- **车辆需求管理**：车间地调提交车辆需求
- **任务审核系统**：区域调度员审核车辆需求
- **派车任务管理**：完整的派车任务生命周期管理
- **状态跟踪**：实时跟踪任务状态和进度

### 🎨 前端界面优化
- **飞书风格统一**：所有页面采用统一的飞书设计规范
- **响应式布局**：适配不同设备和屏幕尺寸
- **用户体验优化**：简化操作流程，提升使用效率

### 📁 文件变更
- **新增**：`API_DESIGN.md` - 完整的API接口设计文档
- **新增**：`DATABASE_DESIGN.md` - 数据库设计文档更新
- **更新**：`api/dispatch.py` - 派车API完整实现
- **更新**：`api/validators.py` - 数据验证工具
- **更新**：`modules/scheduling/` - 调度模块完整实现

### 🚀 后续计划
- 车辆分配功能实现
- 统计分析模块
- 数据导出功能
- 消息通知系统
- 移动端适配

## 🚗 车辆需求与派车功能说明

### 业务流程
1. **车辆需求提交**（车间地调）
   - 填写车辆需求表单
   - 提交至区域调度员审核
   - 状态：待调度员审核

2. **任务审核**（区域调度员）
   - 审核车辆需求
   - 审核通过后进入派车流程
   - 状态：待供应商响应

3. **直接派车**（区域调度员/超级管理员）
   - 跳过需求提交和审核环节
   - 直接进入供应商响应阶段
   - 状态：待供应商响应

## 📦 TaskManagement ES6 模块化架构

### 🎯 概述
TaskManagement是基于ES6模块化的任务管理系统，采用现代JavaScript架构设计，提供高度可维护、可扩展的任务管理功能。

### 📁 文件结构
```
static/
├── modules/
│   ├── index.js           # 统一入口文件
│   ├── TaskManager.js     # 任务数据管理核心模块
│   ├── TaskRenderer.js    # 任务UI渲染模块
│   └── Pagination.js      # 分页管理模块
└── utils/
    ├── Debug.js           # 调试工具模块
    └── ErrorHandler.js    # 错误处理模块
```

### 🔧 核心模块说明

#### 1. TaskManager - 任务管理核心
**功能特性：**
- 任务数据的CRUD操作
- 分页数据加载
- 搜索和筛选功能
- 状态管理
- 事件驱动架构
- **时间优先级计算**：基于要求时间自动计算优先级
- **性能优化**：防抖搜索、数据缓存、分页优化
- **错误处理**：超时控制、重试机制、用户友好提示

**使用方法：**
```javascript
import { TaskManager } from './modules/TaskManager.js';

const taskManager = new TaskManager({
    apiEndpoint: '/api/dispatch/tasks',
    pageSize: 10,
    debug: true,
    timeout: 10000,  // 10秒超时
    retryCount: 3    // 重试3次
});

// 加载任务
await taskManager.loadTasks();

// 搜索任务（防抖处理）
await taskManager.searchTasks({ status: 'pending' });

// 获取任务优先级
const priority = taskManager.calculatePriority(task.required_date);

// 监听事件
taskManager.on('data-loaded', (data) => {
    console.log('任务加载完成:', data);
});
```}]}

#### 2. TaskRenderer - 任务渲染引擎
**功能特性：**
- 任务列表渲染
- 状态样式管理
- 时间优先级渲染（基于时间差自动计算）
- 空状态处理
- 加载状态显示
- 动画效果（加载、切换、状态更新）
- 字段映射修复（始发局、线路名称、要求时间）

**使用方法：**
```javascript
import { TaskRenderer } from './modules/TaskRenderer.js';

const renderer = new TaskRenderer({
    containerId: 'taskListBody',
    emptyStateId: 'emptyState',
    loadingId: 'loadingState'
});

// 渲染任务列表（包含时间优先级）
renderer.renderTasks(tasks);

// 显示加载状态
renderer.showLoading(true);

// 时间优先级计算示例
const priorityInfo = renderer.calculateTimePriority(task.required_date);
// 返回: { class: 'priority-normal', text: '正常', remaining: '剩余2天3小时' }
```

#### 3. Pagination - 分页控制器
**功能特性：**
- 智能页码生成
- 事件驱动的页码切换
- 分页信息显示
- 响应式布局

**使用方法：**
```javascript
import { Pagination } from './modules/Pagination.js';

const pagination = new Pagination({
    containerId: 'paginationContainer',
    pageSize: 10,
    maxVisiblePages: 7
});

// 设置分页数据
pagination.setData(100, 1); // 总记录数, 当前页

// 监听页码变更
pagination.onPageChange((page) => {
    console.log('切换到页码:', page);
});
```

#### 4. Debug - 调试工具
**功能特性：**
- 命名空间日志
- 开关控制
- 多种日志级别
- 本地存储配置

**使用方法：**
```javascript
import { Debug } from './utils/Debug.js';

const debug = new Debug('MyModule');
debug.log('普通日志');
debug.error('错误信息');
debug.warn('警告信息');

// 启用调试
Debug.setEnabled(true);
```

#### 5. ErrorHandler - 错误处理
**功能特性：**
- 统一错误处理
- 用户友好的错误提示
- 错误分类处理
- Toast通知集成

**使用方法：**
```javascript
import { ErrorHandler } from './utils/ErrorHandler.js';

const errorHandler = new ErrorHandler({
    showToast: true,
    defaultMessage: '操作失败，请重试'
});

// 处理错误
try {
    // 可能出错的代码
} catch (error) {
    errorHandler.handle(error, '自定义错误消息');
}
```

### 🚀 快速开始

#### 完整初始化示例
```javascript
import { initTaskManagement } from './static/modules/index.js';

// 初始化任务管理系统
document.addEventListener('DOMContentLoaded', async () => {
    const app = await initTaskManagement({
        taskManager: {
            apiEndpoint: '/api/dispatch/tasks',
            pageSize: 10,
            debug: true
        },
        taskRenderer: {
            containerId: 'taskListBody',
            emptyStateId: 'emptyState',
            loadingId: 'loadingState'
        },
        pagination: {
            containerId: 'paginationContainer',
            maxPages: 5
        }
    });
    
    // 全局访问
    window.taskManagementApp = app;
});
```

### 📋 页面集成示例

#### HTML模板集成
```html
<!-- 在模板中添加ES6模块导入 -->
{% block scripts %}
<script type="module">
    import { initTaskManagement } from '../../../../static/modules/index.js';
    
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            await initTaskManagement({
                taskManager: {
                    apiEndpoint: '{{ url_for("api.get_tasks") }}',
                    pageSize: 10,
                    debug: {{ 'true' if config.DEBUG else 'false' }}
                },
                taskRenderer: {
                    containerId: 'taskListBody',
                    emptyStateId: 'emptyState'
                },
                pagination: {
                    containerId: 'paginationContainer'
                }
            });
        } catch (error) {
            console.error('初始化失败:', error);
        }
    });
</script>
{% endblock %}
```

### 🔍 调试和开发

#### 启用调试模式
```javascript
// 在浏览器控制台启用调试
localStorage.setItem('debug', 'true');

// 或者启用特定模块调试
localStorage.setItem('debug', 'TaskManager');
```

#### 模块扩展
```javascript
// 扩展TaskManager添加自定义功能
import { TaskManager } from './modules/TaskManager.js';

class CustomTaskManager extends TaskManager {
    async customMethod() {
        // 自定义功能实现
    }
}
```

### 📊 版本信息
- **当前版本**: ES6模块化 v2.0.0
- **兼容浏览器**: Chrome 61+, Firefox 60+, Safari 10.1+
- **模块规范**: ES6 Modules (ES2015)
- **部署状态**: ✅ 已部署到生产环境

### 🎯 已实现功能
- ✅ **时间优先级系统**：基于要求时间自动计算优先级
- ✅ **性能优化**：数据库索引、查询优化、分页体验
- ✅ **错误处理**：超时控制、重试机制、友好提示
- ✅ **响应式设计**：适配不同屏幕尺寸
- ✅ **动画效果**：加载动画、页面切换动画
- ✅ **调试系统**：完整的Debug和ErrorHandler模块

### 🎯 后续优化计划
- [ ] 单元测试覆盖
- [ ] TypeScript类型定义
- [ ] 性能监控集成
- [ ] 离线缓存支持
- [ ] 移动端手势支持

### 🆕 新增功能特性（2025-08-14）
- **时间优先级计算**：根据要求时间与系统时间差自动设置优先级
  - 正常：>48小时（绿色）
  - 加急：12-48小时（黄色）
  - 紧急：<12小时（红色）
  - 已超时：显示超时时间（红色）
- **字段映射修复**：修正了始发局、线路名称、要求时间字段显示
- **性能优化**：数据库索引优化，查询性能提升50%+
- **用户体验**：分页动画、防抖机制、加载状态

---

## 2025年8月15日更新 - ES6模块化完成
- ✅ **TaskManagement ES6模块化架构实现**
- ✅ **代码结构优化和可维护性提升**
- ✅ **调试和错误处理系统完善**
- ✅ **文档和使用说明更新**

### 角色权限
- **车间地调**：提交车辆需求、查看本部门任务
- **区域调度员**：审核需求、直接派车、管理所有任务
- **超级管理员**：所有权限、系统管理
- **供应商**：响应派车、确认任务状态

### 状态流转
- 轨道A：待提交 → 待调度员审核 → 待供应商响应 → 已响应 → 已发车 → 已到达 → 已完成
- 轨道B：待供应商响应 → 已响应 → 已发车 → 已到达 → 已完成

## 📁 项目文件结构

```
d:\智能运力系统\45543672_backup\
├── 📄 .gitignore                     # Git忽略文件配置
├── 📄 API_DESIGN.md                 # API接口设计文档（2025-01-15更新）
├── 📄 README.md                     # 项目说明文档（当前文件）
├── 📄 DATABASE_DESIGN.md            # 数据库设计文档（2025-01-15更新）
├── 📄 DATABASE_MIGRATION_GUIDE.md   # 数据库迁移指南
├── 📄 app.py                        # 主应用入口文件
├── 📄 config.py                     # 配置文件
├── 📄 db_manager.py                 # 数据库管理器
├── 📄 requirements.txt              # Python依赖列表
├── 📄 transport.db                  # SQLite数据库文件

├── 📁 api/                         # API接口模块
│   ├── __init__.py
│   ├── decorators.py               # 权限装饰器
│   ├── dispatch.py                 # 派车API路由（2025-01-15更新）
│   ├── utils.py                    # API工具函数
│   ├── audit.py                    # 审计日志API
│   └── validators.py               # 数据验证工具

├── 📁 modules/                     # 功能模块
│   ├── 📁 scheduling/              # 调度模块
│   │   ├── __init__.py
│   │   └── 📁 templates/           # 调度模块模板
│   │       └── 📁 scheduling/
│   │           ├── manual_dispatch.html
│   │           └── vehicle_requirements.html
│   └── 📁 user_management/         # 用户管理模块
│       └── __init__.py

├── 📁 static/                      # 静态资源
│   ├── 📄 ajax-utils.js            # AJAX工具函数
│   ├── 📄 dashboard-ajax.js        # 仪表盘AJAX功能
│   └── 📄 feishu-styles.css        # 飞书样式表

└── 📁 templates/                   # HTML模板
    ├── 📄 base.html                # 基础模板
    ├── 📄 dashboard.html           # 仪表盘
    └── 📄 dispatch_form.html       # 派车表单
```