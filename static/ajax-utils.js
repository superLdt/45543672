/**
 * AJAX工具库 - 智能运力系统前端增强
 * 提供统一的API调用接口和错误处理
 */

class AjaxUtils {
    constructor() {
        this.baseURL = '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
    }

    /**
     * GET请求
     * @param {string} url - 请求URL
     * @param {Object} params - URL参数
     * @param {Object} options - 额外选项
     * @returns {Promise} - 返回Promise对象
     */
    async get(url, params = {}, options = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        return this.request(fullUrl, {
            method: 'GET',
            ...options
        });
    }

    /**
     * POST请求
     * @param {string} url - 请求URL
     * @param {Object} data - 请求数据
     * @param {Object} options - 额外选项
     * @returns {Promise} - 返回Promise对象
     */
    async post(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * PUT请求
     * @param {string} url - 请求URL
     * @param {Object} data - 请求数据
     * @param {Object} options - 额外选项
     * @returns {Promise} - 返回Promise对象
     */
    async put(url, data = {}, options = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data),
            ...options
        });
    }

    /**
     * DELETE请求
     * @param {string} url - 请求URL
     * @param {Object} options - 额外选项
     * @returns {Promise} - 返回Promise对象
     */
    async delete(url, options = {}) {
        return this.request(url, {
            method: 'DELETE',
            ...options
        });
    }

    /**
     * 通用请求方法
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise} - 返回Promise对象
     */
    async request(url, options = {}) {
        const config = {
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('AJAX请求错误:', error);
            this.handleError(error);
            throw error;
        }
    }

    /**
     * 错误处理
     * @param {Error} error - 错误对象
     */
    handleError(error) {
        console.error('AJAX错误详情:', error.message);
        
        // 显示用户友好的错误提示
        if (typeof showToast === 'function') {
            showToast(error.message || '网络请求失败', 'error');
        }
    }

    /**
     * 显示加载状态
     * @param {HTMLElement} element - 要显示加载状态的元素
     * @param {boolean} loading - 是否显示加载状态
     */
    setLoading(element, loading = true) {
        if (loading) {
            element.classList.add('loading');
            element.disabled = true;
        } else {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }

    /**
     * 表单序列化
     * @param {HTMLFormElement} form - 表单元素
     * @returns {Object} - 序列化后的数据对象
     */
    serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }
}

// 创建全局AJAX实例
const $ajax = new AjaxUtils();

/**
 * 快捷方法 - 任务相关API
 */
class TaskAPI {
    static async getTasks(params = {}) {
        return $ajax.get('/api/tasks', params);
    }

    static async createTask(taskData) {
        return $ajax.post('/api/tasks', taskData);
    }

    static async updateTask(taskId, taskData) {
        return $ajax.put(`/api/tasks/${taskId}`, taskData);
    }

    static async deleteTask(taskId) {
        return $ajax.delete(`/api/tasks/${taskId}`);
    }

    static async updateTaskStatus(taskId, status) {
        return $ajax.put(`/api/tasks/${taskId}/status`, { status });
    }
}

/**
 * 快捷方法 - 用户相关API
 */
class UserAPI {
    static async getUserInfo() {
        return $ajax.get('/api/user/info');
    }

    static async updateProfile(userData) {
        return $ajax.put('/api/user/profile', userData);
    }
}

/**
 * 工具函数 - 显示提示消息
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // 添加样式
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;

    // 根据类型设置背景色
    const colors = {
        success: '#52c41a',
        error: '#ff4d4f',
        warning: '#faad14',
        info: '#1890ff'
    };
    toast.style.backgroundColor = colors[type] || colors.info;

    document.body.appendChild(toast);
    
    // 显示动画
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 100);

    // 自动消失
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// 使用示例
/*
// 获取任务列表
TaskAPI.getTasks({ status: 'pending' })
    .then(tasks => console.log('任务列表:', tasks))
    .catch(error => console.error('获取失败:', error));

// 创建新任务
TaskAPI.createTask({
    title: '新任务',
    description: '任务描述',
    priority: 'high'
}).then(response => {
    showToast('任务创建成功', 'success');
});

// 更新任务状态
TaskAPI.updateTaskStatus(123, 'completed')
    .then(() => {
        showToast('状态更新成功', 'success');
    });
*/