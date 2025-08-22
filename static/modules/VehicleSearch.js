/**
 * 车辆信息搜索模块
 * 提供车牌号和车厢号的模糊搜索功能
 */

import { Debug } from '../utils/Debug.js';
import { ErrorHandler } from '../utils/ErrorHandler.js';

export class VehicleSearch {
    constructor() {
        this.debug = new Debug('VehicleSearch');
        this.errorHandler = new ErrorHandler();
        this.searchTimeout = null;
        this.searchDelay = 300; // 搜索延迟（毫秒）
    }

    /**
     * 搜索功能工作原理：
     * 1. 用户在输入框中输入搜索关键词
     * 2. 输入事件触发后，使用防抖机制延迟搜索请求
     * 3. 向后端API发送搜索请求获取匹配结果
     * 4. 将搜索结果渲染到下拉列表中供用户选择
     * 5. 用户点击结果项时，将选中值填入输入框并触发后续操作
     * 
     * 防抖机制：避免用户频繁输入时发送过多请求
     * 搜索API：/api/dispatch/vehicle-info/search
     * 支持搜索类型：license_plate（车牌号）和carriage_number（车厢号）
     */

    /**
     * 绑定搜索事件
     * @param {HTMLElement} form - 表单元素
     */
    bindSearchEvents(form) {
        if (!form) return;

        // 获取车牌号输入框并初始化搜索功能
        const licensePlateInput = form.querySelector('input[name="license_plate"]');
        if (licensePlateInput) {
            this.initLicensePlateSearch(licensePlateInput);
        }

        // 获取车厢号输入框并初始化搜索功能
        const carriageNumberInput = form.querySelector('input[name="carriage_number"]');
        if (carriageNumberInput) {
            this.initCarriageNumberSearch(carriageNumberInput);
        }
    }

