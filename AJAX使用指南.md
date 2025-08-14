# 🚀 AJAX功能使用指南（新手版）

## 📱 一句话理解
**AJAX = 不用刷新页面就能和服务器聊天**

就像微信发消息一样，点击发送 → 对方收到 → 回复你，整个过程页面不会刷新。

---

## 🎯 三步使用法

### 第1步：引入AJAX工具（已帮你做好）
```html
<!-- 这两个文件已经帮你准备好了 -->
<script src="/static/ajax-utils.js"></script>
<script src="/static/dashboard-ajax.js"></script>
```

### 第2步：调用现成的API方法

#### 📊 获取数据（查）
```javascript
// 获取任务列表
const tasks = await TaskAPI.getTasks();

// 获取统计数据
const stats = await AjaxUtils.get('/api/dashboard/stats');
```

#### ➕ 添加数据（增）
```javascript
// 创建新任务（这就是你问的那个方法！）
await TaskAPI.createTask({
    title: "配送任务",
    description: "从合肥送货到南京",
    priority: "high"
});
```

#### ✏️ 修改数据（改）
```javascript
// 更新任务状态
await TaskAPI.updateTaskStatus(123, "completed");
```

#### 🗑️ 删除数据（删）
```javascript
// 删除任务
await TaskAPI.deleteTask(123);
```

### 第3步：处理结果
```javascript
// 成功/失败处理
try {
    await TaskAPI.createTask(taskData);
    alert("✅ 创建成功！");
} catch (error) {
    alert("❌ 创建失败：" + error.message);
}
```

---

## 📋 常用API清单

| 你想做什么 | 代码怎么写 | 对应后端地址 |
|-----------|------------|-------------|
| 查看所有任务 | `TaskAPI.getTasks()` | GET `/api/tasks` |
| 创建新任务 | `TaskAPI.createTask(data)` | POST `/api/tasks` |
| 修改任务状态 | `TaskAPI.updateTaskStatus(id, status)` | PUT `/api/tasks/:id/status` |
| 删除任务 | `TaskAPI.deleteTask(id)` | DELETE `/api/tasks/:id` |
| 获取统计数据 | `AjaxUtils.get('/api/dashboard/stats')` | GET `/api/dashboard/stats` |

---

## 🎮 实际案例演示

### 案例1：点击按钮创建任务
```html
<button onclick="addTask()">创建任务</button>

<script>
async function addTask() {
    const taskName = prompt("请输入任务名称：");
    if (!taskName) return;
    
    try {
        await TaskAPI.createTask({
            title: taskName,
            description: "用户创建的任务",
            priority: "medium"
        });
        alert("任务创建成功！");
        location.reload(); // 刷新页面看效果
    } catch (error) {
        alert("创建失败：" + error.message);
    }
}
</script>
```

### 案例2：实时显示统计数据
```javascript
// 页面加载时自动获取数据
window.onload = async function() {
    try {
        const stats = await AjaxUtils.get('/api/dashboard/stats');
        document.getElementById('task-count').textContent = stats.total_tasks;
    } catch (error) {
        console.error("获取数据失败", error);
    }
};
```

---

## 🔧 调试技巧

### 方法1：看浏览器的Network
1. 按F12打开开发者工具
2. 点击Network（网络）标签
3. 执行AJAX操作
4. 查看请求和响应

### 方法2：使用测试页面
访问：`http://127.0.0.1:5000/dashboard`
- 可以看到实时数据加载
- 点击刷新按钮测试AJAX

---

## ❓常见问题解答

**Q: 为什么我的AJAX请求失败了？**
A: 检查这几点：
- ✅ 服务器是否运行（python app.py）
- ✅ 是否登录系统（需要权限）
- ✅ 网络连接是否正常
- ✅ 请求地址是否正确

**Q: 数据格式是什么样的？**
A: 统一的JSON格式：
```json
{
    "title": "任务名称",
    "description": "任务描述",
    "priority": "high/medium/low"
}
```

**Q: 怎么知道请求成功了？**
A: 看返回值：
- ✅ 成功：返回 `{message: "成功信息"}`
- ❌ 失败：返回 `{error: "错误信息"}`

---

## 🚀 5分钟上手练习

1. **打开浏览器** → 访问 `http://127.0.0.1:5000/dashboard`
2. **打开控制台** → 按F12，切换到Console
3. **输入测试代码**：
   ```javascript
   // 测试获取统计数据
   AjaxUtils.get('/api/dashboard/stats').then(console.log);
   ```
4. **看结果** → 应该能看到返回的JSON数据

---

## 🎨 一句话总结

**记住这个公式：**
```
前端调用 → AJAX方法 → 后端接口 → 数据库 → 返回结果
```

就像点外卖：你下单 → 平台接单 → 商家制作 → 骑手配送 → 你收到餐，全程无需刷新页面！

---

## 📞 技术支持
- 遇到问题先看控制台报错
- 检查网络请求的返回信息
- 确保所有文件都在正确位置
- 重启服务器试试 `python app.py`