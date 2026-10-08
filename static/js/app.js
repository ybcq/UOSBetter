/**
 * UOSBetter 2.0 Frontend JavaScript
 */

const API_BASE = '';
const SSE_URL = '/api/logs';
const TABS_URL = '/api/tabs';
const ACTION_URL = '/api/action';

let sseConnection = null;
let exeHandlerModal = null;
let errorModal = null;
let confirmModal = null;
let logoutModal = null;
let successModal = null;
let pendingAction = null;
let pendingParams = null;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    connectSSE();
    setupBrightnessSlider();
    autoCollapseLogPanel();
    
    const exeModalEl = document.getElementById('exeHandlerModal');
    if (exeModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        exeHandlerModal = new bootstrap.Modal(exeModalEl);
    }
    
    const errorModalEl = document.getElementById('errorModal');
    if (errorModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        errorModal = new bootstrap.Modal(errorModalEl);
    }
    
    const confirmModalEl = document.getElementById('confirmModal');
    if (confirmModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        confirmModal = new bootstrap.Modal(confirmModalEl);
    }
    
    const logoutModalEl = document.getElementById('logoutModal');
    if (logoutModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        logoutModal = new bootstrap.Modal(logoutModalEl);
    }
    
    const successModalEl = document.getElementById('successModal');
    if (successModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        successModal = new bootstrap.Modal(successModalEl);
    }
    
    // 亮度滑块实时更新显示
    const slider = document.getElementById('brightnessSlider');
    if (slider) {
        slider.addEventListener('input', () => {
            document.getElementById('brightnessValue').textContent = slider.value + '%';
        });
    }
    
    window.addEventListener('resize', autoCollapseLogPanel);
});

// ==================== 日志面板折叠 ====================
function toggleLogPanel() {
    const panel = document.getElementById('logPanel');
    const btn = document.getElementById('logToggleBtn');
    if (panel) {
        panel.classList.toggle('collapsed');
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) {
                if (panel.classList.contains('collapsed')) {
                    icon.className = 'bi bi-chevron-double-left';
                } else {
                    icon.className = 'bi bi-chevron-double-right';
                }
            }
        }
    }
}

function autoCollapseLogPanel() {
    const panel = document.getElementById('logPanel');
    if (!panel) return;
    if (window.innerWidth < 900 && !panel.classList.contains('collapsed')) {
        panel.classList.add('collapsed');
        const btn = document.getElementById('logToggleBtn');
        if (btn) {
            const icon = btn.querySelector('i');
            if (icon) icon.className = 'bi bi-chevron-double-left';
        }
    }
}

// ==================== SSE 日志连接 ====================
function connectSSE() {
    if (sseConnection) {
        sseConnection.close();
    }
    
    sseConnection = new EventSource(SSE_URL);
    
    sseConnection.onopen = () => {
        appendLog('系统连接成功');
    };
    
    sseConnection.onmessage = (event) => {
        appendLog(event.data);
    };
    
    sseConnection.onerror = () => {
        appendLog('连接中断，尝试重连...');
        setTimeout(connectSSE, 3000);
    };
}

function appendLog(message) {
    const container = document.getElementById('logContent');
    if (!container) return;
    
    const line = document.createElement('div');
    line.className = 'log-line';
    line.textContent = message;
    container.appendChild(line);
    container.scrollTop = container.scrollHeight;
    
    // 限制日志条数（保留最近 1000 条，避免页面卡顿）
    while (container.children.length > 1000) {
        container.removeChild(container.firstChild);
    }
}

function clearLogs() {
    const container = document.getElementById('logContent');
    if (container) {
        container.innerHTML = '<div class="log-line">日志已清空</div>';
    }
}

function showErrorModal(message) {
    const msgEl = document.getElementById('errorModalMessage');
    if (msgEl) msgEl.textContent = message;
    if (errorModal) errorModal.show();
}

function showConfirmModal(message, onConfirm) {
    const msgEl = document.getElementById('confirmModalMessage');
    if (msgEl) msgEl.textContent = message;
    
    const confirmBtn = document.getElementById('confirmModalConfirmBtn');
    if (confirmBtn) {
        // 移除之前的事件监听器
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        
        newBtn.addEventListener('click', () => {
            if (confirmModal) confirmModal.hide();
            onConfirm();
        });
    }
    
    if (confirmModal) confirmModal.show();
}

function showLogoutModal(message) {
    const msgEl = document.getElementById('logoutModalMessage');
    if (msgEl) msgEl.textContent = message;
    if (logoutModal) logoutModal.show();
}

function showSuccessModal(message) {
    const msgEl = document.getElementById('successModalMessage');
    if (msgEl) msgEl.textContent = message;
    if (successModal) successModal.show();
}

function doLogout() {
    if (logoutModal) logoutModal.hide();
    // 使用 pkexec 执行注销命令
    fetch(ACTION_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'logout_user', params: {} })
    }).then(() => {
        appendLog('正在注销...');
    }).catch(() => {
        appendLog('注销失败，请手动注销');
    });
}

// ==================== API 调用 ====================
async function doAction(action, params = {}) {
    // 定义需要确认的破坏性操作
    const confirmActions = {
        'uninstall_package': '确定要卸载此软件包吗？此操作不可撤销。',
        'unset_wine_c': '确定要卸载 Wine C 盘吗？',
        'unset_win_disk': '确定要卸载 Windows 风格磁盘吗？',
        'restore_default_fm': '确定要还原默认文件管理器吗？',
        'unlock_kernel': '确定要解锁内核版本吗？这可能导致系统更新时自动更换内核。',
        'uninstall_spark_store': '确定要卸载星火应用商店吗？',
        'remove_flat_store': '确定要移除 Flatpak 商店图标吗？',
        'remove_appimage_store': '确定要移除 AppImage 商店图标吗？',
    };
    
    // 检查是否需要确认
    if (confirmActions[action]) {
        showConfirmModal(confirmActions[action], () => {
            executeAction(action, params);
        });
        return { success: false, message: '等待用户确认...' };
    }
    
    return executeAction(action, params);
}

