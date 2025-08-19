/**
 * 统一API客户端类
 * 提供统一的HTTP请求接口，支持错误处理、超时控制、重试机制
 * 遵循单一职责原则，专门处理API通信
 */
class ApiClient {
    /**
     * 创建ApiClient实例
     * @param {Object} options - 配置选项
     * @param {string} options.baseURL - 基础URL
     * @param {Object} options.defaultHeaders - 默认请求头
     * @param {number} options.timeout - 超时时间(毫秒)
     * @param {number} options.maxRetries - 最大重试次数
     * @param {Function} options.onError - 全局错误处理函数
     */
    constructor(options = {}) {
        this.baseURL = options.baseURL || '';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            ...options.defaultHeaders
        };
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 3;
        this.onError = options.onError || this._defaultErrorHandler;
        
        // 绑定方法
        this.request = this.request.bind(this);
        this.get = this.get.bind(this);
        this.post = this.post.bind(this);
        this.put = this.put.bind(this);
        this.delete = this.delete.bind(this);
    }

    /**
     * 统一请求方法
     * @param {string} endpoint - API端点
     * @param {Object} options - 请求配置
     * @param {string} options.method - HTTP方法
     * @param {Object} options.headers - 额外请求头
     * @param {Object} options.body - 请求体
     * @param {Object} options.params - URL参数
     * @returns {Promise} 返回Promise
     */
    async request(endpoint, options = {}) {
        const url = this._buildURL(endpoint, options.params);
        const config = this._buildConfig(options);
        
        Debug.log('ApiClient', `开始请求: ${options.method || 'GET'} ${url}`);
        
        let lastError;
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await this._fetchWithTimeout(url, config);
                const data = await this._parseResponse(response);
                
                Debug.log('ApiClient', `请求成功: ${options.method || 'GET'} ${url}`);
                return data;
                
            } catch (error) {
                lastError = error;
                Debug.error('ApiClient', `请求失败 (尝试 ${attempt}/${this.maxRetries}):`, error);
                
                // 不重试客户端错误
                if (error.status >= 400 && error.status < 500) {
                    break;
                }
                
                // 最后一次尝试不等待
                if (attempt < this.maxRetries) {
                    await this._delay(1000 * attempt);
                }
            }
        }
        
        this.onError(lastError);
        throw lastError;
    }

    /**
     * GET请求
     * @param {string} endpoint - API端点
     * @param {Object} params - URL参数
     * @param {Object} headers - 额外请求头
     * @returns {Promise}
     */
    async get(endpoint, params = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'GET',
            params,
            headers
        });
    }

    /**
     * POST请求
     * @param {string} endpoint - API端点
     * @param {Object} data - 请求数据
     * @param {Object} headers - 额外请求头
     * @returns {Promise}
     */
    async post(endpoint, data = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: data,
            headers
        });
    }

    /**
     * PUT请求
     * @param {string} endpoint - API端点
     * @param {Object} data - 请求数据
     * @param {Object} headers - 额外请求头
     * @returns {Promise}
     */
    async put(endpoint, data = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: data,
            headers
        });
    }

    /**
     * DELETE请求
     * @param {string} endpoint - API端点
     * @param {Object} params - URL参数
     * @param {Object} headers - 额外请求头
     * @returns {Promise}
     */
    async delete(endpoint, params = {}, headers = {}) {
        return this.request(endpoint, {
            method: 'DELETE',
            params,
            headers
        });
    }

    /**
     * 构建完整URL
     * @private
     */
    _buildURL(endpoint, params = {}) {
        const url = this.baseURL + endpoint;
        if (!params || Object.keys(params).length === 0) {
            return url;
        }
        
        const searchParams = new URLSearchParams();
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                searchParams.append(key, params[key]);
            }
        });
        
        return `${url}?${searchParams.toString()}`;
    }

    /**
     * 构建请求配置
     * @private
     */
    _buildConfig(options = {}) {
        return {
            method: options.method || 'GET',
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined
        };
    }

    /**
     * 带超时的fetch
     * @private
     */
    async _fetchWithTimeout(url, config) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('请求超时');
            }
            throw error;
        }
    }

    /**
     * 解析响应
     * @private
     */
    async _parseResponse(response) {
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            error.response = response;
            
            try {
                error.data = await response.json();
            } catch {
                error.data = await response.text();
            }
            
            throw error;
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    }

    /**
     * 默认错误处理
     * @private
     */
    _defaultErrorHandler(error) {
        ErrorHandler.handle(error);
    }

    /**
     * 延迟函数
     * @private
     */
    async _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * 预定义的API客户端实例
 */

// 调度模块API客户端
const dispatchApiClient = new ApiClient({
    baseURL: '/api/dispatch',
    onError: (error) => {
        Debug.error('DispatchApi', '调度API错误:', error);
        ErrorHandler.handle(error, {
            title: '调度操作失败',
            fallbackMessage: '调度操作失败，请稍后重试'
        });
    }
});

// 公司管理API客户端
const companyApiClient = new ApiClient({
    baseURL: '/api/company',
    onError: (error) => {
        Debug.error('CompanyApi', '公司API错误:', error);
        ErrorHandler.handle(error, {
            title: '公司数据获取失败',
            fallbackMessage: '无法获取公司信息，请稍后重试'
        });
    }
});

// 通用API客户端
const apiClient = new ApiClient({
    baseURL: '/api',
    onError: (error) => {
        Debug.error('ApiClient', 'API错误:', error);
        ErrorHandler.handle(error);
    }
});

// 导出供全局使用
window.ApiClient = ApiClient;
window.apiClient = apiClient;
window.dispatchApiClient = dispatchApiClient;
window.companyApiClient = companyApiClient;