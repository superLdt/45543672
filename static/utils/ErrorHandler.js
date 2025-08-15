/**
 * ErrorHandler - 错误处理工具类
 * 提供统一的错误处理和用户提示
 */

export class ErrorHandler {
    constructor(options = {}) {
        this.options = {
            defaultMessage: '操作失败，请稍后重试',
            showToast: true,
            ...options
        };
    }
    
    /**
     * 处理错误
     */
    handle(error, customMessage = null) {
        console.error('ErrorHandler:', error);
        
        const message = customMessage || this.getErrorMessage(error);
        
        if (this.options.showToast) {
            this.showToast(message, 'error');
        }
        
        // 发送错误到服务器（可选）
        if (window.errorReporter) {
            window.errorReporter.report(error);
        }
    }
    
    /**
     * 获取错误消息
     */
    getErrorMessage(error) {
        if (typeof error === 'string') {
            return error;
        }
        
        if (error.response) {
            // HTTP错误
            switch (error.response.status) {
                case 400:
                    return '请求参数错误';
                case 401:
                    return '请重新登录';
                case 403:
                    return '权限不足';
                case 404:
                    return '资源不存在';
                case 500:
                    return '服务器内部错误';
                default:
                    return `网络错误 (${error.response.status})`;
            }
        }
        
        if (error.message) {
            return error.message;
        }
        
        return this.options.defaultMessage;
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
            alert(message);
        }
    }
    
    /**
     * 显示确认对话框
     */
    async confirm(message, title = '确认操作') {
        return new Promise((resolve) => {
            const confirmed = confirm(`${title}\n\n${message}`);
            resolve(confirmed);
        });
    }
}