async function executeAction(action, params = {}) {
    appendLog(`> 执行: ${action}`);
    
    try {
        const response = await fetch(ACTION_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, params })
        });
        
        const result = await response.json();
        
        if (result.success) {
            appendLog(`✓ ${result.message || '执行成功'}`);
            
            // 检查是否需要注销生效
            if (result.logout_required) {
                showLogoutModal(result.message + '\n\n建议立即注销重新登录以使更改生效。');
            } else {
                showSuccessModal(result.message || '执行成功');
            }
        } else {
            appendLog(`✗ ${result.message || '执行失败'}`);
            showErrorModal(result.message || '执行失败');
        }
        
        return result;
    } catch (error) {
        appendLog(`✗ 请求失败: ${error.message}`);
        showErrorModal(`请求失败: ${error.message}`);
        return { success: false, message: error.message };
    }
}

// ==================== 文件与图标选择 (使用 easygui) ====================
async function pickFile(inputId, filter = '') {
    try {
        const res = await fetch(`/api/pick-file?filter=${encodeURIComponent(filter)}`);
        const data = await res.json();
        if (data.success && data.data) {
            document.getElementById(inputId).value = data.data.path;
        }
        // 如果用户取消选择，则不做任何事（保持原值）
    } catch (e) {
        showErrorModal(`网络错误: ${e.message}`);
    }
}

async function pickIcon(inputId) {
    try {
        const res = await fetch('/api/pick-icon');
        const data = await res.json();
        if (data.success && data.data) {
            document.getElementById(inputId).value = data.data.path;
        }
        // 如果用户取消选择，则不做任何事（保持原值）
    } catch (e) {
        showErrorModal(`网络错误: ${e.message}`);
    }
}

// ==================== EXE 处理器 ====================
function showExeHandlerModal() {
    if (exeHandlerModal) {
        exeHandlerModal.show();
        return;
    }
    // 回退：如果初始化失败，尝试用 data-api 打开
    const el = document.getElementById('exeHandlerModal');
    if (el && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        new bootstrap.Modal(el).show();
    }
}

async function chooseExeHandler(wineType) {
    if (exeHandlerModal) {
        exeHandlerModal.hide();
    } else {
        const el = document.getElementById('exeHandlerModal');
        if (el && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            bootstrap.Modal.getInstance(el)?.hide();
        }
    }
    await doAction('set_exe_handler_with_wine', { wine_type: wineType });
}

// ==================== 快捷方式管理 ====================
function createShortcut() {
    const locationInput = document.querySelector('input[name="sc_location"]:checked');
    const params = {
        name: document.getElementById('sc_name').value,
        exec_path: document.getElementById('sc_exec').value,
        icon_path: document.getElementById('sc_icon').value,
        args: document.getElementById('sc_args').value,
        sudo: document.getElementById('sc_sudo').checked,
        location: locationInput ? locationInput.value : 'desktop'
    };
    
    doAction('create_shortcut', params);
}

function installSelectedFM() {
    const selected = document.querySelector('input[name="fm_type"]:checked');
    if (!selected) {
        appendLog('请先选择要安装的文件管理器');
        return;
    }
    const fmType = selected.id.replace('fm_', '');
    doAction('install_tree_fm', { fm_type: fmType });
}

function setSelectedFMDefault() {
    const selected = document.querySelector('input[name="fm_type"]:checked');
    if (!selected) {
        appendLog('请先选择要设为默认的文件管理器');
        return;
    }
    const fmType = selected.id.replace('fm_', '');
    doAction('set_default_fm', { fm_type: fmType });
}

function createContextMenu() {
    const params = {
        name: document.getElementById('cm_name').value,
        command: document.getElementById('cm_command').value,
        icon_path: document.getElementById('cm_icon').value,
        menu_type: document.getElementById('cm_file').checked ? 'file' : 'directory',
        location: document.getElementById('cm_user').checked ? 'user' : 'system'
    };
    
    doAction('create_context_menu', params);
}

function manageShortcuts(location) {
    doAction('manage_app_icons', { location });
}

function manageContextMenus() {
    doAction('manage_context_menus');
}

// ==================== 服务管理 ====================
function createService() {
    const name = document.getElementById('sv_name').value.trim();
    const command = document.getElementById('sv_command').value.trim();
    const restart = document.getElementById('sv_restart').value;
    
    if (!name || !command) {
        showErrorModal('服务名称和执行命令不能为空');
        return;
    }
    
    const params = { name, command, restart };
    doAction('create_service', params);
}

// ==================== 软件包管理 ====================
function installPackage() {
    const params = {
        path: document.getElementById('pkg_path').value,
        isolate: document.getElementById('pkg_isolate').checked
    };
    
    doAction('install_package', params);
}

function uninstallPackage() {
    const params = {
        path: document.getElementById('pkg_path').value,
        isolate: document.getElementById('pkg_isolate').checked
    };
    
    doAction('uninstall_package', params);
}

// ==================== 亮度调节 ====================
function setBrightness() {
    const brightness = document.getElementById('brightnessSlider').value;
    doAction('set_brightness', { brightness: parseInt(brightness) });
}

function setupBrightnessSlider() {
    // 已通过 addEventListener 设置
}

// ==================== 工具函数 ====================
function showToast(message, type = 'info') {
    appendLog(`[${type}] ${message}`);
}