    /**
     * 初始化车牌号搜索
     * @param {HTMLElement} inputElement - 车牌号输入框元素
     */
    initLicensePlateSearch(inputElement) {
        if (!inputElement) return;

        // 创建搜索结果容器
        const resultsContainer = this.createResultsContainer(inputElement);
        let isSelectingResult = false; // 标志：是否正在选择结果
        
        // 绑定输入事件
        inputElement.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchLicensePlates(e.target.value, resultsContainer, inputElement);
            }, this.searchDelay);
        });

        // 失去焦点时隐藏结果
        inputElement.addEventListener('blur', () => {
            // 添加一个短暂的延迟，确保点击事件能先执行
            setTimeout(() => {
                if (!isSelectingResult) {
                    resultsContainer.style.display = 'none';
                }
                isSelectingResult = false; // 重置标志
            }, 150);
        });

        // 获得焦点时显示结果（如果有内容）
        inputElement.addEventListener('focus', () => {
            if (inputElement.value && resultsContainer.children.length > 0 && !isSelectingResult) {
                resultsContainer.style.display = 'block';
            }
        });

        // 为容器添加mousedown事件，防止触发blur
        resultsContainer.addEventListener('mousedown', (e) => {
            e.preventDefault(); // 防止触发blur事件
            isSelectingResult = true;
        });
    }

    /**
     * 初始化车厢号搜索
     * @param {HTMLElement} inputElement - 车厢号输入框元素
     */
    initCarriageNumberSearch(inputElement) {
        if (!inputElement) return;

        // 创建搜索结果容器
        const resultsContainer = this.createResultsContainer(inputElement);
        let isSelectingResult = false; // 标志：是否正在选择结果
        
        // 绑定输入事件
        inputElement.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchCarriageNumbers(e.target.value, resultsContainer, inputElement);
            }, this.searchDelay);
        });

        // 失去焦点时隐藏结果
        inputElement.addEventListener('blur', () => {
            // 添加一个短暂的延迟，确保点击事件能先执行
            setTimeout(() => {
                if (!isSelectingResult) {
                    resultsContainer.style.display = 'none';
                }
                isSelectingResult = false; // 重置标志
            }, 150);
        });

        // 获得焦点时显示结果（如果有内容）
        inputElement.addEventListener('focus', () => {
            if (inputElement.value && resultsContainer.children.length > 0 && !isSelectingResult) {
                resultsContainer.style.display = 'block';
            }
        });

        // 为容器添加mousedown事件，防止触发blur
        resultsContainer.addEventListener('mousedown', (e) => {
            e.preventDefault(); // 防止触发blur事件
            isSelectingResult = true;
        });
    }

    /**
     * 创建搜索结果容器
     * @param {HTMLElement} inputElement - 输入框元素
     * @returns {HTMLElement} 结果容器元素
     */
    createResultsContainer(inputElement) {
        // 查找是否已存在结果容器
        let container = inputElement.parentNode.querySelector('.vehicle-search-results');
        if (container) return container;

        // 创建新的结果容器
        container = document.createElement('div');
        container.className = 'vehicle-search-results';
        container.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            max-height: 200px;
            overflow-y: auto;
            display: none;
        `;

        // 插入到输入框后面
        inputElement.parentNode.style.position = 'relative';
        inputElement.parentNode.appendChild(container);

        return container;
    }

    /**
     * 搜索车牌号
     * @param {string} query - 搜索关键词
     * @param {HTMLElement} container - 结果容器
     * @param {HTMLElement} inputElement - 输入框元素
     */
    async searchLicensePlates(query, container, inputElement) {
        if (!query || query.length < 2) {
            container.style.display = 'none';
            return;
        }

        try {
            // 使用fetch发送请求，包含认证信息
            const response = await fetch(`/api/dispatch/vehicle-info/search?query=${encodeURIComponent(query)}&type=license_plate&limit=10`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    this.renderResults(result.data, container, inputElement, 'license_plate');
                    container.style.display = 'block';
                } else {
                    container.style.display = 'none';
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.errorHandler.handle(error, '搜索车牌号失败');
            container.style.display = 'none';
        }
    }

    /**
     * 搜索车厢号
     * @param {string} query - 搜索关键词
     * @param {HTMLElement} container - 结果容器
     * @param {HTMLElement} inputElement - 输入框元素
     */
    async searchCarriageNumbers(query, container, inputElement) {
        if (!query || query.length < 2) {
            container.style.display = 'none';
            return;
        }

        try {
            // 使用fetch发送请求，包含认证信息
            const response = await fetch(`/api/dispatch/vehicle-info/search?query=${encodeURIComponent(query)}&type=carriage_number&limit=10`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    this.renderResults(result.data, container, inputElement, 'carriage_number');
                    container.style.display = 'block';
                } else {
                    container.style.display = 'none';
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.errorHandler.handle(error, '搜索车厢号失败');
            container.style.display = 'none';
        }
    }

    /**
     * 渲染搜索结果
     * @param {Array} results - 搜索结果数组
     * @param {HTMLElement} container - 结果容器
     * @param {HTMLElement} inputElement - 输入框元素
     * @param {string} searchType - 搜索类型
     */
    renderResults(results, container, inputElement, searchType) {
        container.innerHTML = '';

        results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'vehicle-search-result-item';
            resultItem.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f3f4f6;
                transition: background-color 0.2s;
            `;

            if (searchType === 'license_plate') {
                resultItem.innerHTML = `
                    <div style="font-weight: 500;">${item.license_plate}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                        ${item.vehicle_type} | ${item.actual_volume}m³ | ${item.supplier}
                    </div>
                `;
            } else {
                resultItem.innerHTML = `
                    <div style="font-weight: 500;">${item.carriage_number}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                        ${item.license_plate} | ${item.vehicle_type} | ${item.actual_volume}m³
                    </div>
                `;
            }

            // 存储车辆信息到DOM元素
            resultItem.dataset.vehicleInfo = JSON.stringify(item);

            // 点击选择结果
            resultItem.addEventListener('click', async (e) => {
                // 阻止事件冒泡，防止触发输入框的blur事件
                e.stopPropagation();
                
                const vehicleInfo = JSON.parse(resultItem.dataset.vehicleInfo);
                
                if (searchType === 'license_plate') {
                    inputElement.value = vehicleInfo.license_plate;
                } else {
                    inputElement.value = vehicleInfo.carriage_number;
                }
                container.style.display = 'none';
                
                // 智能设置容积 - 根据车厢号优先原则
                await this.setVolumeIntelligently(vehicleInfo);
                
                // 手动触发失焦，确保输入框失去焦点
                inputElement.blur();
                
                // 触发change事件而不是input事件，避免重新触发搜索
                inputElement.dispatchEvent(new Event('change', { bubbles: true }));
            });

            // 鼠标悬停效果
            resultItem.addEventListener('mouseenter', () => {
                resultItem.style.backgroundColor = '#f3f4f6';
            });

            resultItem.addEventListener('mouseleave', () => {
                resultItem.style.backgroundColor = 'white';
            });

            container.appendChild(resultItem);
        });
    }

    /**
     * 设置实际容积显示值
     * @param {string|number} volume - 实际容积值
     */
    setActualVolume(volume) {
        // 查找当前页面中的容积显示元素
        const volumeValueElement = document.querySelector('.volume-value');
        if (volumeValueElement) {
            volumeValueElement.textContent = volume || '-';
        }
        
        // 同时尝试查找其他可能的容积显示元素
        const volumeDisplay = document.querySelector('[name="actual_volume"] .volume-value');
        if (volumeDisplay) {
            volumeDisplay.textContent = volume || '-';
        }

        // 触发容积更新事件，通知其他模块
        const volumeUpdateEvent = new CustomEvent('volumeUpdated', {
            detail: { volume: volume || '-' },
            bubbles: true
        });
        document.dispatchEvent(volumeUpdateEvent);
    }

    /**
     * 获取当前车厢号值
     * @returns {string} 当前车厢号
     */
    getCurrentCarriageNumber() {
        const carriageNumberInput = document.querySelector('input[name="carriage_number"]');
        return carriageNumberInput ? carriageNumberInput.value.trim() : '';
    }

    /**
     * 获取当前车牌号值
     * @returns {string} 当前车牌号
     */
    getCurrentLicensePlate() {
        const licensePlateInput = document.querySelector('input[name="license_plate"]');
        return licensePlateInput ? licensePlateInput.value.trim() : '';
    }

    /**
     * 智能设置容积 - 根据车厢号优先原则
     * @param {Object} vehicleInfo - 车辆信息对象
     */
    async setVolumeIntelligently(vehicleInfo) {
        // 获取当前表单中的车厢号和车牌号
        const currentCarriageNumber = this.getCurrentCarriageNumber();
        const currentLicensePlate = this.getCurrentLicensePlate();
        
        // 如果当前车厢号有值，优先使用车厢号查询容积
        if (currentCarriageNumber) {
            await this.fetchVolumeByCarriageNumber(currentCarriageNumber);
        } else {
            // 车厢号为空时，使用当前选择的车辆信息
            this.setActualVolume(vehicleInfo.actual_volume);
        }
    }

    /**
     * 根据车厢号获取容积
     * 使用现有的搜索API接口来获取车厢号对应的容积信息
     * @param {string} carriageNumber - 车厢号
     */
    async fetchVolumeByCarriageNumber(carriageNumber) {
        if (!carriageNumber) return;
        
        try {
            const response = await fetch(`/api/dispatch/vehicle-info/search?query=${encodeURIComponent(carriageNumber)}&type=carriage_number&limit=1`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.length > 0) {
                    const vehicle = result.data[0];
                    this.setActualVolume(vehicle.actual_volume);
                } else {
                    this.setActualVolume('-');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('根据车厢号获取容积失败:', error);
            this.setActualVolume('-');
        }
    }
}

// 添加全局样式
const styles = `
<style>
.vehicle-search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 1000;
    background: white;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    max-height: 200px;
    overflow-y: auto;
    display: none;
}

.vehicle-search-result-item {
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: 1px solid #f3f4f6;
    transition: background-color 0.2s;
}

.vehicle-search-result-item:hover {
    background-color: #f3f4f6;
}

.vehicle-search-result-item:last-child {
    border-bottom: none;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', styles);