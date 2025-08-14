/**
 * Dashboard AJAX功能增强
 * 使用新的AJAX工具库实现动态数据加载
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard AJAX模块已加载');
    
    // 初始化统计数据
    loadDashboardStats();
    
    // 初始化最新任务
    loadLatestTasks();
    
    // 初始化待处理申请
    loadPendingApplications();
    
    // 设置定时刷新（每30秒）
    setInterval(() => {
        loadDashboardStats();
    }, 30000);
});

/**
 * 加载仪表盘统计数据
 */
async function loadDashboardStats() {
    try {
        console.log('正在加载统计数据...');
        
        // 模拟API调用 - 实际使用时替换为真实API
        const stats = await $ajax.get('/api/dashboard/stats');
        
        updateStatCard('total-tasks', stats.total_tasks || 0);
        updateStatCard('pending-tasks', stats.pending_tasks || 0);
        updateStatCard('completed-tasks', stats.completed_tasks || 0);
        updateStatCard('total-revenue', `¥${(stats.total_revenue || 0).toLocaleString()}`);
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
        showToast('加载统计数据失败', 'error');
    }
}

/**
 * 加载最新任务
 */
async function loadLatestTasks() {
    try {
        const tasks = await $ajax.get('/api/tasks/latest', { limit: 5 });
        updateLatestTasksList(tasks);
    } catch (error) {
        console.error('加载最新任务失败:', error);
    }
}

/**
 * 加载待处理申请
 */
async function loadPendingApplications() {
    try {
        const applications = await $ajax.get('/api/applications/pending');
        updatePendingApplicationsList(applications);
    } catch (error) {
        console.error('加载待处理申请失败:', error);
    }
}

/**
 * 更新统计卡片数据
 * @param {string} cardId - 卡片ID
 * @param {string|number} value - 新值
 */
function updateStatCard(cardId, value) {
    const card = document.getElementById(cardId);
    if (card) {
        const valueElement = card.querySelector('.stat-value');
        if (valueElement) {
            // 添加动画效果
            valueElement.style.transform = 'scale(1.1)';
            setTimeout(() => {
                valueElement.textContent = value;
                valueElement.style.transform = 'scale(1)';
            }, 200);
        }
    }
}

/**
 * 更新最新任务列表
 * @param {Array} tasks - 任务数组
 */
