/**
 * TaskManager - 任务管理核心模块
 * 提供任务数据的加载、搜索、分页等核心功能
 */

import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';

export class TaskManager {
    constructor(options = {}) {
        this.debug = new Debug('TaskManager');
        this.errorHandler = new ErrorHandler();
        
        // 配置选项
        this.options = {
            apiEndpoint: '/api/dispatch/tasks',
            pageSize: 10,
            ...options
        };
        
        // 状态管理
        this.state = {
            tasks: [],
            totalTasks: 0,
            currentPage: 1,
            isLoading: false,
            filters: {},
            sortBy: 'created_at',
            sortOrder: 'desc'
        };
        
        // 事件监听
        this.listeners = new Map();
        
        this.debug.log('TaskManager initialized', this.options);
    }
    
    /**
     * 添加事件监听
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    /**
     * 触发事件
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => callback(data));
        }
    }
    
    /**
     * 加载任务列表
     */
    async loadTasks(filters = {}) {
        try {
            this.state.isLoading = true;
            this.emit('loading-start');
            
            const params = new URLSearchParams({
                page: this.state.currentPage,
                limit: this.options.pageSize,
                ...filters
            });
            
            this.debug.log('Loading tasks with params:', params.toString());
            
            const response = await fetch(`${this.options.apiEndpoint}?${params}`, {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                this.state.tasks = result.data || [];
                this.state.totalTasks = result.total || 0;
                this.emit('data-loaded', {
                    tasks: this.state.tasks,
                    total: this.state.totalTasks
                });
            } else {
                throw new Error(result.error?.message || '加载任务失败');
            }
            
        } catch (error) {
            this.debug.error('Failed to load tasks:', error);
            this.errorHandler.handle(error);
            this.emit('error', error);
        } finally {
            this.state.isLoading = false;
            this.emit('loading-end');
        }
    }
    
    /**
     * 搜索任务
     */
    async searchTasks(searchParams) {
        this.state.currentPage = 1; // 重置到第一页
        this.state.filters = searchParams;
        await this.loadTasks(searchParams);
    }
    
    /**
     * 获取任务详情
     */
    async getTaskDetail(taskId) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}/${taskId}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            return result.success ? result.data : null;
            
        } catch (error) {
            this.debug.error('Failed to get task detail:', error);
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 更新任务状态
     */
    async updateTaskStatus(taskId, status, data = {}) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ status, ...data })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                // 更新本地数据
                const taskIndex = this.state.tasks.findIndex(t => t.id === taskId);
                if (taskIndex !== -1) {
                    this.state.tasks[taskIndex].status = status;
                    this.emit('task-updated', this.state.tasks[taskIndex]);
                }
            }
            
            return result.success;
            
        } catch (error) {
            this.debug.error('Failed to update task status:', error);
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 设置当前页码
     */
    setPage(page) {
        this.state.currentPage = Math.max(1, page);
        this.loadTasks(this.state.filters);
    }
    
    /**
     * 获取当前状态
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * 获取分页信息
     */
    getPaginationInfo() {
        const totalPages = Math.ceil(this.state.totalTasks / this.options.pageSize);
        return {
            currentPage: this.state.currentPage,
            totalPages,
            totalTasks: this.state.totalTasks,
            pageSize: this.options.pageSize,
            hasPrev: this.state.currentPage > 1,
            hasNext: this.state.currentPage < totalPages
        };
    }
}