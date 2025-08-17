/**
 * 任务管理系统主入口
 * 统一导出所有模块和初始化函数
 */

import { TaskManager } from './TaskManager.js';
import { TaskRenderer } from './TaskRenderer.js';
import { Pagination } from './Pagination.js';
import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';

/**
 * 任务管理应用主类
 */
class TaskManagementApp {
    constructor(options = {}) {
        this.debug = new Debug('TaskManagementApp');
        this.errorHandler = new ErrorHandler();
        
        // 初始化各模块
        this.taskManager = new TaskManager(options.taskManager);
        this.taskRenderer = new TaskRenderer(options.taskRenderer);
        this.pagination = new Pagination(options.pagination);
        
        // 绑定模块间通信
        this.setupModuleCommunication();
        
        this.debug.log('TaskManagementApp initialized');
    }
    
    /**
     * 设置模块间通信
     */
    setupModuleCommunication() {
        // 任务数据加载完成
        this.taskManager.on('data-loaded', (data) => {
            this.taskRenderer.renderTasks(data.tasks);
            this.pagination.setData(data.total, this.taskManager.getState().currentPage);
            this.pagination.render();
        });
        
        // 分页变更
        this.pagination.onPageChange((page) => {
            this.taskManager.setPage(page);
        });
        
        // 错误处理
        this.taskManager.on('error', (error) => {
            this.errorHandler.handle(error);
        });
        
        // 加载状态
        this.taskManager.on('loading-start', () => {
            this.taskRenderer.showLoading(true);
        });
        
        this.taskManager.on('loading-end', () => {
            this.taskRenderer.showLoading(false);
        });
    }
    
    /**
     * 初始化应用
     */
    async init() {
        try {
            this.debug.log('Initializing Task Management App...');
            
            // 绑定UI事件
            this.bindUIEvents();
            
            // 加载统计信息
            await this.loadStatistics();
            
            // 加载初始数据
            await this.taskManager.loadTasks();
            
            this.debug.log('Task Management App initialized successfully');
        } catch (error) {
            this.errorHandler.handle(error, '初始化失败');
        }
    }

    /**
     * 加载统计信息
     */
    async loadStatistics() {
        try {
            this.taskRenderer.showDetailLoading();
            // 加载统计信息
            const statistics = await this.taskManager.getStatistics();
        
            if (statistics) {
                this.taskRenderer.renderStatistics(statistics);
            } else {
                this.taskRenderer.showDetailError('无法加载统计信息');
            }
        } catch (error) {
            console.error('加载统计信息失败:', error);
            this.taskRenderer.showDetailError('加载统计信息失败');
        }
    }
    
    /**
     * 绑定UI事件
     */
    bindUIEvents() {
        // 搜索按钮
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleSearch());
        }
        
        // 重置按钮
        const resetBtn = document.querySelector('.feishu-btn-secondary');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.handleReset());
        }
        
        // 详情按钮和任务行点击（事件委托）
        document.addEventListener('click', (e) => {
            // 检查是否点击了详情按钮
            if (e.target.classList.contains('view-detail') || e.target.closest('.view-detail')) {
                const btn = e.target.classList.contains('view-detail') ? e.target : e.target.closest('.view-detail');
                const taskId = btn.dataset.taskId;
                if (taskId) {
                    this.showTaskDetail(taskId);
                }
            }
            // 检查是否点击了任务行
            else if (e.target.classList.contains('task-row') || e.target.closest('.task-row')) {
                const row = e.target.classList.contains('task-row') ? e.target : e.target.closest('.task-row');
                const taskId = row.dataset.taskId;
                if (taskId) {
                    this.showTaskDetail(taskId);
                }
            }
        });
        
        // 筛选条件变化
        const filterInputs = document.querySelectorAll('.filter-group select, .filter-group input');
        filterInputs.forEach(input => {
            input.addEventListener('change', () => this.handleSearch());
        });
    }
    
    /**
     * 处理搜索
     */
    async handleSearch() {
        const filters = this.getFilters();
        await this.taskManager.searchTasks(filters);
    }
    
    /**
     * 处理重置
     */
    async handleReset() {
        const form = document.querySelector('.filter-form');
        if (form) form.reset();
        
        await this.taskManager.searchTasks({});
    }
    
    /**
     * 获取筛选条件
     */
    getFilters() {
        const filters = {};
        
        const fields = [
            'trackTypeFilter', 'statusFilter', 'startBureauFilter',
            'routeFilter', 'priorityFilter', 'carrierFilter'
        ];
        
        fields.forEach(field => {
            const element = document.getElementById(field);
            if (element && element.value) {
                const key = field.replace('Filter', '');
                filters[key] = element.value;
            }
        });
        
        return filters;
    }
    
    /**
     * 显示任务详情
     */
    async showTaskDetail(taskId) {
        try {
            // 显示加载状态
            this.taskRenderer.showDetailLoading();
            
            const task = await this.taskManager.getTaskDetail(taskId);
            if (task) {
                // 渲染任务详情
                this.taskRenderer.renderTaskDetail(task);
            } else {
                // 显示错误状态
                this.taskRenderer.showDetailError('未找到任务详情');
            }
        } catch (error) {
            // 显示错误状态
            this.taskRenderer.showDetailError('获取任务详情失败: ' + error.message);
            this.errorHandler.handle(error, '获取任务详情失败');
        }
    }
    
    /**
     * 跳转到指定页
     */
    goToPage(page) {
        this.pagination.goToPage(page);
    }
}

/**
 * 全局初始化函数
 */
export async function initTaskManagement(options = {}) {
    const app = new TaskManagementApp(options);
    await app.init();
    
    // 暴露到全局
    window.taskManagementApp = app;
    
    return app;
}

// 导出所有模块
export {
    TaskManager,
    TaskRenderer,
    Pagination,
    Debug,
    ErrorHandler,
    TaskManagementApp
};