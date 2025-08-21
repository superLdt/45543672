/**
 * 基础管理-车辆管理模块 - 重构版
 * 基于ES6模块化架构，与TaskManagementApp保持一致
 */

import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';
import { Pagination } from './Pagination.js';

/**
 * 车辆管理器类
 * 提供车辆信息的CRUD操作、搜索筛选等功能
 */
export class VehicleManager {
    constructor(options = {}) {
        this.debug = new Debug('VehicleManager');
        this.errorHandler = new ErrorHandler();
        
        // 状态管理
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 1;
        this.searchTerm = '';
        this.sortField = 'id';
        this.sortOrder = 'asc';
        this.filters = {};
        this.currentEditingVehicle = null;
        
        
        // 绑定方法
        this.bindMethods();
        
        this.debug.log('VehicleManager 实例化完成');
    }

    /**
     * 绑定方法到实例，确保this上下文正确
     */
    bindMethods() {
        this.init = this.init.bind(this);
        this.loadVehicles = this.loadVehicles.bind(this);
        this.renderVehicles = this.renderVehicles.bind(this);
        this.searchVehicles = this.searchVehicles.bind(this);
        this.addVehicle = this.addVehicle.bind(this);
        this.updateVehicle = this.updateVehicle.bind(this);
        this.deleteVehicle = this.deleteVehicle.bind(this);
        this.handleResponse = this.handleResponse.bind(this);
        this.showToast = this.showToast.bind(this);
        this.formatSuppliers = this.formatSuppliers.bind(this);
        this.formatDateTime = this.formatDateTime.bind(this);
    }

    /**
     * 初始化车辆管理器
     */
    async init() {
        try {
            this.debug.log('开始初始化车辆管理器...');
            await this.checkAuth();
            
            // 获取公司名称映射
            await this.fetchCompanyNames();
            
            // 初始化分页
            this.pagination = new Pagination({
                containerId: 'paginationContainer',
                pageSize: 10
            });
            
            this.pagination.onPageChange(async (page) => {
                await this.loadVehicles(page);
            });
            
            await this.loadVehicles();
            this.bindEvents();
            this.debug.log('车辆管理器初始化完成');
        } catch (error) {
            this.errorHandler.handle(error, '车辆管理器初始化失败');
            this.showToast('初始化失败，请刷新页面重试', 'error');
        }
    }

    /**
     * 检查用户认证状态
     */
    async checkAuth() {
        try {
            const response = await fetch('/debug/user', {
                credentials: 'include'
            });
            
            if (response.status === 401) {
                this.debug.log('用户未登录，重定向到登录页');
                window.location.href = '/login';
                return false;
            }
            
            if (response.ok) {
                const userData = await response.json();
                this.debug.log('用户已登录:', userData);
                return true;
            }
            
            return false;
        } catch (error) {
            this.errorHandler.handle(error, '认证检查失败');
            return false;
        }
    }

    /**
     * 处理API响应
     */
    async handleResponse(response) {
        if (response.status === 401) {
            this.debug.log('会话过期，重定向到登录页');
            window.location.href = '/login';
            throw new Error('未登录或会话已过期');
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.error?.message || '操作失败');
        }
        