function updateLatestTasksList(tasks) {
    const container = document.getElementById('latest-tasks-list');
    if (!container) return;

    if (tasks.length === 0) {
        container.innerHTML = '<p class="text-muted">暂无最新任务</p>';
        return;
    }

    const html = tasks.map(task => `
        <div class="task-item" data-task-id="${task.id}">
            <div class="task-header">
                <span class="task-title">${task.title}</span>
                <span class="task-status status-${task.status}">${getStatusText(task.status)}</span>
            </div>
            <div class="task-info">
                <span class="task-time">${formatDateTime(task.created_at)}</span>
                <span class="task-priority priority-${task.priority}">${getPriorityText(task.priority)}</span>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

/**
 * 更新待处理申请列表
 * @param {Array} applications - 申请数组
 */
function updatePendingApplicationsList(applications) {
    const container = document.getElementById('pending-applications-list');
    if (!container) return;

    if (applications.length === 0) {
        container.innerHTML = '<p class="text-muted">暂无待处理申请</p>';
        return;
    }

    const html = applications.map(app => `
        <div class="application-item" data-application-id="${app.id}">
            <div class="application-header">
                <span class="application-type">${getApplicationTypeText(app.type)}</span>
                <span class="application-time">${formatDateTime(app.created_at)}</span>
            </div>
            <div class="application-content">
                <span class="applicant">${app.applicant_name}</span>
                <div class="application-actions">
                    <button class="btn btn-sm btn-primary" onclick="handleApplicationAction(${app.id}, 'approve')">通过</button>
                    <button class="btn btn-sm btn-secondary" onclick="handleApplicationAction(${app.id}, 'reject')">拒绝</button>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

/**
 * 处理申请操作
 * @param {number} applicationId - 申请ID
 * @param {string} action - 操作类型
 */
async function handleApplicationAction(applicationId, action) {
    try {
        const button = event.target;
        $ajax.setLoading(button, true);

        await $ajax.put(`/api/applications/${applicationId}/action`, {
            action: action,
            reason: action === 'reject' ? '拒绝原因' : undefined
        });

        showToast(`${action === 'approve' ? '已通过' : '已拒绝'}申请`, 'success');
        
        // 重新加载待处理申请
        loadPendingApplications();
        
    } catch (error) {
        console.error('处理申请失败:', error);
        showToast('处理申请失败', 'error');
    } finally {
        if (event && event.target) {
            $ajax.setLoading(event.target, false);
        }
    }
}

/**
 * 快速创建任务
 */
async function quickCreateTask() {
    const title = prompt('请输入任务标题:');
    if (!title) return;

    try {
        await TaskAPI.createTask({
            title: title,
            description: '快速创建的任务',
            priority: 'medium',
            status: 'pending'
        });

        showToast('任务创建成功', 'success');
        loadLatestTasks(); // 刷新任务列表
        loadDashboardStats(); // 刷新统计数据
        
    } catch (error) {
        console.error('创建任务失败:', error);
        showToast('创建任务失败', 'error');
    }
}

/**
 * 工具函数：获取状态文本
 */
function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
}

/**
 * 工具函数：获取优先级文本
 */
function getPriorityText(priority) {
    const priorityMap = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'urgent': '紧急'
    };
    return priorityMap[priority] || priority;
}

/**
 * 工具函数：获取申请类型文本
 */
function getApplicationTypeText(type) {
    const typeMap = {
        'leave': '请假申请',
        'overtime': '加班申请',
        'expense': '费用申请',
        'vehicle': '用车申请'
    };
    return typeMap[type] || type;
}

/**
 * 工具函数：格式化日期时间
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    
    return date.toLocaleDateString('zh-CN');
}

/**
 * 实时搜索功能
 */
function setupRealTimeSearch() {
    const searchInput = document.getElementById('global-search');
    if (!searchInput) return;

    let searchTimeout;
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) return;
        
        searchTimeout = setTimeout(async () => {
            try {
                const results = await $ajax.get('/api/search', { q: query, limit: 10 });
                displaySearchResults(results);
            } catch (error) {
                console.error('搜索失败:', error);
            }
        }, 300);
    });
}

/**
 * 显示搜索结果
 */
function displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!container) return;

    if (results.length === 0) {
        container.innerHTML = '<div class="search-no-results">未找到相关结果</div>';
        return;
    }

    const html = results.map(item => `
        <div class="search-result-item" onclick="navigateToResult('${item.type}', ${item.id})">
            <div class="result-type">${item.type}</div>
            <div class="result-title">${item.title}</div>
            <div class="result-description">${item.description}</div>
        </div>
    `).join('');

    container.innerHTML = html;
}

/**
 * 导航到搜索结果
 */
function navigateToResult(type, id) {
    const routes = {
        'task': `/tasks/${id}`,
        'user': `/users/${id}`,
        'vehicle': `/vehicles/${id}`
    };

    const route = routes[type];
    if (route) {
        window.location.href = route;
    }
}

// 页面加载完成后初始化
window.addEventListener('load', function() {
    setupRealTimeSearch();
    
    // 添加快速创建任务按钮事件
    const quickCreateBtn = document.getElementById('quick-create-task');
    if (quickCreateBtn) {
        quickCreateBtn.addEventListener('click', quickCreateTask);
    }
});

// 导出供其他模块使用
window.DashboardAJAX = {
    loadDashboardStats,
    loadLatestTasks,
    loadPendingApplications,
    quickCreateTask
};