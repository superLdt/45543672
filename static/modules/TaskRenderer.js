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
        const timePriority = this.calculateTimePriority(task.required_date);
        
        return `
            <tr class="task-row" data-task-id="${task.task_id}" style="cursor: pointer;" 
                onmouseover="this.style.backgroundColor='#f5f5f5'" 
                onmouseout="this.style.backgroundColor=''">
                <td>${index + 1}</td>
                <td>
                    <div class="task-id">
                        <span class="text-primary">${task.task_id || task.id}</span>
                    </div>
                </td>
                <td>${task.start_bureau || '-'}</td>
                <td>${task.route_name || '-'}</td>
                <td>
                    <span class="transport-type">${task.transport_type || '-'}</span>
                </td>
                <td>
                    <div style="max-width: 120px;" title="${task.carrier_company || '-'}">
                        ${(task.carrier_company || '-').substring(0, 4)}
                    </div>
                </td>
                <td>
                    <span class="status-badge ${statusClass}">
                        ${this.getStatusText(task.status)}
                    </span>
                </td>
                <td>
                    <span class="priority-badge ${timePriority.class}">
                        ${timePriority.text}
                    </span>
                </td>
                <td>
                    <div class="time-info">
                        <span>${this.formatDateTime(task.required_date)}</span>
                        <small class="text-muted">${timePriority.remaining}</small>
                    </div>
                </td>
                <td>
                    <button class="feishu-btn feishu-btn-primary feishu-btn-sm view-detail" 
                            data-task-id="${task.task_id || task.id}">
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
     * 计算基于时间差的优先级
     * @param {string} requiredDate - 要求时间
     * @returns {object} 优先级信息
     */
    calculateTimePriority(requiredDate) {
        if (!requiredDate) {
            return {
                class: 'priority-normal',
                text: '正常',
                remaining: '无时间要求'
            };
        }

        const now = new Date();
        const required = new Date(requiredDate);
        
        // 计算时间差（小时）
        const diffMs = required.getTime() - now.getTime();
        const diffHours = diffMs / (1000 * 60 * 60);
        
        let priority = {
            class: '',
            text: '',
            remaining: ''
        };

        // 根据时间差设置优先级
        if (diffHours > 48) {
            priority.class = 'priority-normal';
            priority.text = '正常';
        } else if (diffHours > 12) {
            priority.class = 'priority-urgent';
            priority.text = '加急';
        } else if (diffHours > 0) {
            priority.class = 'priority-emergency';
            priority.text = '紧急';
        } else {
            priority.class = 'priority-emergency';
            priority.text = '已超时';
        }

        // 计算剩余时间描述
        if (diffHours > 24) {
            const days = Math.floor(diffHours / 24);
            priority.remaining = `剩余${days}天`;
        } else if (diffHours > 1) {
            priority.remaining = `剩余${Math.floor(diffHours)}小时`;
        } else if (diffHours > 0) {
            const minutes = Math.floor(diffHours * 60);
            priority.remaining = `剩余${minutes}分钟`;
        } else {
            const overdueHours = Math.abs(Math.floor(diffHours));
            priority.remaining = `已超时${overdueHours}小时`;
        }

        return priority;
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
    
    /**
     * 渲染任务详情
     */
    renderTaskDetail(task) {
        const container = document.getElementById(this.options.detailContainerId);
        if (!container) return;

        // 添加加载状态
        container.innerHTML = `
            <div class="detail-header">
                <h5><i class="fas fa-file-alt"></i> 流程详情</h5>
                <button class="feishu-btn feishu-btn-secondary feishu-btn-sm" onclick="taskManagement.closeDetail()">
                    <i class="fas fa-times"></i> 关闭
                </button>
            </div>
            
            <!-- 流程进度 -->
            <div class="detail-section" style="padding:12px 16px;border-bottom:1px solid var(--feishu-border);">
                <h6 style="color:var(--feishu-text-secondary);margin-bottom:12px;font-size:14px;">流程进度</h6>
                <div class="progress-steps" style="gap:8px;">
                    ${this.renderProgressSteps(task)}
                </div>
            </div>
            
            <!-- 基础信息 -->
            <div class="detail-section" style="padding:12px 16px;border-bottom:1px solid var(--feishu-border);">
                <h6 style="color:var(--feishu-text-secondary);margin-bottom:12px;font-size:14px;">基础信息</h6>
                <div style="font-size:13px;line-height:1.6;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">任务编号</span><span style="font-weight:500;">${task.task_id || task.id}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">轨道类型</span><span style="font-weight:500;">${task.dispatch_track || '-'}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">始发局</span><span style="font-weight:500;">${task.start_bureau || '-'}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">线路名称</span><span style="font-weight:500;">${task.route_name || '-'}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">运输类型</span><span style="font-weight:500;">${task.transport_type || '-'}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">承运商</span><span style="font-weight:500;">${task.carrier_company || '-'}</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">吨位/容积</span><span style="font-weight:500;">${task.weight || '-'}吨/${task.volume || '-'}立方米</span></div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:var(--feishu-text-secondary);">发起时间</span><span style="font-weight:500;">${this.formatDateTime(task.created_at)}</span></div>
                    <div style="display:flex;justify-content:space-between;"><span style="color:var(--feishu-text-secondary);">要求时间</span><span style="font-weight:500;">${this.formatDateTime(task.required_date)}</span></div>
                </div>
            </div>
            
            <!-- 操作记录 -->
            <div class="detail-section" style="padding:12px 16px;border-bottom:1px solid var(--feishu-border);">
                <h6 style="color:var(--feishu-text-secondary);margin-bottom:12px;font-size:14px;">操作记录</h6>
                <div class="feishu-timeline" style="padding:0;">
                    ${this.renderOperationRecords(task)}
                </div>
            </div>
            
            <!-- 当前操作 -->
            <div class="detail-section" style="padding:12px 16px;">
                <h6 style="color:var(--feishu-text-secondary);margin-bottom:12px;font-size:14px;">当前操作</h6>
                <div style="display:flex;gap:8px;flex-direction:column;">
                    ${this.renderOperationButtons(task)}
                </div>
            </div>
        `;
    }
    
    /**
     * 根据用户角色和任务状态渲染操作按钮
     */
    renderOperationButtons(task) {
        // 获取当前用户信息
        const userInfo = window.currentUserInfo || {};
        const userRole = userInfo.user_role || '';
        
        // 根据角色和状态确定可显示的按钮
        let buttons = [];
        
        // 超级管理员、区域调度员
        if (userRole === '超级管理员' || userRole === '区域调度员') {
            // 根据任务状态显示不同的按钮
            if (task.status === '待调度员审核') {
                buttons.push(`
                    <button class="feishu-btn feishu-btn-primary" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.confirmApproval('${task.id}')">
                        <i class="fas fa-check"></i> 确认审批
                    </button>
                    <button class="feishu-btn feishu-btn-danger" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.rejectApproval('${task.id}')">
                        <i class="fas fa-times"></i> 拒绝审批
                    </button>
                `);
            } else {
                // 其他状态显示提示信息
                buttons.push(`<div class="feishu-alert feishu-alert-info" style="padding:8px 12px;font-size:13px;">请等待流程进度确认</div>`);
            }
        }
        // 车间地调
        else if (userRole === '车间地调') {
            if (task.status === '供应商已响应') {
                buttons.push(`
                    <button class="feishu-btn feishu-btn-primary" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.workshopDeparture('${task.id}')">
                        <i class="fas fa-truck"></i> 车间发车
                    </button>
                `);
            } else if (task.status === '供应商已确认') {
                buttons.push(`
                    <button class="feishu-btn feishu-btn-primary" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.finalConfirmation('${task.id}')">
                        <i class="fas fa-check-circle"></i> 最终确认
                    </button>
                `);
            } else {
                // 其他状态显示提示信息
                buttons.push(`<div class="feishu-alert feishu-alert-info" style="padding:8px 12px;font-size:13px;">请等待流程进度确认</div>`);
            }
        }
        // 供应商
        else if (userRole === '供应商') {
            if (task.status === '待供应商响应') {
                buttons.push(`
                    <button class="feishu-btn feishu-btn-primary" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.confirmResponse('${task.id}')">
                        <i class="fas fa-check"></i> 确认响应
                    </button>
                `);
            } else {
                // 其他状态显示提示信息
                buttons.push(`<div class="feishu-alert feishu-alert-info" style="padding:8px 12px;font-size:13px;">请等待流程进度确认</div>`);
            }
        }
        // 默认按钮（兼容旧数据）
        else {
            buttons.push(`
                <button class="feishu-btn feishu-btn-primary" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.confirmResponse('${task.id}')">
                    <i class="fas fa-check"></i> 确认响应
                </button>
                <button class="feishu-btn feishu-btn-warning" style="padding:8px 12px;font-size:13px;" onclick="taskManagement.requestPause('${task.id}')">
                    <i class="fas fa-exclamation-triangle"></i> 申请暂停
                </button>
                <div class="feishu-alert feishu-alert-info" style="padding:8px 12px;font-size:13px;margin-top:8px;">请等待流程进度确认</div>
            `);
        }
        
        return buttons.join('\n');
    }

    /**
     * 渲染进度步骤
     * 根据任务的当前状态动态计算每个步骤的状态
     */
    renderProgressSteps(task) {
        // 根据轨道类型确定步骤
        let steps = [];
        
        // 定义轨道A和轨道B的状态流转
        const trackAStatusFlow = [
            '待提交',
            '待调度员审核',
            '待供应商响应',
            '供应商已响应',
            '车间已核查',
            '供应商已确认',
            '任务结束'
        ];
        
        const trackBStatusFlow = [
            '待供应商响应',
            '供应商已响应',
            '车间已核查',
            '供应商已确认',
            '任务结束'
        ];
        
        // 获取当前状态的索引
        let currentStatusIndex = -1;
        
        if (task.dispatch_track === '轨道A') {
            currentStatusIndex = trackAStatusFlow.indexOf(task.status);
            steps = [
                { name: '车间地调需求', key: 'requirement' },
                { name: '区域调度审核', key: 'dispatch' },
                { name: '供应商响应', key: 'carrier' },
                { name: '车间发车', key: 'departure' },
                { name: '供应商确认', key: 'confirmation' },
                { name: '车间最终确认', key: 'final' }
            ];
        } else if (task.dispatch_track === '轨道B') {
            currentStatusIndex = trackBStatusFlow.indexOf(task.status);
            steps = [
                { name: '区域调度直派', key: 'dispatch' },
                { name: '供应商响应', key: 'carrier' },
                { name: '车间发车', key: 'departure' },
                { name: '供应商确认', key: 'confirmation' },
                { name: '车间最终确认', key: 'final' }
            ];
        } else {
            // 默认步骤（兼容旧数据）
            steps = [
                { name: '区域调度派车', key: 'dispatch' },
                { name: '承运商响应', key: 'carrier' },
                { name: '车间发车', key: 'departure' },
                { name: '承运商确认', key: 'confirmation' },
                { name: '车间最终确认', key: 'final' }
            ];
        }

        // 为每个步骤设置状态
        steps = steps.map((step, index) => {
            // 默认状态为待处理
            let status = 'pending';
            
            // 根据当前状态索引设置步骤状态
            if (task.dispatch_track === '轨道A') {
                if (index < currentStatusIndex) {
                    status = 'completed';
                } else if (index === currentStatusIndex) {
                    status = 'in_progress';
                }
            } else if (task.dispatch_track === '轨道B') {
                // 对于轨道B，当状态为"待供应商响应"时，"区域调度直派"步骤应显示为已完成
                if (task.status === '待供应商响应' && index === 0) {
                    status = 'completed';
                } 
                // 对于轨道B，当状态为"待供应商响应"时，"供应商响应"步骤应显示为进行中
                else if (task.status === '待供应商响应' && index === 1) {
                    status = 'in_progress';
                } else if (index < currentStatusIndex) {
                    status = 'completed';
                } else if (index === currentStatusIndex) {
                    status = 'in_progress';
                }
            }
            
            return {
                ...step,
                status: status
            };
        });

        return steps.map((step, index) => {
            const isCompleted = step.status === 'completed';
            const isActive = step.status === 'in_progress';
            const isPending = step.status === 'pending';
            
            // 处理操作人和时间信息
            let subtitleText = '';
            if (isCompleted) {
                subtitleText = '已完成';
            } else if (isActive) {
                subtitleText = '进行中';
            } else {
                subtitleText = '待处理';
            }

            return `
                <div class="progress-step ${isCompleted ? 'completed' : isActive ? 'active' : ''}" 
                     style="padding: 8px; border-radius: var(--feishu-radius);">
                    <div class="step-icon ${isCompleted ? 'completed' : isActive ? 'active' : 'pending'}" 
                         style="width: 20px; height: 20px; font-size: 10px;">
                        ${index + 1}
                    </div>
                    <div class="step-content">
                        <p class="step-title" style="font-size: 13px; margin: 0;">${step.name}</p>
                        <p class="step-subtitle" style="font-size: 11px; margin: 0; color: var(--feishu-text-secondary);">
                            ${subtitleText}
                        </p>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    /**
     * 渲染操作记录
     */
    renderOperationRecords(task) {
        // 从任务数据中获取操作记录
        // 如果任务数据中包含history字段，则使用该字段
        // 否则使用静态数据演示
        const records = task.history || [
            { title: '区域调度派车', operator: '张经理', time: '08:30', description: '派车至合肥中心局，5吨车辆' }
        ];
        
        return records.map(record => `
            <div class="timeline-item" style="padding:8px 0;">
                <div class="timeline-dot" style="width:6px;height:6px;margin-left:-15px;"></div>
                <div class="timeline-content">
                    <p class="timeline-title" style="font-size:13px;margin:0;">${record.title || record.status_change}</p>
                    <p class="timeline-subtitle" style="font-size:11px;margin:0;">${record.operator || '系统'} ${this.formatDateTime(record.time || record.timestamp)}</p>
                    <p class="timeline-desc" style="font-size:12px;margin-top:2px;">${record.description || record.note || ''}</p>
                </div>
            </div>
        `).join('');
    }

    /**
     * 显示任务详情加载状态
     */
    showDetailLoading() {
        const container = document.getElementById(this.options.detailContainerId);
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 40px; text-align: center;">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">加载中...</span>
                </div>
                <p style="margin-top: 12px; color: var(--feishu-text-secondary);">正在加载任务详情...</p>
            </div>
        `;
    }

    /**
     * 显示任务详情错误状态
     */
    showDetailError(message) {
        const container = document.getElementById(this.options.detailContainerId);
        if (!container) return;

        container.innerHTML = `
            <div style="padding: 40px; text-align: center;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: var(--feishu-danger); margin-bottom: 16px;"></i>
                <p style="color: var(--feishu-text-secondary); margin-bottom: 16px;">${message}</p>
                <button class="feishu-btn feishu-btn-primary" onclick="taskManagement.retryDetail()">
                    <i class="fas fa-redo"></i> 重试
                </button>
            </div>
        `;
    }

    /**
     * 渲染任务统计信息
     */
    renderStatistics(statistics) {
        const container = document.getElementById(this.options.detailContainerId);
        if (!container || !statistics) return;

        container.innerHTML = `
            <div class="statistics-container">
                <div class="statistics-header">
                    <h3>任务统计概览</h3>
                    <div class="statistics-time">更新时间：${new Date().toLocaleString('zh-CN')}</div>
                </div>
                
                <div class="statistics-grid">
                    <div class="stat-card primary">
                        <div class="stat-icon">📊</div>
                        <div class="stat-content">
                            <div class="stat-number">${statistics.total_tasks || 0}</div>
                            <div class="stat-label">总任务数</div>
                        </div>
                    </div>
                    
                    <div class="stat-card success">
                        <div class="stat-icon">📈</div>
                        <div class="stat-content">
                            <div class="stat-number">${statistics.today_new_tasks || 0}</div>
                            <div class="stat-label">今日新增</div>
                        </div>
                    </div>
                    
                    <div class="stat-card warning">
                        <div class="stat-icon">⚠️</div>
                        <div class="stat-content">
                            <div class="stat-number">${statistics.urgent_tasks || 0}</div>
                            <div class="stat-label">即将超时</div>
                        </div>
                    </div>
                </div>

                <div class="statistics-section">
                    <h4>状态分布</h4>
                    <div class="status-distribution">
                        ${Object.entries(statistics.status_counts || {}).map(([status, count]) => `
                            <div class="status-item">
                                <span class="status-name">${status}</span>
                                <span class="status-count">${count}</span>
                                <div class="status-bar">
                                    <div class="status-bar-fill" style="width: ${statistics.total_tasks > 0 ? (count / statistics.total_tasks * 100) : 0}%"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="statistics-section">
                    <h4>轨道类型分布</h4>
                    <div class="track-distribution">
                        ${Object.entries(statistics.track_counts || {}).map(([track, count]) => `
                            <div class="track-item">
                                <span class="track-name">${track}</span>
                                <span class="track-count">${count}</span>
                                <div class="track-bar">
                                    <div class="track-bar-fill" style="width: ${statistics.total_tasks > 0 ? (count / statistics.total_tasks * 100) : 0}%"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                ${statistics.urgent_tasks > 0 ? `
                    <div class="urgent-notice">
                        <div class="notice-icon">🚨</div>
                        <div class="notice-content">
                            <h5>紧急提醒</h5>
                            <p>有 ${statistics.urgent_tasks} 个任务需要在24小时内处理，请及时关注！</p>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
}
