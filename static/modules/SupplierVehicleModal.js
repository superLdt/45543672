/**
 * 供应商车辆信息确认模态框模块
 * 负责处理供应商车辆信息确认的UI显示和数据提交
 */

import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';

export class SupplierVehicleModal {
    static instance = null;
    
    constructor() {
        this.debug = new Debug('SupplierVehicleModal');
        this.errorHandler = new ErrorHandler();
        this.currentTask = null;
        this.modalElement = null;
    }
    
    /**
     * 获取单例实例
     */
    static getInstance() {
        if (!SupplierVehicleModal.instance) {
            SupplierVehicleModal.instance = new SupplierVehicleModal();
        }
        return SupplierVehicleModal.instance;
    }
    
    /**
     * 显示供应商车辆信息确认对话框
     * @param {Object} task - 任务数据
     */
    static show(task) {
        const modal = SupplierVehicleModal.getInstance();
        modal.show(task);
    }
    
    /**
     * 关闭模态框
     */
    static close() {
        const modal = SupplierVehicleModal.getInstance();
        modal.close();
    }
    
    /**
     * 提交表单数据
     */
    static async submit() {
        const modal = SupplierVehicleModal.getInstance();
        await modal.submit();
    }
    
    /**
     * 显示模态框
     * @param {Object} task - 任务数据
     * @param {Object} context - 上下文对象（可选）
     * @param {Object} options - 配置选项
     * @param {string} options.returnUrl - 提交成功后的返回URL
     */
    show(task, context = null, options = {}) {
        this.currentTask = task;
        this.options = options; // 存储配置选项
        this.context = context; // 存储上下文
        this.renderModal();
        this.bindEvents();
        this.showModal();
    }
    
    /**
     * 渲染模态框内容
     */
    renderModal() {
        if (!this.currentTask) return;
        
        // 添加必要的CSS样式
        this.injectStyles();
        
        // 创建模态框容器
        this.modalElement = document.createElement('div');
        this.modalElement.className = 'feishu-modal-overlay';
        this.modalElement.innerHTML = this.getModalTemplate();
        
        // 填充任务数据
        this.fillTaskData();
        
        document.body.appendChild(this.modalElement);
    }
    
