/**
 * 派车任务-供应商响应
 * 供应商车辆信息确认模态框模块
 * 负责处理供应商车辆信息确认的UI显示和数据提交
 */

import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';
import { VehicleSearch } from './VehicleSearch.js';

export class SupplierVehicleModal {
    static instance = null;
    
    constructor() {
        this.debug = new Debug('SupplierVehicleModal');
        this.errorHandler = new ErrorHandler();
        this.currentTask = null;
        this.modalElement = null;
        // 初始化车辆搜索功能
        this.vehicleSearch = new VehicleSearch();
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
        this.requiredVolume = task.volume || 0; // 保存需求车型容积
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
                                        <span class="info-label">需求容积:</span>
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
                                
                                <!-- 实际容积显示 -->
                                <div class="form-row">
                                    <div class="form-group">
                                        <label class="form-label">
                                            <i class="fas fa-cube"></i>
                                            实际容积
                                        </label>
                                        <div class="volume-display" name="actual_volume">
                                            <span class="volume-value">-</span>
                                            <span class="volume-unit">m³</span>
                                        </div>
                                        <span class="form-hint">系统根据车牌号或车厢号自动获取</span>
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
        
        // 初始化实际容积显示
        const volumeValueElement = this.modalElement.querySelector('[name="actual_volume"] .volume-value');
        if (volumeValueElement) {
            volumeValueElement.textContent = '-';
        }
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
        
        // 绑定车辆搜索功能（在bindFormValidation中也进行了绑定）
        const form = this.modalElement.querySelector('#supplierVehicleForm');
        if (form) {
            this.vehicleSearch.bindSearchEvents(form);
        }
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
     * 绑定车辆搜索功能
     */
    bindVehicleSearch() {
        // 车辆搜索功能已通过VehicleSearch类实现
        // 此方法保留以保持向后兼容性
    }
    
    /**
     * 绑定表单验证
     * 同时绑定车辆搜索功能
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
        
        // 为实际容积字段添加特殊验证
        const actualVolumeInput = form.querySelector('input[name="actual_volume"]');
        if (actualVolumeInput) {
            actualVolumeInput.addEventListener('blur', () => this.validateActualVolume(actualVolumeInput));
            actualVolumeInput.addEventListener('input', () => this.clearFieldError(actualVolumeInput));
        }
        
        // 绑定车辆搜索功能
        this.vehicleSearch.bindSearchEvents(form);
        
        // 添加车牌号和车厢号输入事件监听器来触发容积查询
        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        
        if (licensePlateInput) {
            licensePlateInput.addEventListener('input', () => {
                this.clearFieldError(licensePlateInput);
                this.debounceFetchVolume();
            });
        }
        
        if (carriageNumberInput) {
            carriageNumberInput.addEventListener('input', () => {
                this.clearFieldError(carriageNumberInput);
                this.debounceFetchVolume();
            });
        }
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
        
        // 实际容积数值验证
        if (fieldName === 'actual_volume') {
            const volume = parseFloat(value);
            if (isNaN(volume) || volume < 0) {
                this.showFieldError(input, '请输入有效的容积数值');
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
     * 验证实际容积字段
     * 当实际容积小于需求容积时，显示详细的确认对话框
     * @param {HTMLInputElement} input - 实际容积输入框
     * @returns {boolean} 是否验证通过
     */
    validateActualVolume(input) {
        // 先执行常规验证
        if (!this.validateField(input)) {
            return false;
        }
        
        const value = input.value.trim();
        const actualVolume = parseFloat(value);
        
        // 检查实际容积是否小于需求车型容积
        if (actualVolume < this.requiredVolume) {
            // 显示详细的确认对话框
            const confirmMsg = `⚠️ 容积警告

该车实际容积(${actualVolume}m³)小于需求车型容积(${this.requiredVolume}m³)

选择该车将按实际容积(${actualVolume}m³)进行结算

如车辆实际容积与真实情况不符，请及时联系车间地调发车进行量方修改

是否确定选择该车？`;
            
            if (!confirm(confirmMsg)) {
                // 用户选择取消，清空输入并聚焦
                input.value = '';
                input.focus();
                return false;
            }
        }
        
        return true;
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
        
        // 验证实际容积字段
        const actualVolumeInput = form.querySelector('input[name="actual_volume"]');
        if (actualVolumeInput && !this.validateActualVolume(actualVolumeInput)) {
            isValid = false;
        }
        
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
            actual_volume: formData.get('actual_volume') ? parseFloat(formData.get('actual_volume')) : null,
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
     * 防抖函数 - 用于容积查询
     */
    /**
     * 防抖获取容积信息
     * 使用防抖机制避免频繁请求，延迟500ms执行
     */
    debounceFetchVolume() {
        clearTimeout(this.volumeTimeout);
        this.volumeTimeout = setTimeout(() => {
            this.fetchVolume();
        }, 500);
    }
    
    /**
     * 获取车辆容积信息
     * 根据车厢号和车牌号查询对应车辆的实际容积
     * 
     * 查询优先级规则：
     * 1. 优先使用车厢号查询（如果车厢号有值）
     * 2. 车厢号为空时，使用车牌号查询
     * 3. 两个字段都为空时，清空容积显示
     */
    async fetchVolume() {
        const form = this.modalElement?.querySelector('#supplierVehicleForm');
        if (!form) return;
        
        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        
        const carriageNumber = carriageNumberInput?.value?.trim();
        const licensePlate = licensePlateInput?.value?.trim();
        
        // 如果两个字段都为空，清空容积显示
        if (!carriageNumber && !licensePlate) {
            this.setVolumeDisplay('-');
            return;
        }
        
        try {
            // 根据优先级选择查询参数
            let queryParam = '';
            let queryType = '';
            
            if (carriageNumber) {
                // 优先使用车厢号
                queryParam = carriageNumber;
                queryType = 'carriage_number';
            } else if (licensePlate) {
                // 车厢号为空时使用车牌号
                queryParam = licensePlate;
                queryType = 'license_plate';
            }
            
            if (!queryParam) {
                this.setVolumeDisplay('-');
                return;
            }
            
            this.debug.log('查询车辆容积:', { queryParam, queryType });
            
            const response = await fetch(
                `/api/dispatch/vehicle-info/search?query=${encodeURIComponent(queryParam)}&type=${queryType}&limit=1`,
                {
                    credentials: 'include' // 确保携带认证信息
                }
            );
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success && result.data && result.data.length > 0) {
                    // 使用查询到的第一个匹配结果
                    const vehicle = result.data[0];
                    const volume = vehicle.actual_volume || '-';
                    this.setVolumeDisplay(volume);
                    this.debug.log('获取容积成功:', volume);
                } else {
                    // 未找到匹配车辆
                    this.setVolumeDisplay('-');
                    this.debug.log('未找到匹配车辆');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.errorHandler.handle(error, '获取车辆容积失败');
            this.setVolumeDisplay('-');
        }
    }
    
    /**
     * 设置容积显示值
     * @param {string|number} volume - 容积值
     */
    setVolumeDisplay(volume) {
        const volumeValue = this.elements.actualVolume?.querySelector('.volume-value');
        if (volumeValue) {
            volumeValue.textContent = volume || '-';
        }
    }
    
    /**
     * 根据车牌号或车厢号获取车辆信息
     * 查询优先级：1. 车厢号（精确匹配）2. 车牌号（精确匹配）3. 车牌号（模糊匹配）
     * @param {string} licensePlate - 车牌号
     * @param {string} carriageNumber - 车厢号
     */
    async fetchVehicleInfo(licensePlate, carriageNumber) {
        // 如果车厢号有值，优先使用车厢号查询
        const effectiveCarriageNumber = carriageNumber || this.getCurrentCarriageNumber();
        const effectiveLicensePlate = licensePlate || this.getCurrentLicensePlate();
        
        if (!effectiveLicensePlate && !effectiveCarriageNumber) {
            this.clearVehicleInfo();
            return;
        }

        try {
            let url = '/api/dispatch/vehicle-info';
            let params = new URLSearchParams();
            
            // 根据优先级构建查询参数：车厢号优先
            if (effectiveCarriageNumber) {
                // 优先级1：车厢号精确匹配
                params.append('carriage_number', effectiveCarriageNumber);
            } else if (effectiveLicensePlate) {
                // 优先级2：车牌号精确匹配（仅当车厢号为空时）
                params.append('license_plate', effectiveLicensePlate);
            }
            
            url += '?' + params.toString();

            const response = await fetch(url, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    const vehicle = result.data[0];
                    this.populateVehicleInfo(vehicle);
                } else {
                    // 如果精确匹配未找到，尝试模糊匹配车牌号
                    if (!effectiveCarriageNumber && effectiveLicensePlate) {
                        await this.searchByLicensePlate(effectiveLicensePlate);
                    } else {
                        this.clearVehicleInfo();
                    }
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.errorHandler.handle(error, '获取车辆信息失败');
            this.clearVehicleInfo();
        }
    }

    /**
     * 通过车牌号进行模糊搜索
     * @param {string} licensePlate - 车牌号
     */
    async searchByLicensePlate(licensePlate) {
        try {
            const response = await fetch(`/api/dispatch/vehicle-info/search?query=${encodeURIComponent(licensePlate)}&type=license_plate&limit=1`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    const vehicle = result.data[0];
                    this.populateVehicleInfo(vehicle);
                } else {
                    this.clearVehicleInfo();
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.errorHandler.handle(error, '搜索车辆信息失败');
            this.clearVehicleInfo();
        }
    }

    /**
     * 获取当前车厢号值
     * @returns {string} 当前车厢号
     */
    getCurrentCarriageNumber() {
        const form = this.modalElement?.querySelector('#supplierVehicleForm');
        if (!form) return '';
        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        return carriageNumberInput ? carriageNumberInput.value.trim() : '';
    }

    /**
     * 获取当前车牌号值
     * @returns {string} 当前车牌号
     */
    getCurrentLicensePlate() {
        const form = this.modalElement?.querySelector('#supplierVehicleForm');
        if (!form) return '';
        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        return licensePlateInput ? licensePlateInput.value.trim() : '';
    }

    /**
     * 填充车辆信息到表单
     * @param {Object} vehicle - 车辆信息对象
     */
    populateVehicleInfo(vehicle) {
        const form = this.modal.querySelector('form');
        if (!form) return;

        // 只填充空值，不覆盖已有值
        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        if (licensePlateInput && !licensePlateInput.value.trim()) {
            licensePlateInput.value = vehicle.license_plate || '';
        }

        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        if (carriageNumberInput && !carriageNumberInput.value.trim()) {
            carriageNumberInput.value = vehicle.carriage_number || '';
        }

        // 始终更新容积显示，但遵循车厢号优先原则
        this.setVolumeDisplay(vehicle.actual_volume);

        const vehicleTypeInput = form.querySelector('input[name="vehicle_type"]');
        if (vehicleTypeInput && !vehicleTypeInput.value.trim()) {
            vehicleTypeInput.value = vehicle.vehicle_type || '';
        }

        const supplierInput = form.querySelector('input[name="supplier"]');
        if (supplierInput && !supplierInput.value.trim()) {
            supplierInput.value = vehicle.supplier || '';
        }
    }

    /**
     * 设置实际容积显示值
     * @param {string|number} volume - 实际容积值
     */
    setVolumeDisplay(volume) {
        const volumeValueElement = document.querySelector('[name="actual_volume"] .volume-value');
        if (volumeValueElement) {
            volumeValueElement.textContent = volume || '-';
        }
    }

    /**
     * 清空车辆信息
     */
    clearVehicleInfo() {
        const form = this.modal.querySelector('form');
        if (!form) return;

        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        if (licensePlateInput) {
            licensePlateInput.value = '';
        }

        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        if (carriageNumberInput) {
            carriageNumberInput.value = '';
        }

        this.setVolumeDisplay('-');

        const vehicleTypeInput = form.querySelector('input[name="vehicle_type"]');
        if (vehicleTypeInput) {
            vehicleTypeInput.value = '';
        }

        const supplierInput = form.querySelector('input[name="supplier"]');
        if (supplierInput) {
            supplierInput.value = '';
        }
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
            'actual_volume': '实际容积',
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

/* 实际容积显示样式 */
.volume-display {
    display: flex;
    align-items: center;
    min-height: 38px;
    padding: 8px 12px;
    background-color: #f8f9fa;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 14px;
}

.volume-value {
    font-weight: 600;
    color: #1f2937;
    margin-right: 4px;
}

.volume-unit {
    color: #6b7280;
    font-size: 12px;
}
</style>
`;

// 注入样式
document.head.insertAdjacentHTML('beforeend', styles);

// 导出实例
window.SupplierVehicleModal = SupplierVehicleModal;
