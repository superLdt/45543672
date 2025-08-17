/**
 * ManualDispatch - 人工派车页面逻辑
 * 使用ES6模块重构，不再依赖ajax-utils.js
 */

import { TaskManager } from './TaskManager.js';
import { TaskRenderer } from './TaskRenderer.js';
import { Pagination } from './Pagination.js';
import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';

class ManualDispatchApp {
    constructor() {
        this.debug = new Debug('ManualDispatch');
        this.errorHandler = new ErrorHandler();
        
        // 初始化模块
        this.taskManager = new TaskManager({
            apiEndpoint: '/api/dispatch-tasks'
        });
        
        this.taskRenderer = new TaskRenderer({
            tableId: 'dispatchTaskList'
        });
        
        this.pagination = new Pagination({
            containerId: 'paginationContainer',
            pageSize: 10
        });
        
        // 绑定事件
        this.bindEvents();
        
        // 初始化页面
        this.init();
    }
    
    /**
     * 初始化页面
     */
    async init() {
        try {
            // 检查登录状态
            await this.checkLoginStatus();
            
            // 加载派车任务
            await this.loadDispatchTasks();
            
            this.debug.log('Manual dispatch app initialized');
        } catch (error) {
            this.errorHandler.handle(error, '初始化失败');
        }
    }
    
    /**
     * 检查登录状态
     */
    async checkLoginStatus() {
        try {
            const response = await fetch('/api/check-login', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('登录状态检查失败');
            }
            
            const result = await response.json();
            if (!result.loggedIn) {
                window.location.href = '/login';
            }
        } catch (error) {
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 加载派车任务
     */
    async loadDispatchTasks(page = 1) {
        try {
            // 显示加载状态
            this.taskRenderer.showLoading(true);
            
            // 加载任务数据
            const data = await this.taskManager.loadTasks({ page });
            
            // 渲染任务列表
            this.taskRenderer.renderTasks(data.tasks);
            
            // 更新分页信息
            this.pagination.setData(data.total, page);
            this.pagination.render();
            
            this.debug.log(`Loaded ${data.tasks.length} dispatch tasks`);
        } catch (error) {
            this.errorHandler.handle(error, '加载派车任务失败');
            this.taskRenderer.showEmptyState('加载派车任务失败');
        } finally {
            this.taskRenderer.showLoading(false);
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 绑定分页事件
        this.pagination.onPageChange(async (page) => {
            await this.loadDispatchTasks(page);
        });
        
        // 绑定表单提交事件
        const form = document.getElementById('dispatchForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        // 绑定重量与容积映射关系处理
        const weightInput = document.getElementById('weight');
        const volumeInput = document.getElementById('volume');
        
        if (weightInput && volumeInput) {
            // 定义重量与容积的映射关系
            const weightToVolumeMap = {
                '5': { min: 35, next: 45 },
                '8': { min: 45, next: 55 },
                '12': { min: 55, next: 100 },
                '20': { min: 100, next: 130 },
                '30': { min: 130, next: 150 },
                '40A': { min: 150, next: 180 },
                '40B': { min: 180, next: null }
            };
            
            weightInput.addEventListener('change', () => {
                const weight = weightInput.value;
                const volumeInfo = weightToVolumeMap[weight];
                
                if (volumeInfo) {
                    // 设置容积输入框的最小值和默认值
                    volumeInput.min = volumeInfo.min;
                    volumeInput.value = volumeInfo.min;
                    volumeInput.placeholder = `最小容积 ${volumeInfo.min} 立方米`;
                    volumeInput.disabled = false;
                } else {
                    volumeInput.min = 0;
                    volumeInput.placeholder = '请选择重量后输入容积';
                    volumeInput.disabled = true;
                    volumeInput.value = '';
                }
            });
        }
    }
    
    /**
     * 处理表单提交
     */
    async handleFormSubmit(e) {
        e.preventDefault();
        
        try {
            const form = e.target;
            const formData = new FormData(form);
            const taskData = Object.fromEntries(formData.entries());
            
            // 容积验证
            const weight = taskData.weight;
            const volume = parseInt(taskData.volume);
            
            // 获取重量与容积映射关系
            const weightToVolumeMap = {
                '5': { min: 35, next: 45 },
                '8': { min: 45, next: 55 },
                '12': { min: 55, next: 100 },
                '20': { min: 100, next: 130 },
                '30': { min: 130, next: 150 },
                '40A': { min: 150, next: 180 },
                '40B': { min: 180, next: null }
            };
            
            if (weight && weightToVolumeMap[weight]) {
                const volumeInfo = weightToVolumeMap[weight];
                const minVolume = volumeInfo.min;
                const maxVolume = volumeInfo.next;
                
                if (volume < minVolume) {
                    throw new Error(`容积必须大于等于 ${minVolume} 立方米`);
                }
                
                if (maxVolume && volume >= maxVolume) {
                    throw new Error(`容积必须小于 ${maxVolume} 立方米`);
                }
            }
            
            // 显示加载状态
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
            submitBtn.disabled = true;
            
            // 发送创建任务请求
            const response = await fetch('/api/dispatch-tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(taskData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 显示成功消息
                this.showToast('派车任务创建成功', 'success');
                
                // 重置表单
                form.reset();
                
                // 重新加载任务列表
                await this.loadDispatchTasks();
            } else {
                throw new Error(result.message || '创建任务失败');
            }
        } catch (error) {
            this.errorHandler.handle(error, '创建派车任务失败');
        } finally {
            // 恢复提交按钮
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '创建任务';
            submitBtn.disabled = false;
        }
    }
    
    /**
     * 显示Toast提示
     */
    showToast(message, type = 'info') {
        // 使用现有的showToast函数或创建新的
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // 简单的alert实现
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.manualDispatchApp = new ManualDispatchApp();
    } catch (error) {
        console.error('Failed to initialize manual dispatch app:', error);
    }
});