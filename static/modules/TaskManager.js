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
            
            // 添加超时控制和重试机制
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
            
            const response = await fetch(`${this.options.apiEndpoint}?${params}`, {
                credentials: 'include',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 适配API返回格式：可能是数组或包含list的对象
                let tasks = [];
                let total = 0;
                
                if (Array.isArray(result.data)) {
                    // 兼容旧格式：直接是数组
                    tasks = result.data;
                    total = tasks.length;
                } else if (result.data && Array.isArray(result.data.list)) {
                    // 新格式：包含list的对象
                    tasks = result.data.list;
                    total = result.data.total || 0;
                } else {
                    // 其他情况
                    tasks = [];
                    total = 0;
                }
                
                this.state.tasks = tasks;
                this.state.totalTasks = total;
                this.emit('data-loaded', {
                    tasks: this.state.tasks,
                    total: this.state.totalTasks
                });
            } else {
                throw new Error(result.error?.message || '加载任务失败');
            }
            
        } catch (error) {
            this.debug.error('Failed to load tasks:', error);
            
            // 网络错误时的友好提示
            if (error.name === 'AbortError' || error.message.includes('fetch')) {
                error.message = '网络连接超时，请检查网络后重试';
            }
            
            this.errorHandler.handle(error);
            this.emit('error', error);
            
            // 清空数据避免显示错误数据
            this.state.tasks = [];
            this.state.totalTasks = 0;
            this.emit('data-loaded', { tasks: [], total: 0 });
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
            this.debug.log(`Fetching task detail for ID: ${taskId}`);
            const response = await fetch(`${this.options.apiEndpoint}/${taskId}`, {
                credentials: 'include'
            });
            
            this.debug.log(`Task detail response status: ${response.status}`);
            
            // 处理401未认证错误，重定向到登录页面
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.debug.log('Task detail result:', result);
            return result.success ? result.data : null;
            
        } catch (error) {
            this.debug.error('Failed to get task detail:', error);
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 获取当前用户信息
     */
    async getCurrentUserInfo() {
        try {
            this.debug.log('Fetching current user info');
            const response = await fetch('/api/dispatch/user/info', {
                credentials: 'include'
            });
            
            this.debug.log(`User info response status: ${response.status}`);
            
            // 处理401未认证错误，重定向到登录页面
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            this.debug.log('User info result:', result);
            return result.success ? result.data : null;
            
        } catch (error) {
            this.debug.error('Failed to get user info:', error);
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
     * 显示供应商确认响应对话框
     * 供应商对派车任务进行接单确认，填写车辆信息
     * @param {string} taskId - 任务ID
     */
    showSupplierConfirmDialog(taskId) {
        const task = this.state.tasks.find(t => (t.task_id || t.id) === taskId);
        if (!task) return;

        // 构建正确的返回URL - 使用相对路径
        const returnUrl = encodeURIComponent('/scheduling/task-management');

        // 使用独立的供应商车辆信息确认模块
        import('./SupplierVehicleModal.js').then(({ SupplierVehicleModal }) => {
            SupplierVehicleModal.show(task, this, { returnUrl });
        }).catch(error => {
            console.error('Failed to load SupplierVehicleModal:', error);
            // 降级处理：使用旧的实现
            this.showLegacySupplierConfirmDialog(task);
        });
    }

    /**
     * 传统供应商确认对话框（降级方案）
     * @param {Object} task - 任务数据
     */
    showLegacySupplierConfirmDialog(task) {
        console.warn('Using legacy supplier confirm dialog');
        const modal = this.createSupplierVehicleModal(task);
        document.body.appendChild(modal);
    }

    /**
     * 创建供应商车辆信息填写模态框（保留为降级方案）
     */
    createSupplierVehicleModal(task) {
        const modal = document.createElement('div');
        modal.className = 'feishu-modal';
        modal.id = 'supplierVehicleModal';
        
        modal.innerHTML = `
            <div class="feishu-modal-content" style="max-width: 600px;">
                <div class="feishu-modal-header">
                    <h3 class="feishu-modal-title">
                        <i class="fas fa-truck" style="color:var(--feishu-success);margin-right:8px;"></i>
                        车辆信息确认
                    </h3>
                    <button class="feishu-modal-close" onclick="this.closest('.feishu-modal').remove()">&times;</button>
                </div>
                
                <div class="feishu-modal-body">
                    <div class="confirmation-card" style="margin-bottom: 20px;">
                        <div class="confirmation-title">派车任务信息</div>
                        <div class="confirmation-content">
                            <div class="form-preview" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div class="form-preview-item">
                                    <span class="form-preview-label">任务编号:</span>
                                    <span class="form-preview-value">${task.task_id || task.id}</span>
                                </div>
                                <div class="form-preview-item">
                                    <span class="form-preview-label">承运公司:</span>
                                    <span class="form-preview-value">${task.carrier_company || ''}</span>
                                </div>
                                <div class="form-preview-item" style="grid-column: 1 / -1;">
                                    <span class="form-preview-label">路线:</span>
                                    <span class="form-preview-value">${task.start_bureau || ''} → ${task.route_name || ''}</span>
                                </div>
                                <div class="form-preview-item">
                                    <span class="form-preview-label">用车时间:</span>
                                    <span class="form-preview-value">${this.formatDateTime(task.required_date)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <form class="supplier-form" id="supplierVehicleForm">
                        <div class="form-section" style="margin-bottom: 15px;">
                            <h4 class="form-section-title" style="margin-bottom: 10px; font-size: 14px;">
                                <i class="fas fa-file-alt"></i> 单据信息
                            </h4>
                            
                            <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label form-required" style="font-size: 13px; margin-bottom: 4px;">路单流水号</label>
                                    <input type="text" 
                                           class="form-input" 
                                           name="manifest_number" 
                                           placeholder="如：LS20240115001"
                                           required
                                           style="height: 32px; font-size: 13px; padding: 6px 8px;">
                                </div>
                                
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label form-required" style="font-size: 13px; margin-bottom: 4px;">派车单号</label>
                                    <input type="text" 
                                           class="form-input" 
                                           name="dispatch_number" 
                                           placeholder="如：PC20240115001"
                                           required
                                           style="height: 32px; font-size: 13px; padding: 6px 8px;">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-section" style="margin-bottom: 15px;">
                            <h4 class="form-section-title" style="margin-bottom: 10px; font-size: 14px;">
                                <i class="fas fa-car"></i> 车辆信息
                            </h4>
                            
                            <div class="form-row" style="display: grid; grid-template-columns: 2fr 1fr; gap: 12px;">
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label form-required" style="font-size: 13px; margin-bottom: 4px;">车牌号</label>
                                    <input type="text" 
                                           class="form-input" 
                                           name="license_plate" 
                                           placeholder="如：京A12345"
                                           required
                                           pattern="^[\u4e00-\u9fa5][A-Z][0-9A-Z]{5,6}$"
                                           style="height: 32px; font-size: 13px; padding: 6px 8px;">
                                </div>
                                
                                <div class="form-group" style="margin-bottom: 0;">
                                    <label class="form-label" style="font-size: 13px; margin-bottom: 4px;">车厢号</label>
                                    <input type="text" 
                                           class="form-input" 
                                           name="carriage_number" 
                                           placeholder="可选"
                                           style="height: 32px; font-size: 13px; padding: 6px 8px;">
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group" style="margin-bottom: 0;">
                            <label class="form-label" style="font-size: 13px; margin-bottom: 4px;">备注信息</label>
                            <textarea class="form-textarea" 
                                      name="notes" 
                                      placeholder="可选：补充说明、特殊要求等..."
                                      style="height: 60px; font-size: 13px; padding: 6px 8px; min-height: 40px;"></textarea>
                        </div>
                    </form>
                </div>
                
                <div class="feishu-modal-footer">
                    <button class="feishu-btn feishu-btn-secondary" style="height: 32px; font-size: 13px;" onclick="this.closest('.feishu-modal').remove()">
                        取消
                    </button>
                    <button class="feishu-btn feishu-btn-primary" style="height: 32px; font-size: 13px;" onclick="taskManager.submitSupplierVehicleConfirm('${task.task_id || task.id}')">
                        <i class="fas fa-check"></i> 确认响应
                    </button>
                </div>
            </div>
        `;
        
        // 添加点击背景关闭功能
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    }

    /**
     * 提交供应商车辆信息确认响应（已废弃）
     * 新的实现已移至 SupplierVehicleModal.js 模块
     * @deprecated 请使用 SupplierVehicleModal.submit() 方法
     */
    async submitSupplierVehicleConfirm(taskId) {
        console.warn('submitSupplierVehicleConfirm is deprecated. Use SupplierVehicleModal instead.');
        // 此方法已被废弃，新的实现由 SupplierVehicleModal 模块处理
    }

    /**
     * 获取字段中文标签
     */
    getFieldLabel(fieldName) {
        const labels = {
            'manifest_number': '路单流水号',
            'dispatch_number': '派车单号',
            'license_plate': '车牌号',
            'driver_name': '司机姓名',
            'driver_phone': '联系电话'
        };
        return labels[fieldName] || fieldName;
    }

    /**
     * 格式化日期时间显示
     */
    formatDateTime(dateStr) {
        if (!dateStr) return '待定';
        try {
            return new Date(dateStr).toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateStr;
        }
    }
    
    /**
     * 添加备注
     */
    async addRemark(taskId, remark) {
        try {
            // 这里应该弹出一个对话框让用户输入备注
            // 暂时使用prompt演示
            const remarkText = remark || prompt('请输入备注信息：');
            
            if (!remarkText) {
                return false;
            }
            
            const response = await fetch(`${this.options.apiEndpoint}/${taskId}/remark`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ remark: remarkText })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                // 触发添加备注事件
                this.emit('remark-added', { taskId, remark: remarkText });
            }
            
            return result.success;
            
        } catch (error) {
            this.debug.error('Failed to add remark:', error);
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 申请暂停
     */
    async requestPause(taskId) {
        try {
            const response = await fetch(`${this.options.apiEndpoint}/${taskId}/pause`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                // 更新本地数据
                const taskIndex = this.state.tasks.findIndex(t => t.id === taskId);
                if (taskIndex !== -1) {
                    this.state.tasks[taskIndex].status = 'paused';
                    this.emit('task-updated', this.state.tasks[taskIndex]);
                }
                
                // 触发申请暂停事件
                this.emit('pause-requested', { taskId });
            }
            
            return result.success;
            
        } catch (error) {
            this.debug.error('Failed to request pause:', error);
            this.errorHandler.handle(error);
            throw error;
        }
    }
    
    /**
     * 设置当前页码
     */
    async setPage(page) {
        if (page < 1 || page > this.getPaginationInfo().totalPages) {
            return;
        }
        
        // 防止重复点击
        if (this.state.isLoading) {
            return;
        }
        
        this.state.currentPage = page;
        
        // 添加页面切换动画
        this.showPageTransition();
        
        await this.loadTasks(this.state.filters);
    }
    
    /**
     * 显示页面切换动画
     */
    showPageTransition() {
        const tbody = document.getElementById('taskTableBody');
        if (tbody) {
            tbody.style.opacity = '0.5';
            tbody.style.transition = 'opacity 0.3s ease';
            
            setTimeout(() => {
                tbody.style.opacity = '1';
            }, 100);
        }
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

    /**
     * 获取任务统计信息
     */
    async getStatistics() {
        try {
            this.emit('loading', true);
            
            const response = await fetch('/api/dispatch/statistics', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (response.status === 401) {
                this.emit('error', '未授权访问，请重新登录');
                return null;
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error?.message || '获取统计信息失败');
            }

            this.emit('loading', false);
            return result.data;
            
        } catch (error) {
            this.emit('loading', false);
            this.emit('error', `获取统计信息失败: ${error.message}`);
            this.debug.error('获取统计信息失败:', error);
            return null;
        }
    }
}