        return data;
    }

    /**
     * 加载车辆数据
     */
    async loadVehicles(page = 1) {
        try {
            this.showLoading();
            this.currentPage = page;
            
            const params = new URLSearchParams({
                page: page,
                limit: this.pageSize,
                search: this.searchTerm,
                sort: this.sortField,
                order: this.sortOrder,
                ...this.filters
            });
            
            const response = await fetch(`/api/dispatch/vehicle-capacity?${params}`, {
                credentials: 'include'
            });
            
            const data = await this.handleResponse(response);
            this.renderVehicles(data.data?.list || []);
            this.updatePagination(data.data?.total || 0);
            
        } catch (error) {
            this.errorHandler.handle(error, '加载车辆数据失败');
            this.showToast('加载数据失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 搜索车辆
     */
    async searchVehicles(term) {
        this.searchTerm = term;
        this.currentPage = 1;
        await this.loadVehicles();
    }

    /**
     * 添加车辆
     */
    async addVehicle(vehicleData) {
        try {
            this.showLoading();
            
            const response = await fetch('/api/dispatch/vehicle-capacity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(vehicleData)
            });
            
            await this.handleResponse(response);
            this.showToast('车辆添加成功');
            await this.loadVehicles();
            
        } catch (error) {
            this.errorHandler.handle(error, '添加车辆失败');
            this.showToast('添加失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 更新车辆
     */
    async updateVehicle(vehicleData) {
        try {
            this.showLoading();
            
            const response = await fetch('/api/dispatch/vehicle-capacity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(vehicleData)
            });
            
            await this.handleResponse(response);
            this.showToast('车辆更新成功');
            await this.loadVehicles();
            
        } catch (error) {
            this.errorHandler.handle(error, '更新车辆失败');
            this.showToast('更新失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 删除车辆
     */
    async deleteVehicle(licensePlate) {
        if (!confirm(`确定要删除车牌号为 ${licensePlate} 的车辆吗？`)) {
            return;
        }
        
        try {
            this.showLoading();
            
            const response = await fetch(`/api/dispatch/vehicle-capacity/${licensePlate}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            await this.handleResponse(response);
            this.showToast('车辆删除成功');
            await this.loadVehicles();
            
        } catch (error) {
            this.errorHandler.handle(error, '删除车辆失败');
            this.showToast('删除失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * 渲染车辆列表
     */
    renderVehicles(vehicles) {
        const tbody = document.querySelector('#vehicleTableBody');
        const emptyState = document.querySelector('.empty-state');
        
        if (!tbody) return;
        
        if (!vehicles || vehicles.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            // 确保分页容器也被清空
            if (this.pagination) {
                this.pagination.setData(0, 1);
                this.pagination.render();
            }
            return;
        }
        
        if (emptyState) emptyState.style.display = 'none';
        
        // 计算序号：基于当前页码和页大小
        const startIndex = (this.currentPage - 1) * this.pageSize + 1;
        
        tbody.innerHTML = vehicles.map((vehicle, index) => `
            <tr>
                <td>${startIndex + index}</td>
                <td>${vehicle.vehicle_type || ''}</td>
                <td>${vehicle.license_plate || ''}</td>
                <td>${vehicle.standard_volume || ''}</td>
                <td>${this.formatSuppliers(vehicle.suppliers)}</td>
                <td>${this.formatDateTime(vehicle.created_at)}</td>
                <td>${this.formatDateTime(vehicle.updated_at)}</td>
                <td>
                    <button class="btn btn-sm btn-primary edit-vehicle-btn" 
                            data-license-plate="${vehicle.license_plate}">
                        编辑
                    </button>
                    <button class="btn btn-sm btn-danger delete-vehicle-btn" 
                            data-license-plate="${vehicle.license_plate}">
                        删除
                    </button>
                </td>
            </tr>
        `).join('');
        
        // 按钮事件已经在bindEvents中绑定
    }

    /**
     * 更新分页
     * 使用Pagination.js进行分页管理
     */
    updatePagination(totalItems) {
        this.debug.log(`更新分页: 总记录数=${totalItems}, 当前页=${this.currentPage}, 页大小=${this.pageSize}`);
        
        // 确保分页容器存在
        const container = document.getElementById('paginationContainer');
        if (!container) {
            this.debug.error('分页容器未找到: #paginationContainer');
            return;
        }
        
        this.pagination.setData(totalItems, this.currentPage);
        this.pagination.render();
        
        // 确保分页容器可见
        container.style.display = totalItems > 0 ? 'flex' : 'none';
    }

    /**
     * 格式化供应商显示
     */
    formatSuppliers(suppliers) {
        if (!suppliers) return '-';
        try {
            const supplierList = typeof suppliers === 'string' ? JSON.parse(suppliers) : suppliers;
            if (Array.isArray(supplierList)) {
                // 将ID数组转换为公司名称数组
                return supplierList.map(id => this.companyMap[id] || id).join(', ');
            }
            return String(supplierList);
        } catch {
            return String(suppliers);
        }
    }

    /**
     * 获取公司名称
     */
    async fetchCompanyNames() {
        try {
            const response = await fetch('/api/companies', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const companies = await response.json();
                // 创建ID到名称的映射
                this.companyMap = {};
                companies.forEach(company => {
                    this.companyMap[company.id] = company.name;
                });
            }
        } catch (error) {
            console.error('获取公司名称失败:', error);
        }
    }

    /**
     * 格式化日期时间显示
     */
    formatDateTime(dateTimeStr) {
        if (!dateTimeStr) return '-';
        try {
            const date = new Date(dateTimeStr);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
          
            });
        } catch {
            return dateTimeStr;
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loading = document.querySelector('.loading');
        if (loading) loading.style.display = 'block';
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        const loading = document.querySelector('.loading');
        if (loading) loading.style.display = 'none';
    }

    /**
     * 显示Toast通知
     */
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    /**
     * 绑定事件
     */
    /**
     * 初始化事件绑定
     */
    bindEvents() {
        // 搜索按钮
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.handleSearch());
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('resetSearchBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.handleReset());
        }
        
        // 新增车辆按钮
        const addBtn = document.getElementById('addVehicleBtn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.showAddModal());
        }
        
        // 空状态添加按钮
        const emptyAddBtn = document.getElementById('emptyAddBtn');
        if (emptyAddBtn) {
            emptyAddBtn.addEventListener('click', () => this.showAddModal());
        }
        
        // 导入按钮
        const importBtn = document.getElementById('importBtn');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.showImportModal());
        }
        
        // 下载模板链接
        const downloadTemplateLink = document.getElementById('downloadTemplateLink');
        if (downloadTemplateLink) {
            downloadTemplateLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.downloadImportTemplate();
            });
        }

        // 文件上传功能
        this.initFileUpload();
        
        // 导出按钮
        const exportBtn = document.getElementById('exportBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.showExportModal());
        }
        
        // 表格操作事件委托
        const tableBody = document.getElementById('vehicleTableBody');
        if (tableBody) {
            tableBody.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                if (!row) return;
                
                const licensePlate = row.dataset.licensePlate;
                if (!licensePlate) return;
                
                // 编辑按钮
                if (e.target.classList.contains('edit-btn') || e.target.closest('.edit-btn')) {
                    this.editVehicle(licensePlate);
                }
                // 删除按钮
                else if (e.target.classList.contains('delete-btn') || e.target.closest('.delete-btn')) {
                    this.deleteVehicle(licensePlate);
                }
            });
        }
        
        // 回车搜索
        const searchInputs = document.querySelectorAll('#searchVehicleType, #searchLicensePlate, #searchSuppliers');
        searchInputs.forEach(input => {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch();
                }
            });
        });
        
        // 导入模态框关闭按钮
        const closeImportModalBtn = document.getElementById('closeImportModalBtn');
        const cancelImportBtn = document.getElementById('cancelImportBtn');
        const importModal = document.getElementById('importModal');
        
        const closeImportModal = () => {
            if (importModal) {
                importModal.style.display = 'none';
            }
        };
        
        if (closeImportModalBtn) {
            closeImportModalBtn.addEventListener('click', closeImportModal);
        }
        
        if (cancelImportBtn) {
            cancelImportBtn.addEventListener('click', closeImportModal);
        }
        
        // 点击导入模态框背景关闭
        if (importModal) {
            importModal.addEventListener('click', (e) => {
                if (e.target === importModal) {
                    closeImportModal();
                }
            });
        }
        
        // 导出模态框关闭按钮
        const closeExportModalBtn = document.getElementById('closeExportModalBtn');
        const cancelExportBtn = document.getElementById('cancelExportBtn');
        const exportModal = document.getElementById('exportModal');
        
        const closeExportModal = () => {
            if (exportModal) {
                exportModal.style.display = 'none';
            }
        };
        
        if (closeExportModalBtn) {
            closeExportModalBtn.addEventListener('click', closeExportModal);
        }
        
        if (cancelExportBtn) {
            cancelExportBtn.addEventListener('click', closeExportModal);
        }
        
        // 点击导出模态框背景关闭
        if (exportModal) {
            exportModal.addEventListener('click', (e) => {
                if (e.target === exportModal) {
                    closeExportModal();
                }
            });
        }
        
        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeImportModal();
                closeExportModal();
            }
        });
    }

    /**
     * 显示导入模态框
     */
    showImportModal() {
        const importModal = document.getElementById('importModal');
        if (importModal) {
            importModal.style.display = 'flex';
        }
    }

    /**
     * 显示导出模态框
     */
    showExportModal() {
        const exportModal = document.getElementById('exportModal');
        if (exportModal) {
            exportModal.style.display = 'flex';
        }
    }

    /**
     * 下载车辆信息导入模板
     */
    downloadImportTemplate() {
        this.debug.log('开始下载车辆信息导入模板');
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = '/basic_data/vehicle_import_template';
        link.download = '车辆信息导入模板.xlsx';
        link.style.display = 'none';
        
        // 添加到DOM并触发下载
        document.body.appendChild(link);
        link.click();
        
        // 清理
        setTimeout(() => {
            document.body.removeChild(link);
            this.debug.log('车辆信息导入模板下载已启动');
        }, 100);
    }

    /**
     * 初始化文件上传功能
     * 支持拖拽上传和点击选择文件
     */
    initFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileUploadArea = document.getElementById('fileUploadArea');
        const selectedFileName = document.getElementById('selectedFileName');
        const startImportBtn = document.getElementById('startImportBtn');

        if (!fileInput || !fileUploadArea) {
            this.debug.warn('文件上传元素未找到');
            return;
        }

        // 点击上传区域触发文件选择
        fileUploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // 文件选择事件
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            this.handleFileSelection(file);
        });

        // 拖拽上传功能
        this.setupDragAndDrop(fileUploadArea, selectedFileName, startImportBtn);
    }

    /**
     * 设置拖拽上传功能
     */
    setupDragAndDrop(uploadArea, fileNameDisplay, importBtn) {
        // 防止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // 拖拽进入时的视觉反馈
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('drag-over');
                uploadArea.style.borderColor = 'var(--feishu-primary)';
                uploadArea.style.backgroundColor = 'rgba(51, 112, 255, 0.05)';
            });
        });

        // 拖拽离开时的视觉反馈
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('drag-over');
                uploadArea.style.borderColor = '';
                uploadArea.style.backgroundColor = '';
            });
        });

        // 文件放置事件
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                this.handleFileSelection(file);
            }
        });
    }

    /**
     * 处理文件选择
     */
    handleFileSelection(file) {
        const selectedFileName = document.getElementById('selectedFileName');
        const startImportBtn = document.getElementById('startImportBtn');
        const fileUploadArea = document.getElementById('fileUploadArea');

        if (!file) {
            this.resetFileSelection();
            return;
        }

        // 验证文件类型
        const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
        if (!validTypes.includes(file.type) && !file.name.endsWith('.xlsx')) {
            this.showToast('请选择Excel文件(.xlsx)', 'error');
            this.resetFileSelection();
            return;
        }

        // 验证文件大小（最大10MB）
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showToast('文件大小不能超过10MB', 'error');
            this.resetFileSelection();
            return;
        }

        // 显示文件名和启用导入按钮
        if (selectedFileName) {
            selectedFileName.textContent = `已选择: ${file.name}`;
            selectedFileName.style.display = 'block';
        }

        if (startImportBtn) {
            startImportBtn.disabled = false;
            startImportBtn.addEventListener('click', () => this.handleFileImport(file));
        }

        // 更新上传区域样式
        if (fileUploadArea) {
            fileUploadArea.style.borderColor = 'var(--feishu-success)';
            fileUploadArea.style.backgroundColor = 'rgba(82, 196, 26, 0.05)';
        }

        this.debug.log(`文件选择完成: ${file.name}, 大小: ${(file.size / 1024).toFixed(2)}KB`);
    }

    /**
     * 重置文件选择状态
     */
    resetFileSelection() {
        const selectedFileName = document.getElementById('selectedFileName');
        const startImportBtn = document.getElementById('startImportBtn');
        const fileUploadArea = document.getElementById('fileUploadArea');
        const fileInput = document.getElementById('fileInput');

        if (selectedFileName) {
            selectedFileName.style.display = 'none';
            selectedFileName.textContent = '';
        }

        if (startImportBtn) {
            startImportBtn.disabled = true;
            startImportBtn.replaceWith(startImportBtn.cloneNode(true)); // 移除事件监听器
        }

        if (fileUploadArea) {
            fileUploadArea.style.borderColor = '';
            fileUploadArea.style.backgroundColor = '';
        }

        if (fileInput) {
            fileInput.value = '';
        }
    }

    /**
     * 处理文件导入
     */
    async handleFileImport(file) {
        const startImportBtn = document.getElementById('startImportBtn');
        const importSpinner = document.getElementById('importSpinner');

        if (!file) {
            this.showToast('请选择文件', 'error');
            return;
        }

        try {
            // 显示加载状态
            if (startImportBtn) {
                startImportBtn.disabled = true;
            }
            if (importSpinner) {
                importSpinner.style.display = 'inline-block';
            }

            this.debug.log(`开始导入文件: ${file.name}`);

            // 创建FormData对象
            const formData = new FormData();
            formData.append('file', file);

            // 发送导入请求
            const response = await fetch('/api/dispatch/vehicle-capacity/batch-import', {
                method: 'POST',
                credentials: 'include',
                body: formData
            });

            const data = await this.handleResponse(response);
            
            this.showToast(`导入成功: ${data.message || '文件导入完成'}`, 'success');
            this.debug.log('文件导入成功');

            // 关闭导入模态框并刷新数据
            this.closeImportModal();
            await this.loadVehicles();

        } catch (error) {
            this.errorHandler.handle(error, '文件导入失败');
            this.showToast(`导入失败: ${error.message}`, 'error');
            
            // 恢复按钮状态
            if (startImportBtn) {
                startImportBtn.disabled = false;
            }
        } finally {
            // 隐藏加载状态
            if (importSpinner) {
                importSpinner.style.display = 'none';
            }
            if (startImportBtn) {
                startImportBtn.disabled = false;
            }
        }
    }

    /**
     * 关闭导入模态框
     */
    closeImportModal() {
        const importModal = document.getElementById('importModal');
        if (importModal) {
            importModal.style.display = 'none';
            this.resetFileSelection();
        }
    }

    /**
     * 显示添加模态框 - 飞书风格
     */
    showAddModal() {
        this.debug.log('显示添加车辆模态框');
        
        // 创建模态框容器
        const modal = document.createElement('div');
        modal.className = 'feishu-modal';
        modal.id = 'addVehicleModal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            animation: modalFadeIn 0.3s ease;
        `;

        // 创建模态框内容
        modal.innerHTML = `
            <div class="feishu-modal-content" style="
                background: var(--feishu-white);
                border-radius: var(--feishu-radius-lg);
                box-shadow: var(--feishu-shadow-lg);
                width: 90%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
                animation: slideDown 0.3s ease;">
                
                <div class="feishu-modal-header" style="
                    padding: var(--feishu-spacing-lg);
                    border-bottom: 1px solid var(--feishu-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;">
                    <h3 class="feishu-modal-title" style="
                        margin: 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: var(--feishu-text-primary);">
                        <i class="fas fa-plus" style="color: var(--feishu-primary); margin-right: 8px;"></i>
                        添加车辆
                    </h3>
                    <button type="button" class="feishu-modal-close" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: var(--feishu-text-tertiary);
                        padding: 0;
                        width: 32px;
                        height: 32px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        transition: all 0.2s ease;">
                        &times;
                    </button>
                </div>

                <div class="feishu-modal-body" style="padding: var(--feishu-spacing-lg);">
                    <form id="addVehicleForm" novalidate>
                        <div class="form-group" style="margin-bottom: var(--feishu-spacing-md);">
                            <label class="form-label form-required" style="
                                display: block;
                                font-size: 14px;
                                font-weight: 600;
                                color: var(--feishu-text-primary);
                                margin-bottom: var(--feishu-spacing-xs);">
                                <i class="fas fa-car" style="margin-right: 4px;"></i>
                                车辆类型
                            </label>
                            <select class="feishu-select" id="vehicleType" required style="
                                width: 100%;
                                padding: 8px 12px;
                                border: 1px solid var(--feishu-border);
                                border-radius: var(--feishu-radius);
                                font-size: 14px;
                                color: var(--feishu-text-primary);">
                                <option value="">请选择车辆类型</option>
                                <option value="单车">单车</option>
                                <option value="挂车">挂车</option>
                                <option value="厢式货车">厢式货车</option>
                                <option value="平板车">平板车</option>
                                <option value="冷藏车">冷藏车</option>
                            </select>
                            <div class="field-error" style="
                                color: var(--feishu-error);
                                font-size: 12px;
                                margin-top: 4px;
                                display: none;"></div>
                        </div>

                        <div class="form-group" style="margin-bottom: var(--feishu-spacing-md);">
                            <label class="form-label form-required" style="
                                display: block;
                                font-size: 14px;
                                font-weight: 600;
                                color: var(--feishu-text-primary);
                                margin-bottom: var(--feishu-spacing-xs);">
                                <i class="fas fa-hashtag" style="margin-right: 4px;"></i>
                                车牌号
                            </label>
                            <input type="text" class="feishu-input" id="licensePlate" required 
                                   maxlength="10" placeholder="例如：皖A12345" style="
                                width: 100%;
                                padding: 8px 12px;
                                border: 1px solid var(--feishu-border);
                                border-radius: var(--feishu-radius);
                                font-size: 14px;
                                color: var(--feishu-text-primary);">
                            <div class="field-error" style="
                                color: var(--feishu-error);
                                font-size: 12px;
                                margin-top: 4px;
                                display: none;"></div>
                        </div>

                        <div class="form-group" style="margin-bottom: var(--feishu-spacing-md);">
                            <label class="form-label form-required" style="
                                display: block;
                                font-size: 14px;
                                font-weight: 600;
                                color: var(--feishu-text-primary);
                                margin-bottom: var(--feishu-spacing-xs);">
                                <i class="fas fa-box" style="margin-right: 4px;"></i>
                                标准容积(m³)
                            </label>
                            <input type="number" class="feishu-input" id="standardVolume" required 
                                   min="0" step="0.1" placeholder="例如：50.0" style="
                                width: 100%;
                                padding: 8px 12px;
                                border: 1px solid var(--feishu-border);
                                border-radius: var(--feishu-radius);
                                font-size: 14px;
                                color: var(--feishu-text-primary);">
                            <div class="field-error" style="
                                color: var(--feishu-error);
                                font-size: 12px;
                                margin-top: 4px;
                                display: none;"></div>
                        </div>

                        <div class="form-group" style="margin-bottom: var(--feishu-spacing-md);">
                            <label class="form-label" style="
                                display: block;
                                font-size: 14px;
                                font-weight: 600;
                                color: var(--feishu-text-primary);
                                margin-bottom: var(--feishu-spacing-xs);">
                                <i class="fas fa-users" style="margin-right: 4px;"></i>
                                供应商
                            </label>
                            <input type="text" class="feishu-input" id="suppliers" 
                                   placeholder="请输入供应商名称，多个用逗号分隔" style="
                                width: 100%;
                                padding: 8px 12px;
                                border: 1px solid var(--feishu-border);
                                border-radius: var(--feishu-radius);
                                font-size: 14px;
                                color: var(--feishu-text-primary);">
                            <small class="form-hint" style="
                                display: block;
                                font-size: 12px;
                                color: var(--feishu-text-secondary);
                                margin-top: 4px;">
                                多个供应商请用逗号分隔，例如：供应商A, 供应商B
                            </small>
                        </div>
                    </form>
                </div>

                <div class="feishu-modal-footer" style="
                    padding: var(--feishu-spacing-lg);
                    border-top: 1px solid var(--feishu-border);
                    display: flex;
                    justify-content: flex-end;
                    gap: var(--feishu-spacing-sm);
                    <button type="button" class="feishu-btn feishu-btn-secondary" id="cancelModalBtn">
                        取消
                    </button>
                    <button type="button" class="feishu-btn feishu-btn-primary" id="saveVehicleBtn">
                        保存
                    </button>
                </div>
            </div>
        `;

        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes modalFadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes modalFadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideDown {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-5px); }
                75% { transform: translateX(5px); }
            }
            .feishu-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                animation: modalFadeIn 0.3s ease;
            }
            .feishu-modal-content {
                background: var(--feishu-white);
                border-radius: var(--feishu-radius-lg);
                box-shadow: var(--feishu-shadow-lg);
                width: 90%;
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
                animation: slideDown 0.3s ease;
            }
            .feishu-modal-header {
                padding: var(--feishu-spacing-lg);
                border-bottom: 1px solid var(--feishu-border);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .feishu-modal-title {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                color: var(--feishu-text-primary);
            }
            .feishu-modal-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: var(--feishu-text-tertiary);
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.2s ease;
            }
            .feishu-modal-close:hover {
                background-color: var(--feishu-bg);
                color: var(--feishu-text-primary);
            }
            .feishu-modal-body {
                padding: var(--feishu-spacing-lg);
            }
            .feishu-modal-footer {
                padding: var(--feishu-spacing-lg);
                border-top: 1px solid var(--feishu-border);
                display: flex;
                justify-content: flex-end;
                gap: var(--feishu-spacing-sm);
            }
            .form-group {
                margin-bottom: var(--feishu-spacing-md);
            }
            .form-label {
                display: block;
                font-size: 14px;
                font-weight: 600;
                color: var(--feishu-text-primary);
                margin-bottom: var(--feishu-spacing-xs);
            }
            .form-required::after {
                content: ' *';
                color: var(--feishu-error);
            }
            .feishu-input, .feishu-select {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid var(--feishu-border);
                border-radius: var(--feishu-radius);
                font-size: 14px;
                color: var(--feishu-text-primary);
                transition: all 0.2s ease;
            }
            .feishu-input:focus, .feishu-select:focus {
                outline: none;
                border-color: var(--feishu-primary);
                box-shadow: 0 0 0 2px rgba(51, 112, 255, 0.2);
            }
            .feishu-input.error {
                border-color: var(--feishu-error) !important;
                box-shadow: 0 0 0 2px rgba(245, 74, 69, 0.2) !important;
            }
            .field-error {
                color: var(--feishu-error);
                font-size: 12px;
                margin-top: 4px;
                display: none;
            }
            .field-error.show {
                display: block;
                animation: shake 0.3s ease-in-out;
            }
            .form-hint {
                display: block;
                font-size: 12px;
                color: var(--feishu-text-secondary);
                margin-top: 4px;
            }
        `;
        document.head.appendChild(style);

        // 绑定事件
        const closeBtn = modal.querySelector('.feishu-modal-close');
        const cancelBtn = modal.querySelector('#cancelModalBtn');
        const saveBtn = modal.querySelector('#saveVehicleBtn');
        const form = modal.querySelector('#addVehicleForm');

        // 关闭模态框
        const closeModal = () => {
            modal.style.animation = 'modalFadeOut 0.3s ease';
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
                if (style.parentNode) {
                    style.parentNode.removeChild(style);
                }
            }, 300);
        };

        // 点击关闭按钮
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // ESC键关闭
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        // 表单验证
        const validateField = (field) => {
            const value = field.value.trim();
            const errorEl = field.parentNode.querySelector('.field-error');
            
            if (field.hasAttribute('required') && !value) {
                const label = field.parentNode.querySelector('.form-label').textContent;
                errorEl.textContent = `${label.replace('*', '').trim()}不能为空`;
                errorEl.classList.add('show');
                field.classList.add('error');
                return false;
            }

            if (field.id === 'licensePlate' && value) {
                const platePattern = /^[\u4e00-\u9fa5][A-Z][0-9A-Z]{5,6}$/;
                if (!platePattern.test(value)) {
                    errorEl.textContent = '请输入正确的车牌号格式，如：皖A12345';
                    errorEl.classList.add('show');
                    field.classList.add('error');
                    return false;
                }
            }

            if (field.id === 'standardVolume' && value) {
                const volume = parseFloat(value);
                if (isNaN(volume) || volume <= 0) {
                    errorEl.textContent = '请输入有效的容积数值';
                    errorEl.classList.add('show');
                    field.classList.add('error');
                    return false;
                }
            }

            errorEl.classList.remove('show');
            field.classList.remove('error');
            return true;
        };

        // 实时验证
        const inputs = modal.querySelectorAll('.feishu-input, .feishu-select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => {
                const errorEl = input.parentNode.querySelector('.field-error');
                if (errorEl.classList.contains('show')) {
                    validateField(input);
                }
            });
        });

        // 保存按钮事件
        saveBtn.addEventListener('click', async () => {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });

            if (!isValid) return;

            const vehicleData = {
                vehicle_type: modal.querySelector('#vehicleType').value,
                license_plate: modal.querySelector('#licensePlate').value,
                standard_volume: parseFloat(modal.querySelector('#standardVolume').value),
                suppliers: modal.querySelector('#suppliers').value
                    .split(',')
                    .map(s => s.trim())
                    .filter(s => s)
            };

            try {
                saveBtn.disabled = true;
                saveBtn.textContent = '保存中...';
                
                await this.addVehicle(vehicleData);
                closeModal();
            } catch (error) {
                this.errorHandler.handle(error, '保存车辆失败');
                saveBtn.disabled = false;
                saveBtn.textContent = '保存';
            }
        });

        // 添加到页面
        document.body.appendChild(modal);
        
        // 聚焦第一个输入框
        setTimeout(() => {
            modal.querySelector('#vehicleType').focus();
        }, 100);
    }

    /**
     * 编辑车辆
     */
    editVehicle(licensePlate) {
        this.debug.log('编辑车辆:', licensePlate);
        // 实现编辑车辆的逻辑
        alert('编辑功能待实现，车牌号: ' + licensePlate);
    }
}
