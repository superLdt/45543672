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
            
            // 获取当前用户信息
            await this.loadCurrentUserInfo();
            
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
     * 加载当前用户信息
     */
    async loadCurrentUserInfo() {
        try {
            const userInfo = await this.taskManager.getCurrentUserInfo();
            if (userInfo) {
                // 将用户信息存储在全局变量中
                window.currentUserInfo = userInfo;
                this.debug.log('Current user info loaded:', userInfo);
            }
        } catch (error) {
            this.errorHandler.handle(error, '加载用户信息失败');
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
     * 确认审批
     */
    async confirmApproval(taskId) {
        try {
            const confirmed = await this.showApprovalDialog('确认审批', '确定要通过此任务的审批吗？');
            if (!confirmed) return;

            const response = await fetch(`/api/dispatch/tasks/${taskId}/audit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audit_result: '通过',
                    audit_note: '审批通过'
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccessMessage('审批通过成功');
                // 重新加载任务列表和详情
                await this.taskManager.loadTasks();
                await this.showTaskDetail(taskId);
            } else {
                this.showErrorMessage(result.error?.message || '审批失败');
            }
        } catch (error) {
            this.showErrorMessage('审批请求失败: ' + error.message);
            this.errorHandler.handle(error, '确认审批失败');
        }
    }
    
    /**
     * 拒绝审批
     */
    async rejectApproval(taskId) {
        try {
            const note = await this.showRejectDialog();
            if (!note) return;

            const response = await fetch(`/api/dispatch/tasks/${taskId}/audit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    audit_result: '拒绝',
                    audit_note: note
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccessMessage('审批拒绝成功');
                // 重新加载任务列表和详情
                await this.taskManager.loadTasks();
                await this.showTaskDetail(taskId);
            } else {
                this.showErrorMessage(result.error?.message || '拒绝审批失败');
            }
        } catch (error) {
            this.showErrorMessage('拒绝审批请求失败: ' + error.message);
            this.errorHandler.handle(error, '拒绝审批失败');
        }
    }

    /**
     * 显示审批确认对话框
     */
    async showApprovalDialog(title, message) {
        return new Promise((resolve) => {
            const confirmed = confirm(`${title}\n\n${message}`);
            resolve(confirmed);
        });
    }

    /**
     * 显示拒绝对话框
     */
    async showRejectDialog() {
        return new Promise((resolve) => {
            const note = prompt('请输入拒绝原因：');
            if (note && note.trim()) {
                resolve(note.trim());
            } else if (note === '') {
                alert('拒绝原因不能为空');
                resolve(null);
            } else {
                resolve(null);
            }
        });
    }

    /**
     * 显示成功消息
     */
    showSuccessMessage(message) {
        alert(message); // 可以替换为更好的通知组件
    }

    /**
     * 显示错误消息
     */
    showErrorMessage(message) {
        alert(message); // 可以替换为更好的通知组件
    }
    
    /**
     * 车间发车
     */
    workshopDeparture(taskId) {
        // TODO: 实现车间发车逻辑
        console.log('Workshop departure for task:', taskId);
        alert('车间发车功能待实现');
    }
    
    /**
     * 最终确认
     */
    finalConfirmation(taskId) {
        // TODO: 实现最终确认逻辑
        console.log('Final confirmation for task:', taskId);
        alert('最终确认功能待实现');
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
    
    // 创建全局taskManagement对象，暴露常用方法
    window.taskManagement = {
        closeDetail: () => app.taskRenderer.closeDetail(),
        confirmResponse: (taskId) => app.taskManager.updateTaskStatus(taskId, '供应商已响应'),
        addRemark: (taskId) => {
            const remark = prompt('请输入备注:');
            if (remark) {
                // TODO: 实现添加备注逻辑
                alert('备注功能待实现');
            }
        },
        requestPause: (taskId) => {
            if (confirm('确定要申请暂停此任务吗？')) {
                // TODO: 实现申请暂停逻辑
                alert('申请暂停功能待实现');
            }
        },
        confirmApproval: (taskId) => app.confirmApproval(taskId),
        rejectApproval: (taskId) => app.rejectApproval(taskId),
        workshopDeparture: (taskId) => app.workshopDeparture(taskId),
        finalConfirmation: (taskId) => app.finalConfirmation(taskId),
        showTaskDetail: (taskId) => app.showTaskDetail(taskId),
        showSupplierConfirmDialog: (taskId) => app.taskManager.showSupplierConfirmDialog(taskId),
        showApprovalDialog: (taskId, action) => app.taskManager.showApprovalDialog(taskId, action),
        submitSupplierConfirm: (taskId) => app.taskManager.submitSupplierConfirm(taskId),
        submitApproval: (taskId, action) => app.taskManager.submitApproval(taskId, action)
    };
    
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