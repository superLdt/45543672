# 工具类目录说明文档

## 目录结构

```
static/utils/
├── Debug.js        # 调试工具类
└── ErrorHandler.js # 错误处理工具类
```

## 工具类详细说明

### 1. Debug.js - 调试工具类

**功能描述**: 提供统一的调试日志输出，支持命名空间和开关控制。

**核心类**: `Debug`

**构造函数**:
```javascript
const debug = new Debug('MyModule');
```

**主要方法**:
- `log(...args)` - 输出普通日志
- `error(...args)` - 输出错误日志
- `warn(...args)` - 输出警告日志
- `info(...args)` - 输出信息日志

**静态方法**:
- `Debug.setEnabled(enabled)` - 设置全局调试开关
- `Debug.isEnabled()` - 获取当前调试状态

**使用示例**:
```javascript
import { Debug } from './utils/Debug.js';

const debug = new Debug('MyModule');
debug.log('初始化完成');
debug.error('发生错误:', error);

// 设置调试开关
Debug.setEnabled(true);
```

**调试开关控制**:
- 在浏览器控制台执行: `localStorage.setItem('debug', 'true')`
- 或者在URL添加参数: `?debug=true`

### 2. ErrorHandler.js - 错误处理工具类

**功能描述**: 提供统一的错误处理和用户提示，支持自定义消息和Toast显示。

**核心类**: `ErrorHandler`

**构造函数**:
```javascript
const errorHandler = new ErrorHandler({
    defaultMessage: '操作失败',
    showToast: true
});
```

**主要方法**:
- `handle(error, customMessage)` - 处理错误
- `getErrorMessage(error)` - 获取错误消息
- `showToast(message, type)` - 显示Toast提示
- `confirm(message, title)` - 显示确认对话框

**错误消息映射**:
- 400: "请求参数错误"
- 401: "请重新登录"
- 403: "权限不足"
- 404: "资源不存在"
- 500: "服务器内部错误"

**使用示例**:
```javascript
import { ErrorHandler } from './utils/ErrorHandler.js';

const errorHandler = new ErrorHandler();

try {
    await fetchData();
} catch (error) {
    errorHandler.handle(error, '加载数据失败');
}

// 显示确认对话框
const confirmed = await errorHandler.confirm('确定要删除吗？');
if (confirmed) {
    // 执行删除操作
}
```

**Toast集成**:
- 自动检测全局的`showToast`函数
- 如果没有，使用`alert`作为降级方案

## 设计特点

### 1. 统一性
- 所有模块使用相同的调试和错误处理接口
- 一致的日志格式和错误提示风格

### 2. 可配置性
- 支持构造函数参数配置
- 运行时开关控制

### 3. 兼容性
- 自动降级处理（如Toast不存在时使用alert）
- 支持多种错误类型（Error对象、字符串等）

### 4. 易用性
- 简单直观的API设计
- 详细的错误消息映射

## 集成使用示例

### 完整使用示例
```javascript
import { Debug } from './utils/Debug.js';
import { ErrorHandler } from './utils/ErrorHandler.js';

class MyModule {
    constructor() {
        this.debug = new Debug('MyModule');
        this.errorHandler = new ErrorHandler();
    }
    
    async fetchData() {
        try {
            this.debug.log('开始获取数据...');
            
            const response = await fetch('/api/data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.debug.log('数据获取成功:', data);
            
            return data;
        } catch (error) {
            this.debug.error('获取数据失败:', error);
            this.errorHandler.handle(error, '数据加载失败，请重试');
            throw error;
        }
    }
}

// 使用示例
const myModule = new MyModule();
myModule.fetchData();
```

### 调试模式开启
```javascript
// 在浏览器控制台开启调试
localStorage.setItem('debug', 'true');

// 或者针对特定模块
localStorage.setItem('debug', 'MyModule');

// 刷新页面后生效
```

## 扩展建议

### 1. 添加新的工具类
如需添加新的工具类，建议：
- 放置在`utils/`目录下
- 遵循相同的命名和导出规范
- 使用`Debug`和`ErrorHandler`进行调试和错误处理

### 2. 自定义错误处理
可以扩展`ErrorHandler`类：
```javascript
class CustomErrorHandler extends ErrorHandler {
    handle(error, customMessage) {
        // 自定义处理逻辑
        super.handle(error, customMessage);
        // 额外的处理
    }
}
```

### 3. 调试增强
可以扩展`Debug`类：
```javascript
class EnhancedDebug extends Debug {
    group(label) {
        if (this.isEnabled) {
            console.group(`[${this.namespace}] ${label}`);
        }
    }
    
    groupEnd() {
        if (this.isEnabled) {
            console.groupEnd();
        }
    }
}
```