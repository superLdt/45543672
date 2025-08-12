# 飞书风格样式库使用指南

## 概述

本样式库提供了统一的飞书(飞书)风格UI组件，适用于安徽XX智能运力系统。所有组件都遵循飞书设计语言，确保界面的一致性和专业性。

## 快速开始

### 1. 引入样式文件

#### 方法1：在Flask模板中使用
```html
<!-- 引入飞书风格样式库 -->
<link rel="stylesheet" href="{{ url_for('static', filename='feishu-styles.css') }}">

<!-- 建议同时引入Font Awesome图标库 -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

#### 方法2：在静态HTML中使用
```html
<!-- 引入飞书风格样式库 -->
<link rel="stylesheet" href="./feishu-styles.css">

<!-- 建议同时引入Font Awesome图标库 -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

#### 方法3：在现有页面中替换内嵌样式
1. 移除原有的内嵌CSS样式
2. 添加外部样式文件引用
3. 保留页面特定的样式（如有需要）

```html
<!-- 原来的内嵌样式 -->
{% block extra_css %}
<!-- 移除原有的内嵌CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='feishu-styles.css') }}">
<style>
    /* 仅保留页面特定的样式 */
    .page-specific-style {
        /* 你的特定样式 */
    }
</style>
{% endblock %}
```

### 2. 使用基础变量

可以直接使用CSS变量：

```css
.my-custom-element {
    color: var(--feishu-text-primary);
    background: var(--feishu-white);
    border-radius: var(--feishu-radius);
}
```

## 组件列表

### 卡片组件

#### 基础卡片
```html
<div class="feishu-card">
    <h3>卡片标题</h3>
    <p>卡片内容</p>
</div>
```

#### 带标题的卡片
```html
<div class="feishu-card">
    <div class="filter-header">
        <h5><i class="fas fa-filter"></i> 筛选条件</h5>
    </div>
    <div class="filter-body">
        <!-- 内容 -->
    </div>
</div>
```

### 按钮组件

#### 主要按钮
```html
<button class="feishu-btn feishu-btn-primary">主要按钮</button>
```

#### 次要按钮
```html
<button class="feishu-btn feishu-btn-secondary">次要按钮</button>
```

#### 不同尺寸
```html
<button class="feishu-btn feishu-btn-sm">小按钮</button>
<button class="feishu-btn">标准按钮</button>
<button class="feishu-btn feishu-btn-lg">大按钮</button>
```

### 表单组件

#### 输入框
```html
<input type="text" class="feishu-input" placeholder="请输入内容">
```

#### 选择框
```html
<select class="feishu-select">
    <option>选项1</option>
    <option>选项2</option>
</select>
```

#### 文本域
```html
<textarea class="feishu-textarea" rows="3" placeholder="请输入内容"></textarea>
```

### 表格组件

#### 基础表格
```html
<table class="feishu-table">
    <thead>
        <tr>
            <th>列1</th>
            <th>列2</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>数据1</td>
            <td>数据2</td>
        </tr>
    </tbody>
</table>
```

#### 高亮行
```html
<tr class="active">...</tr>
```

### 状态标签

#### 待处理
```html
<span class="feishu-badge feishu-badge-pending">
    <i class="fas fa-clock"></i> 待处理
</span>
```

#### 进行中
```html
<span class="feishu-badge feishu-badge-processing">
    <i class="fas fa-spinner"></i> 进行中
</span>
```

#### 已完成
```html
<span class="feishu-badge feishu-badge-completed">
    <i class="fas fa-check"></i> 已完成
</span>
```

#### 错误
```html
<span class="feishu-badge feishu-badge-error">
    <i class="fas fa-exclamation-triangle"></i> 错误
</span>
```

### 布局系统

#### 容器
```html
<div class="feishu-container">
    <div class="feishu-main-content">
        <!-- 主要内容 -->
    </div>
</div>
```

#### 网格系统
```html
<div class="feishu-row">
    <div class="feishu-col feishu-col-4">占1/3宽度</div>
    <div class="feishu-col feishu-col-8">占2/3宽度</div>
</div>
```

#### 响应式网格
```html
<div class="feishu-row">
    <div class="feishu-col feishu-col-lg-4 feishu-col-md-6 feishu-col-sm-12">
        响应式列
    </div>
</div>
```

## 页面标题

#### 标准页面标题
```html
<div class="page-header">
    <h1 class="page-title">页面标题</h1>
    <p class="page-subtitle">页面描述</p>
</div>
```

## 实用工具类

### 间距
```html
<!-- 外边距 -->
<div class="mb-3">底部间距</div>
<div class="mt-3">顶部间距</div>

<!-- 内边距 -->
<div class="p-3">内边距</div>
```

### 文本对齐
```html
<div class="text-center">居中文本</div>
<div class="text-left">左对齐文本</div>
<div class="text-right">右对齐文本</div>
```

### 宽度高度
```html
<div class="w-100">100%宽度</div>
<div class="h-100">100%高度</div>
```

## 响应式设计

样式库支持以下响应式断点：
- **移动设备**：`max-width: 768px`
- **平板设备**：`max-width: 992px`
- **桌面设备**：`max-width: 1200px`

## 示例页面

### 完整示例

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='feishu-styles.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="feishu-container">
        <div class="page-header">
            <h1 class="page-title">任务管理</h1>
            <p class="page-subtitle">查看和管理所有运输任务</p>
        </div>
        
        <div class="feishu-card">
            <div class="filter-header">
                <h5><i class="fas fa-filter"></i> 筛选条件</h5>
                <button class="feishu-btn feishu-btn-secondary feishu-btn-sm">
                    <i class="fas fa-search"></i> 查询
                </button>
            </div>
            
            <div class="filter-body">
                <div class="feishu-row">
                    <div class="feishu-col feishu-col-4">
                        <label class="filter-label">状态</label>
                        <select class="feishu-select">
                            <option>全部</option>
                            <option>待处理</option>
                            <option>已完成</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="feishu-card">
            <table class="feishu-table">
                <thead>
                    <tr>
                        <th>任务编号</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>TASK001</td>
                        <td>
                            <span class="feishu-badge feishu-badge-processing">
                                <i class="fas fa-spinner"></i> 进行中
                            </span>
                        </td>
                        <td>
                            <button class="feishu-btn feishu-btn-primary feishu-btn-sm">
                                <i class="fas fa-edit"></i> 编辑
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
```

## 最佳实践

1. **保持一致性**：在整个应用中使用相同的组件
2. **合理使用图标**：配合Font Awesome图标库使用
3. **响应式设计**：使用网格系统确保移动端适配
4. **颜色搭配**：遵循飞书色彩体系，不要随意更改主色调
5. **间距规范**：使用预定义的间距变量

## 更新日志

- v1.0.0：初始版本，包含基础组件和布局系统
- 基于task_management页面样式提取优化