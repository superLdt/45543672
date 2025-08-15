/**
 * TaskRenderer - 任务渲染模块
 * 负责任务数据的UI渲染和样式管理
 */

import { Debug } from '../utils/Debug.js';

export class TaskRenderer {
    constructor(options = {}) {
        this.debug = new Debug('TaskRenderer');
        this.options = {
            tableId: 'taskListBody',
            emptyStateId: 'emptyState',
            ...options
        };
    }
    
    /**
     * 渲染任务列表
     */
    renderTasks(tasks) {
        const tbody = document.getElementById(this.options.tableId);
        if (!tbody) {
            this.debug.error('Table body not found:', this.options.tableId);
            return;
        }
        
        if (!tasks || tasks.length === 0) {
            this.showEmptyState();
            return;
        }
        
        tbody.innerHTML = tasks.map((task, index) => 
            this.renderTaskRow(task, index)
        ).join('');
        
        this.debug.log(`Rendered ${tasks.length} tasks`);
    }
    
    /**
     * 渲染单个任务行
     */
    renderTaskRow(task, index) {
        const statusClass = this.getStatusClass(task.status);
        const priorityClass = this.getPriorityClass(task.priority);
        
        return `
            <tr class="task-row" data-task-id="${task.id}">
                <td>${index + 1}</td>
                <td>
                    <div class="task-id">
                        <span class="text-primary">${task.task_id || task.id}</span>
                    </div>
                </td>
                <td>${task.start_location || '-'}</td>
                <td>${task.end_location || '-'}</td>
                <td>
                    <span class="transport-type">${task.transport_type || '-'}</span>
                </td>
                <td>${task.carrier_company || '-'}</td>
                <td>
                    <span class="status-badge ${statusClass}">
                        ${this.getStatusText(task.status)}
                    </span>
                </td>
                <td>
                    <span class="priority-badge ${priorityClass}">
                        ${task.priority || '普通'}
                    </span>
                </td>
                <td>
                    <div class="time-info">
                        <span>${this.formatDateTime(task.required_time)}</span>
                    </div>
                </td>
                <td>
                    <button class="feishu-btn feishu-btn-primary feishu-btn-sm view-detail" 
                            data-task-id="${task.id}">
                        <i class="fas fa-eye"></i> 详情
                    </button>
                </td>
            </tr>
        `;
    }
    
    /**
     * 渲染分页控件
     */
    renderPagination(paginationInfo) {
        const container = document.getElementById('paginationContainer');
        if (!container) return;
        
        const { currentPage, totalPages, totalTasks, hasPrev, hasNext } = paginationInfo;
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        const pages = this.generatePageNumbers(currentPage, totalPages);
        
        container.innerHTML = `
            <button class="feishu-page-btn ${!hasPrev ? 'feishu-page-btn-disabled' : ''}" 
                    ${!hasPrev ? 'disabled' : ''} 
                    onclick="taskManagement.goToPage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i> 上一页
            </button>
            
            <div class="feishu-page-numbers">
                ${pages.map(page => 
                    page === '...' 
                        ? `<span class="feishu-page-ellipsis">...</span>`
                        : `<button class="feishu-page-number ${page === currentPage ? 'feishu-page-number-active' : ''}" 
                                   onclick="taskManagement.goToPage(${page})">${page}</button>`
                ).join('')}
            </div>
            
            <button class="feishu-page-btn ${!hasNext ? 'feishu-page-btn-disabled' : ''}" 
                    ${!hasNext ? 'disabled' : ''} 
                    onclick="taskManagement.goToPage(${currentPage + 1})">
                下一页 <i class="fas fa-chevron-right"></i>
            </button>
            
            <div class="feishu-page-info">
                <span>第 ${currentPage} 页</span>
                <span>共 ${totalPages} 页</span>
                <span>总计 ${totalTasks} 条</span>
            </div>
        `;
    }
    
    /**
     * 生成页码数组
     */
    generatePageNumbers(currentPage, totalPages) {
        const pages = [];
        const maxVisible = 7;
        
        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            
            if (currentPage > 3) {
                pages.push('...');
            }
            
            const start = Math.max(2, currentPage - 1);
            const end = Math.min(totalPages - 1, currentPage + 1);
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            
            if (currentPage < totalPages - 2) {
                pages.push('...');
            }
            
            pages.push(totalPages);
        }
        
        return pages;
    }
    
    /**
     * 显示空状态
     */
    showEmptyState(message = '暂无任务数据') {
        const tbody = document.getElementById(this.options.tableId);
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align: center; padding: 60px;">
                        <div style="color: var(--feishu-text-secondary); margin-bottom: 20px;">
                            <i class="fas fa-inbox fa-3x" style="margin-bottom: 16px; opacity: 0.5;"></i>
                            <p style="font-size: 16px; margin-bottom: 8px;">${message}</p>
                            <p style="font-size: 14px; opacity: 0.7;">请检查筛选条件或稍后再试</p>
                        </div>
                    </td>
                </tr>
            `;
        }
    }
    
    /**
     * 显示加载状态
     */
    showLoading(isLoading) {
        const tbody = document.getElementById(this.options.tableId);
        if (!tbody) return;
        
        if (isLoading) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" style="text-align: center; padding: 60px;">
                        <div class="loading-state">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <p style="margin-top: 16px; color: var(--feishu-text-secondary);">
                                正在加载任务数据...
                            </p>
                        </div>
                    </td>
                </tr>
            `;
        }
    }
    
    /**
     * 获取状态样式类
     */
    getStatusClass(status) {
        const statusMap = {
            'pending': 'status-pending',
            'assigned': 'status-assigned',
            'in_progress': 'status-processing',
            'completed': 'status-completed',
            'cancelled': 'status-error',
            'rejected': 'status-error'
        };
        return statusMap[status] || 'status-default';
    }
    
    /**
     * 获取状态文本
     */
    getStatusText(status) {
        const statusTextMap = {
            'pending': '待处理',
            'assigned': '已分配',
            'in_progress': '进行中',
            'completed': '已完成',
            'cancelled': '已取消',
            'rejected': '已拒绝'
        };
        return statusTextMap[status] || status;
    }
    
    /**
     * 获取优先级样式类
     */
    getPriorityClass(priority) {
        const priorityMap = {
            'urgent': 'priority-urgent',
            'high': 'priority-high',
            'medium': 'priority-medium',
            'low': 'priority-low'
        };
        return priorityMap[priority] || 'priority-normal';
    }
    
    /**
     * 格式化日期时间
     */
    formatDateTime(dateString) {
        if (!dateString) return '-';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;
        
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}