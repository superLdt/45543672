/**
 * Debug - 调试工具类
 * 提供统一的调试日志输出
 */

export class Debug {
    constructor(namespace = 'App') {
        this.namespace = namespace;
        this.isEnabled = localStorage.getItem('debug') === 'true' || 
                        localStorage.getItem('debug')?.includes(namespace);
    }
    
    /**
     * 输出普通日志
     */
    log(...args) {
        if (this.isEnabled) {
            console.log(`[${this.namespace}]`, ...args);
        }
    }
    
    /**
     * 输出错误日志
     */
    error(...args) {
        if (this.isEnabled) {
            console.error(`[${this.namespace}]`, ...args);
        }
    }
    
    /**
     * 输出警告日志
     */
    warn(...args) {
        if (this.isEnabled) {
            console.warn(`[${this.namespace}]`, ...args);
        }
    }
    
    /**
     * 输出信息日志
     */
    info(...args) {
        if (this.isEnabled) {
            console.info(`[${this.namespace}]`, ...args);
        }
    }
    
    /**
     * 设置调试开关
     */
    static setEnabled(enabled) {
        localStorage.setItem('debug', enabled.toString());
    }
    
    /**
     * 获取调试状态
     */
    static isEnabled() {
        return localStorage.getItem('debug') === 'true';
    }
}