/**
 * Pagination - 分页管理模块
 * 提供分页功能的独立管理
 */

import { Debug } from '../utils/Debug.js';

export class Pagination {
    constructor(options = {}) {
        this.debug = new Debug('Pagination');
        this.options = {
            containerId: 'paginationContainer',
            pageSize: 10,
            maxVisiblePages: 7,
            ...options
        };
        
        this.state = {
            currentPage: 1,
            totalItems: 0,
            totalPages: 0
        };
        
        this.callbacks = new Map();
    }
    
    /**
     * 设置分页数据
     */
    setData(totalItems, currentPage = 1) {
        this.state.totalItems = totalItems;
        this.state.currentPage = Math.max(1, currentPage);
        this.state.totalPages = Math.max(1, Math.ceil(totalItems / this.options.pageSize));
        
        this.debug.log('Pagination data updated:', {
            totalItems,
            currentPage: this.state.currentPage,
            totalPages: this.state.totalPages
        });
    }
    
    /**
     * 注册页码变更回调
     */
    onPageChange(callback) {
        this.callbacks.set('pageChange', callback);
    }
    
    /**
     * 跳转到指定页
     */
    goToPage(page) {
        if (page < 1 || page > this.state.totalPages) {
            return;
        }
        
        this.state.currentPage = page;
        this.render();
        
        if (this.callbacks.has('pageChange')) {
            this.callbacks.get('pageChange')(page);
        }
    }
    
    /**
     * 获取当前分页信息
     */
    getPaginationInfo() {
        return {
            currentPage: this.state.currentPage,
            totalPages: this.state.totalPages,
            totalItems: this.state.totalItems,
            pageSize: this.options.pageSize,
            hasPrev: this.state.currentPage > 1,
            hasNext: this.state.currentPage < this.state.totalPages,
            startIndex: (this.state.currentPage - 1) * this.options.pageSize,
            endIndex: Math.min(this.state.currentPage * this.options.pageSize, this.state.totalItems)
        };
    }
    
    /**
     * 渲染分页控件
     */
    render() {
        const container = document.getElementById(this.options.containerId);
        if (!container) {
            this.debug.error('Pagination container not found:', this.options.containerId);
            return;
        }
        
        if (this.state.totalPages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        container.innerHTML = this.generatePaginationHTML();
        this.bindEvents(container);
    }
    
    /**
     * 生成分页HTML
     * 使用统一的飞书样式类名
     */
    generatePaginationHTML() {
        const { currentPage, totalPages, hasPrev, hasNext } = this.getPaginationInfo();
        const pages = this.generatePageNumbers(currentPage, totalPages);
        
        return `
            <div class="feishu-pagination">
                <button class="feishu-page-btn ${!hasPrev ? 'feishu-page-btn-disabled' : ''}" 
                        ${!hasPrev ? 'disabled' : ''} 
                        data-page="${currentPage - 1}">
                    <i class="fas fa-chevron-left"></i> 上一页
                </button>
                
                <div class="feishu-page-numbers">
                    ${pages.map(page => 
                        page === '...' 
                            ? `<span class="feishu-page-ellipsis">...</span>`
                            : `<button class="feishu-page-number ${page === currentPage ? 'feishu-page-number-active' : ''}" 
                                       data-page="${page}">${page}</button>`
                    ).join('')}
                </div>
                
                <button class="feishu-page-btn ${!hasNext ? 'feishu-page-btn-disabled' : ''}" 
                        ${!hasNext ? 'disabled' : ''} 
                        data-page="${currentPage + 1}">
                    下一页 <i class="fas fa-chevron-right"></i>
                </button>
                
                <div class="feishu-page-info">
                    <span>第 ${currentPage} 页</span>
                    <span>共 ${totalPages} 页</span>
                    <span>总计 ${this.state.totalItems} 条</span>
                </div>
            </div>
        `;
    }
    
    /**
     * 生成页码数组
     */
    generatePageNumbers(currentPage, totalPages) {
        const pages = [];
        const maxVisible = this.options.maxVisiblePages;
        
        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            
            if (currentPage > 4) {
                pages.push('...');
            }
            
            const start = Math.max(2, currentPage - 2);
            const end = Math.min(totalPages - 1, currentPage + 2);
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            
            if (currentPage < totalPages - 3) {
                pages.push('...');
            }
            
            pages.push(totalPages);
        }
        
        return pages;
    }
    
    /**
     * 绑定分页事件
     */
    bindEvents(container) {
        container.addEventListener('click', (e) => {
            const button = e.target.closest('[data-page]');
            if (button && !button.disabled) {
                const page = parseInt(button.dataset.page);
                this.goToPage(page);
            }
        });
    }
    
    /**
     * 重置分页
     */
    reset() {
        this.state.currentPage = 1;
        this.render();
    }
}