document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // 添加表单提交事件监听器
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        // 简单的表单验证
        if (!username) {
            showError(usernameInput, '请输入用户名');
            return;
        }

        if (!password) {
            showError(passwordInput, '请输入密码');
            return;
        }

        // 调用登录API
        loginUser(username, password);
    });

    // 输入框获取焦点时清除错误提示
    usernameInput.addEventListener('focus', function() {
        clearError(usernameInput);
    });

    passwordInput.addEventListener('focus', function() {
        clearError(passwordInput);
    });

    // 显示错误提示
    function showError(input, message) {
        clearError(input);
        const formGroup = input.parentElement;
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        errorElement.style.color = '#ff4d4f';
        errorElement.style.fontSize = '12px';
        errorElement.style.marginTop = '4px';
        formGroup.appendChild(errorElement);
        input.style.borderColor = '#ff4d4f';
    }

    // 清除错误提示
    function clearError(input) {
        const formGroup = input.parentElement;
        const errorElement = formGroup.querySelector('.error-message');
        if (errorElement) {
            formGroup.removeChild(errorElement);
        }
        input.style.borderColor = '';
    }

    // 调用登录API
    function loginUser(username, password) {
        // 显示加载状态
        const loginButton = loginForm.querySelector('.login-button');
        const originalButtonText = loginButton.textContent;
        loginButton.disabled = true;
        loginButton.textContent = '登录中...';

        // 发送登录请求
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username, password: password })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '登录失败');
                });
            }
            return response.json();
        })
        .then(data => {
            // 登录成功
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                window.location.href = '/dashboard';
            }
        })
        .catch(error => {
            // 登录失败
            showError(passwordInput, error.message);
        })
        .finally(() => {
            // 恢复按钮状态
            loginButton.disabled = false;
            loginButton.textContent = originalButtonText;
        });
    }
});