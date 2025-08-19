/**
 * ApiClient使用示例
 * 展示如何在项目中使用新的ApiClient类
 */

// 示例1: 基本使用
async function basicExample() {
    try {
        // 使用预定义的apiClient
        const data = await apiClient.get('/some-endpoint');
        console.log('获取数据成功:', data);
    } catch (error) {
        console.error('获取数据失败:', error);
    }
}

// 示例2: 创建自定义ApiClient
function createCustomClient() {
    const customApiClient = new ApiClient({
        baseURL: '/api/custom',
        timeout: 5000,
        maxRetries: 2,
        onError: (error) => {
            console.error('自定义错误处理:', error);
            // 可以在这里添加特定的错误处理逻辑
        }
    });
    
    return customApiClient;
}

// 示例3: 在模块中使用
class TaskService {
    constructor() {
        this.api = dispatchApiClient;
    }
    
    async getTasks(filters = {}) {
        return this.api.get('/tasks', filters);
    }
    
    async createTask(taskData) {
        return this.api.post('/tasks', taskData);
    }
    
    async updateTask(taskId, taskData) {
        return this.api.put(`/tasks/${taskId}`, taskData);
    }
    
    async deleteTask(taskId) {
        return this.api.delete(`/tasks/${taskId}`);
    }
}

// 示例4: 错误处理
async function errorHandlingExample() {
    try {
        const result = await apiClient.get('/non-existent-endpoint');
    } catch (error) {
        // ApiClient会自动处理错误，但也可以在这里进行额外处理
        if (error.status === 404) {
            console.log('资源未找到');
        } else if (error.status === 500) {
            console.log('服务器错误');
        }
    }
}

// 示例5: 批量请求
async function batchRequests() {
    try {
        const [tasks, companies, userInfo] = await Promise.all([
            dispatchApiClient.get('/tasks'),
            companyApiClient.get(''),
            dispatchApiClient.get('/user/info')
        ]);
        
        console.log('批量请求完成:', { tasks, companies, userInfo });
    } catch (error) {
        console.error('批量请求失败:', error);
    }
}

// 导出示例供测试使用
window.ApiClientExamples = {
    basicExample,
    createCustomClient,
    TaskService,
    errorHandlingExample,
    batchRequests
};