    /**
     * 注入必要的CSS样式
     */
    injectStyles() {
        if (document.getElementById('supplierModalStyles')) return;
        
        const style = document.createElement('style');
        style.id = 'supplierModalStyles';
        style.textContent = `
            @keyframes slideDown {
                from { transform: translate(-50%, -100%); opacity: 0; }
                to { transform: translate(-50%, 0); opacity: 1; }
            }
            
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            
            .field-error {
                animation: shake 0.3s ease-in-out;
            }
            
            .form-input.error {
                border-color: #ff4d4f !important;
                box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.2) !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * 获取模态框模板
     * 从模板文件加载HTML内容
     */
    getModalTemplate() {
        // 创建模板容器，使用模板文件的内容
        const templateContainer = document.createElement('div');
        
        // 查找已加载的模板内容
        const existingTemplate = document.getElementById('supplierVehicleModalTemplate');
        if (existingTemplate) {
            templateContainer.innerHTML = existingTemplate.innerHTML;
        } else {
            // 如果没有预加载模板，使用基本结构
            templateContainer.innerHTML = this.getBasicTemplate();
        }
        
        return templateContainer.innerHTML;
    }
    
    /**
     * 获取基础模板（备用方案）
     */
    getBasicTemplate() {
        return `
            <div class="feishu-modal supplier-vehicle-modal">
                <div class="feishu-modal-content supplier-modal-content">
                    <div class="feishu-modal-header">
                        <h3 class="feishu-modal-title">
                            <i class="fas fa-truck" style="color:var(--feishu-success);margin-right:8px;"></i>
                            车辆信息确认
                        </h3>
                        <button class="feishu-modal-close" data-action="close">&times;</button>
                    </div>
                    
                    <div class="feishu-modal-body">
                        <!-- 任务信息卡片 -->
                        <div class="confirmation-card task-info-card">
                            <div class="confirmation-title">
                                <i class="fas fa-info-circle"></i>
                                派车任务信息
                            </div>
                            <div class="confirmation-content">
                                <div class="task-info-grid">
                                    <div class="task-info-item">
                                        <span class="info-label">任务编号:</span>
                                        <span class="info-value" data-field="task_id"></span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="info-label">承运公司:</span>
                                        <span class="info-value" data-field="carrier_company"></span>
                                    </div>
                                    <div class="task-info-item full-width">
                                        <span class="info-label">路线:</span>
                                        <span class="info-value route-display" data-field="route"></span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="info-label">用车时间:</span>
                                        <span class="info-value" data-field="required_date"></span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="info-label">吨位:</span>
                                        <span class="info-value" data-field="tonnage"></span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="info-label">容积:</span>
                                        <span class="info-value" data-field="volume"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 车辆信息表单 -->
                        <form class="supplier-form" id="supplierVehicleForm" novalidate>
                            <!-- 单据信息 -->
                            <div class="form-section">
                                <h4 class="form-section-title">
                                    <i class="fas fa-file-alt"></i>
                                    单据信息
                                    <span class="section-subtitle">请准确填写相关单据号码</span>
                                </h4>
                                
                                <div class="form-row">
                                    <div class="form-group">
                                        <label class="form-label form-required">
                                            <i class="fas fa-hashtag"></i>
                                            路单流水号
                                        </label>
                                        <input type="text" 
                                               class="form-input" 
                                               name="manifest_number" 
                                               placeholder="例：LS20240115001"
                                               required
                                               maxlength="20">
                                        <span class="form-hint">格式：LS + 年月日 + 序号</span>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label form-required">
                                            <i class="fas fa-file-invoice"></i>
                                            派车单号
                                        </label>
                                        <input type="text" 
                                               class="form-input" 
                                               name="dispatch_number" 
                                               placeholder="例：PC20240115001"
                                               required
                                               maxlength="20">
                                        <span class="form-hint">格式：PC + 年月日 + 序号</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 车辆信息 -->
                            <div class="form-section">
                                <h4 class="form-section-title">
                                    <i class="fas fa-car"></i>
                                    车辆信息
                                    <span class="section-subtitle">请提供准确的车辆信息</span>
                                </h4>
                                
                                <div class="form-row">
                                    <div class="form-group vehicle-plate">
                                        <label class="form-label form-required">
                                            <i class="fas fa-car-side"></i>
                                            车牌号
                                        </label>
                                        <input type="text" 
                                               class="form-input" 
                                               name="license_plate" 
                                               placeholder="例：京A12345"
                                               required
                                               pattern="^[\u4e00-\u9fa5][A-Z][0-9A-Z]{5,6}$"
                                               maxlength="8">
                                        <span class="form-hint">格式：省份简称 + 字母 + 5-6位数字/字母</span>
                                    </div>
                                    
                                    <div class="form-group">
                                        <label class="form-label">
                                            <i class="fas fa-box"></i>
                                            车厢号
                                        </label>
                                        <input type="text" 
                                               class="form-input" 
                                               name="carriage_number" 
                                               placeholder="可选填写"
                                               maxlength="10">
                                        <span class="form-hint">如有多个车厢请填写</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 备注信息 -->
                            <div class="form-section">
                                <h4 class="form-section-title">
                                    <i class="fas fa-sticky-note"></i>
                                    备注信息
                                    <span class="section-subtitle">补充说明或特殊要求</span>
                                </h4>
                                
                                <div class="form-group">
                                    <label class="form-label">
                                        <i class="fas fa-edit"></i>
                                        备注
                                    </label>
                                    <textarea class="form-textarea" 
                                              name="notes" 
                                              placeholder="如有特殊要求或补充说明，请在此填写..."
                                              maxlength="500"
                                              rows="3"></textarea>
                                    <span class="form-hint">最多500字符</span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div class="feishu-modal-footer">
                        <button type="button" class="feishu-btn feishu-btn-secondary" data-action="close">
                            <i class="fas fa-times"></i>
                            取消
                        </button>
                        <button type="button" class="feishu-btn feishu-btn-primary" data-action="submit">
                            <i class="fas fa-check"></i>
                            确认响应
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 填充任务数据
     */
    fillTaskData() {
        if (!this.currentTask || !this.modalElement) return;
        
        const task = this.currentTask;
        
        // 填充任务信息
        this.modalElement.querySelector('[data-field="task_id"]').textContent = task.task_id || task.id || '';
        this.modalElement.querySelector('[data-field="carrier_company"]').textContent = task.carrier_company || '未指定';
        
        // 格式化路线显示，避免多余空格
        const startBureau = task.start_bureau || '';
        const routeName = task.route_name || '';
        const routeDisplay = startBureau && routeName ? `${startBureau} → ${routeName}` : 
                           startBureau || routeName || '未指定路线';
        this.modalElement.querySelector('[data-field="route"]').textContent = routeDisplay;
        
        this.modalElement.querySelector('[data-field="required_date"]').textContent = this.formatDateTime(task.required_date);
        
        // 填充吨位和容积信息
        const weight = task.weight;
        const weightText = (weight !== null && weight !== undefined && weight !== '' && weight !== 0) ? `${weight}吨` : '未指定';
        this.modalElement.querySelector('[data-field="weight"]').textContent = weightText;
        this.modalElement.querySelector('[data-field="volume"]').textContent = task.volume ? `${task.volume}m³` : '未指定';
    }
    
    /**
     * 绑定事件处理
     */
    bindEvents() {
        if (!this.modalElement) return;
        
        // 关闭按钮
        this.modalElement.querySelectorAll('[data-action="close"]').forEach(btn => {
            btn.addEventListener('click', () => this.close());
        });
        
        // 提交按钮
        const submitBtn = this.modalElement.querySelector('[data-action="submit"]');
        if (submitBtn) {
            submitBtn.addEventListener('click', () => this.submit());
        }
        
        // 点击背景关闭
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                this.close();
            }
        });
        
        // ESC键关闭
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        
        // 表单验证
        this.bindFormValidation();
    }
    
    /**
     * 键盘事件处理
     */
    handleKeyDown(e) {
        if (e.key === 'Escape') {
            this.close();
        }
    }
    
    /**
     * 绑定表单验证
     */
    bindFormValidation() {
        const form = this.modalElement.querySelector('#supplierVehicleForm');
        if (!form) return;
        
        // 实时验证
        const inputs = form.querySelectorAll('.form-input[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }
    
    /**
     * 验证单个字段
     */
    validateField(input) {
        const value = input.value.trim();
        const fieldName = input.name;
        
        // 清除之前的错误状态
        this.clearFieldError(input);
        
        // 必填验证
        if (!value) {
            this.showFieldError(input, `${this.getFieldLabel(fieldName)}不能为空`);
            return false;
        }
        
        // 车牌号格式验证
        if (fieldName === 'license_plate') {
            const pattern = /^[\u4e00-\u9fa5][A-Z][0-9A-Z]{5,6}$/;
            if (!pattern.test(value)) {
                this.showFieldError(input, '请输入正确的车牌号格式，如：京A12345');
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 显示字段错误
     */
    showFieldError(input, message) {
        input.classList.add('error');
        
        const formGroup = input.closest('.form-group');
        if (formGroup) {
            let errorEl = formGroup.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'field-error';
                errorEl.style.cssText = `
                    color: #ff4d4f;
                    font-size: 12px;
                    margin-top: 4px;
                    background: #fff2f0;
                    border: 1px solid #ffccc7;
                    border-radius: 4px;
                    padding: 4px 8px;
                    animation: shake 0.3s ease-in-out;
                `;
                formGroup.appendChild(errorEl);
            }
            errorEl.textContent = message;
        }
    }
    
    /**
     * 清除字段错误
     */
    clearFieldError(input) {
        input.classList.remove('error');
        
        const formGroup = input.closest('.form-group');
        if (formGroup) {
            const errorEl = formGroup.querySelector('.field-error');
            if (errorEl) {
                errorEl.remove();
            }
        }
    }
    
    /**
     * 显示模态框
     */
    showModal() {
        if (!this.modalElement) return;
        
        document.body.appendChild(this.modalElement);
        
        // 添加动画效果
        setTimeout(() => {
            this.modalElement.classList.add('show');
        }, 10);
    }
    
    /**
     * 关闭模态框
     */
    close() {
        if (!this.modalElement) return;
        
        // 移除事件监听器
        document.removeEventListener('keydown', this.handleKeyDown.bind(this));
        
        // 添加关闭动画
        this.modalElement.classList.add('hide');
        
        setTimeout(() => {
            if (this.modalElement && this.modalElement.parentNode) {
                this.modalElement.remove();
            }
            this.modalElement = null;
            this.currentTask = null;
        }, 300);
    }
    
    /**
     * 提交表单数据
     */
    async submit() {
        if (!this.currentTask || !this.modalElement) return;
        
        const form = this.modalElement.querySelector('#supplierVehicleForm');
        if (!form) return;
        
        // 验证所有字段
        const inputs = form.querySelectorAll('.form-input[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            this.showError('请正确填写所有必填项');
            return;
        }
        
        // 收集表单数据
        const formData = new FormData(form);
        const vehicleData = {
            manifest_number: formData.get('manifest_number')?.trim(),
            dispatch_number: formData.get('dispatch_number')?.trim(),
            license_plate: formData.get('license_plate')?.trim(),
            carriage_number: formData.get('carriage_number')?.trim() || null,
            notes: formData.get('notes')?.trim() || null
        };
        
        const taskId = this.currentTask.task_id || this.currentTask.id;
        
        // 检查任务状态，如果已经响应则提示用户
        if (this.currentTask.status === '供应商已响应') {
            this.showError('该任务已经确认响应，请勿重复提交');
            return;
        }
        
        // 移除了额外的服务器状态检查以提高响应速度
        // 原代码：向服务器查询任务的最新状态
        
        try {
            // 显示加载状态
            const submitBtn = this.modalElement.querySelector('[data-action="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 提交中...';
            }
            
            const response = await fetch(`/api/dispatch/tasks/${taskId}/confirm-with-vehicle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    ...vehicleData,
                    task_id: taskId,
                    response_type: 'accept'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 成功提交 - 显示成功消息并自动跳转
                if (window.feishuUtils && window.feishuUtils.showToast) {
                    window.feishuUtils.showToast('车辆信息提交成功，正在跳转...', 'success', {
                        duration: 1500,
                        onClose: () => {
                            this.handleSuccessRedirect();
                        }
                    });
                } else {
                    this.showSuccess('提交成功，正在跳转...');
                    setTimeout(() => this.handleSuccessRedirect(), 1000);
                }
                
                // 关闭模态框
                this.close();
                
            } else {
                // 显示具体的错误信息
                const errorMsg = result.message || result.error?.message || '提交失败，请重试';
                this.showError(errorMsg);
                
                // 如果是唯一约束冲突，高亮对应字段
                if (result.error?.code === 4003) {
                    const manifestInput = form.querySelector('input[name="manifest_number"]');
                    if (manifestInput) {
                        this.showFieldError(manifestInput, '路单流水号已存在');
                    }
                } else if (result.error?.code === 4004) {
                    const dispatchInput = form.querySelector('input[name="dispatch_number"]');
                    if (dispatchInput) {
                        this.showFieldError(dispatchInput, '派车单号已存在');
                    }
                }
            }
            
        } catch (error) {
            this.debug.error('车辆信息确认失败:', error);
            this.showError('网络错误，请稍后重试');
        } finally {
            // 恢复按钮状态
            const submitBtn = this.modalElement?.querySelector('[data-action="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-check"></i> 确认响应';
            }
        }
    }
    
    /**
     * 处理成功后的跳转 - 强制跳转到任务管理页面
     */
    handleSuccessRedirect() {
        // 无论任何情况，强制跳转到任务管理页面
        console.log('供应商确认成功，强制跳转到: /scheduling/task-management');
        window.location.href = '/scheduling/task-management';
    }
    
    /**
     * 格式化日期时间
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
     * 获取字段标签
     */
    getFieldLabel(fieldName) {
        const labels = {
            'manifest_number': '路单流水号',
            'dispatch_number': '派车单号',
            'license_plate': '车牌号',
            'carriage_number': '车厢号',
            'notes': '备注'
        };
        return labels[fieldName] || fieldName;
    }
    
    /**
     * 显示成功消息
     */
    showSuccess(message) {
        // 使用项目中已有的Toast通知组件
        if (typeof showToast === 'function') {
            showToast(message, 'success');
        } else {
            console.log('Success:', message);
        }
    }
    
    /**
     * 显示错误消息
     */
    showError(message) {
        // 使用统一的错误提示方式，增强在暗色背景下的可见性
        if (window.feishuUtils && window.feishuUtils.showToast) {
            window.feishuUtils.showToast(message, 'error', {
                backgroundColor: '#ff4d4f',
                textColor: '#ffffff',
                duration: 4000,
                position: 'top-center'
            });
        } else {
            // 创建自定义错误提示
            const errorDiv = document.createElement('div');
            errorDiv.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #ff4d4f;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 9999;
                font-size: 14px;
                max-width: 400px;
                text-align: center;
                animation: slideDown 0.3s ease-out;
            `;
            errorDiv.textContent = message;
            document.body.appendChild(errorDiv);
            
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 3000);
        }
    }
}

// 添加样式
const styles = `
<style>
/* 供应商车辆信息确认模态框样式 */
.supplier-vehicle-modal {
    z-index: 1050;
}

.supplier-vehicle-modal.show {
    animation: fadeIn 0.3s ease;
}

.supplier-vehicle-modal.hide {
    animation: fadeOut 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes fadeOut {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.9); }
}

.feishu-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1040;
}

.field-error {
    color: #ef4444;
    font-size: 12px;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.field-error::before {
    content: '\f071';
    font-family: 'Font Awesome 6 Free';
    font-weight: 900;
}

.form-input.error {
    border-color: #ef4444;
    background-color: #fef2f2;
}

.form-input.error:focus {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}
</style>
`;

// 注入样式
document.head.insertAdjacentHTML('beforeend', styles);

// 导出实例
window.SupplierVehicleModal = SupplierVehicleModal;