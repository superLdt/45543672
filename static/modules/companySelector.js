/**
 * 承运公司选择框组件
 * 提供从数据库获取公司列表、搜索和选择功能
 * 使用ApiClient进行统一API调用
 */

// 公司数据缓存
let companyCache = [];
let currentSelectedCompany = '';

/**
 * 初始化公司选择框
 * @param {string} inputElementId - input元素的ID
 */
export async function initializeCompanySelector(inputElementId) {
    const inputElement = document.getElementById(inputElementId);
    if (!inputElement) {
        Debug.error('CompanySelector', `未找到ID为${inputElementId}的元素`);
        return;
    }

    try {
        // 获取公司数据
        await loadCompanies();
        
        // 填充选项
        populateOptions(inputElement);
        
        // 添加事件监听器
        addEventListeners(inputElement);
        
        Debug.log('CompanySelector', '公司选择框初始化完成');
    } catch (error) {
        ErrorHandler.handle(error, {
            title: '公司选择框初始化失败',
            fallbackMessage: '无法初始化公司选择框，请刷新页面重试'
        });
    }
}

/**
 * 从API加载公司数据
 * 使用companyApiClient进行统一API调用
 */
async function loadCompanies() {
    try {
        const companies = await companyApiClient.get('');
        companyCache = companies;
        Debug.log('CompanySelector', `成功加载 ${companies.length} 个公司数据`);
    } catch (error) {
        Debug.error('CompanySelector', '加载公司数据失败:', error);
        // 使用ApiClient的错误处理，这里不需要额外处理
        throw error;
    }
}

/**
 * 填充选择框选项
 * @param {HTMLElement} inputElement - input元素
 */
function populateOptions(inputElement) {
    // 创建datalist元素以支持输入联想
    const datalistId = inputElement.id + '-datalist';
    let datalist = document.getElementById(datalistId);
    if (!datalist) {
        datalist = document.createElement('datalist');
        datalist.id = datalistId;
        inputElement.parentNode.appendChild(datalist);
    } else {
        // 清空现有选项
        while (datalist.firstChild) {
            datalist.removeChild(datalist.firstChild);
        }
    }
    
    // 添加公司选项到datalist
    companyCache.forEach(company => {
        const option = document.createElement('option');
        option.value = company.name;
        datalist.appendChild(option);
    });
    
    // 关联input和datalist
    inputElement.setAttribute('list', datalistId);
}

/**
 * 添加事件监听器
 * @param {HTMLElement} inputElement - input元素
 */
function addEventListeners(inputElement) {
    // 处理用户输入事件
    inputElement.addEventListener('input', function(event) {
        handleUserInput(inputElement, event.target.value);
    });
    
    // 处理选择变化事件
    inputElement.addEventListener('change', function(event) {
        currentSelectedCompany = event.target.value;
    });
}

/**
 * 处理用户输入
 * @param {HTMLElement} inputElement - input元素
 * @param {string} inputValue - 输入值
 */
function handleUserInput(inputElement, inputValue) {
    // 查找完全匹配的公司（不区分大小写）
    const matchedCompany = companyCache.find(company => 
        company.name.toLowerCase() === inputValue.toLowerCase()
    );
    
    // 如果找到完全匹配的公司，更新当前选择
    if (matchedCompany) {
        currentSelectedCompany = matchedCompany.name;
    } else {
        // 如果没有找到完全匹配的公司，保留用户输入
        currentSelectedCompany = inputValue;
    }
}

/**
 * 获取当前选择的公司
 * @returns {string} 当前选择的公司名称
 */
export function getSelectedCompany() {
    return currentSelectedCompany;
}

/**
 * 验证公司选择
 * @returns {boolean} - 验证是否通过
 */
export function validateCompanySelection() {
    // 检查是否有输入的公司名称
    if (!currentSelectedCompany) {
        alert('请输入委办承运公司');
        return false;
    }
    
    // 检查输入的公司是否在缓存中存在
    const isValidCompany = companyCache.some(company => 
        company.name === currentSelectedCompany
    );
    
    if (!isValidCompany) {
        alert('请输入有效的委办承运公司');
        return false;
    }
    
    return true;
}