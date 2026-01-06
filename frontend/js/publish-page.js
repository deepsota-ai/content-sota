// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 获取页面元素
    const folderList = document.getElementById('folder-list');
    const publishBtn = document.getElementById('publish-btn');
    const statusMessage = document.getElementById('status-message');
    // const infoMessage = document.getElementById('info-message'); // Unused
    const backBtn = document.getElementById('back-btn');

    // 当前状态
    let currentLevel = 'root'; // 'root' (日期列表) 或 'date' (素材列表)
    let currentDateFolder = null; // 当前选中的日期文件夹名
    let selectedFolder = null;

    // 返回首页按钮点击事件 - 初始绑定
    backBtn.addEventListener('click', function () {
        window.location.href = 'index.html';
    });

    // 初始化页面
    initPage();

    // 初始化页面
    function initPage() {
        showStatus('info', '正在加载发布列表...');
        fetchFolders(); // Initial fetch for root level (date folders)
    }

    // 获取文件夹列表
    // dateParam: 可选，日期文件夹名
    async function fetchFolders(dateParam = null) {
        try {
            let url = '/api/publish/folders';
            if (dateParam) {
                url += `?date=${dateParam}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                renderFolderList(data.folders, dateParam);
                if (dateParam) {
                    showStatus('success', `已进入 ${dateParam}，共 ${data.folders.length} 个素材`);
                } else {
                    showStatus('success', `加载完成，共 ${data.folders.length} 个日期归档`);
                }
                updateBreadcrumb(dateParam);
            } else {
                showStatus('error', `加载失败：${data.message}`);
            }
        } catch (error) {
            showStatus('error', `加载失败：${error.message}`);
        }
    }

    // 更新面包屑/标题
    function updateBreadcrumb(date) {
        const titleEl = document.querySelector('header h1');
        if (titleEl) {
            const currentBackBtn = document.getElementById('back-btn');

            if (date) {
                titleEl.innerHTML = `<i class="fas fa-pencil-alt"></i> 内容创作者助手 > ${date}`;

                // 重置 backBtn 元素以清除所有监听器
                if (currentBackBtn) {
                    const newBackBtn = currentBackBtn.cloneNode(true);
                    currentBackBtn.parentNode.replaceChild(newBackBtn, currentBackBtn);

                    newBackBtn.innerHTML = '<i class="fas fa-arrow-left"></i> 返回列表';
                    newBackBtn.addEventListener('click', function () {
                        currentLevel = 'root';
                        currentDateFolder = null;
                        selectedFolder = null;
                        fetchFolders(null);
                    });
                }

            } else {
                titleEl.innerHTML = `<i class="fas fa-pencil-alt"></i> 内容创作者助手`;

                if (currentBackBtn) {
                    const newBackBtn = currentBackBtn.cloneNode(true);
                    currentBackBtn.parentNode.replaceChild(newBackBtn, currentBackBtn);

                    newBackBtn.innerHTML = '<i class="fas fa-home"></i> 返回首页';
                    newBackBtn.addEventListener('click', function () {
                        window.location.href = 'index.html';
                    });
                }
            }
        }
    }

    // 渲染文件夹列表
    function renderFolderList(folders, isDateLevel) {
        folderList.innerHTML = '';

        // 每次渲染列表，先清空选中状态
        selectedFolder = null;
        publishBtn.disabled = true;
        const xhsPerfectBtn = document.getElementById('xhs-perfect-btn');
        if (xhsPerfectBtn) xhsPerfectBtn.disabled = true;

        if (folders.length === 0) {
            folderList.innerHTML = '<div class="empty-state">暂无内容</div>';
            return;
        }

        folders.forEach(folder => {
            const folderItem = document.createElement('div');
            folderItem.className = 'folder-item';

            // 如果是日期层级，name就是日期（如 2026.1.6）
            // 如果是素材层级，name就是素材名（如 素材_1）
            folderItem.dataset.folderName = folder.name;

            // 实际上这里的 isDateLevel 是传入的 dateParam，不为空则是素材列表(date level)，为空则是root
            const isMaterialList = !!isDateLevel;

            if (isMaterialList) {
                // 素材列表展示
                folderItem.innerHTML = `
                    <i class="fas fa-folder"></i>
                    <div class="folder-main">
                        <h3>${folder.name}</h3>
                        <div class="folder-title">${folder.title || '无标题'}</div>
                    </div>
                    <div class="folder-info">
                        ${folder.fileCount} 个文件
                    </div>
                `;
            } else {
                // 日期列表展示
                folderItem.innerHTML = `
                    <i class="fas fa-calendar-alt"></i>
                    <div class="folder-main">
                        <h3>${folder.name}</h3>
                        <div class="folder-title">点击查看详情</div>
                    </div>
                    <div class="folder-info">
                        ${folder.fileCount} 个素材
                    </div>
                `;
            }

            // 添加点击事件
            folderItem.addEventListener('click', function () {
                if (!isMaterialList) {
                    // === 日期层级：点击进入下一级 ===
                    currentLevel = 'date';
                    currentDateFolder = this.dataset.folderName;
                    fetchFolders(currentDateFolder);
                } else {
                    // === 素材层级：点击选中 ===
                    // 移除其他文件夹的选中状态
                    document.querySelectorAll('.folder-item').forEach(item => {
                        item.classList.remove('selected');
                    });

                    // 添加当前文件夹的选中状态
                    this.classList.add('selected');

                    // 构造完整的发布路径：日期/素材名
                    // 后端 publish 接口将接收这个路径
                    selectedFolder = `${currentDateFolder}/${this.dataset.folderName}`;

                    // 启用发布按钮
                    publishBtn.disabled = false;
                    if (xhsPerfectBtn) xhsPerfectBtn.disabled = false;

                    showStatus('info', `已选择：${selectedFolder}`);
                }
            });

            folderList.appendChild(folderItem);
        });
    }

    // 发布按钮点击事件
    publishBtn.addEventListener('click', async function () {
        if (!selectedFolder) {
            showStatus('error', '请先选择要发布的文件夹');
            return;
        }

        const xhsPerfectBtn = document.getElementById('xhs-perfect-btn');
        showStatus('info', `<div class="loading-text"><div class="loading"></div>正在发布内容...</div>`);
        publishBtn.disabled = true;
        if (xhsPerfectBtn) xhsPerfectBtn.disabled = true;

        try {
            // 使用 encodeURIComponent 编码路径
            // 后端 app.py 需要配置 <path:folder_name> 来正确接收包含斜杠的路径
            const response = await fetch(`/api/publish/${encodeURIComponent(selectedFolder)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                showStatus('success', `发布成功：${data.message}`);
            } else {
                showStatus('error', `发布失败：${data.message}`);
            }
        } catch (error) {
            showStatus('error', `发布失败：${error.message}`);
        } finally {
            publishBtn.disabled = false;
            if (xhsPerfectBtn) xhsPerfectBtn.disabled = false;
        }
    });

    // 小红书完善按钮点击事件
    const xhsPerfectBtn = document.getElementById('xhs-perfect-btn');
    if (xhsPerfectBtn) {
        xhsPerfectBtn.addEventListener('click', async function () {
            if (!selectedFolder) {
                showStatus('error', '请先选择要发布的文件夹');
                return;
            }

            showStatus('info', `<div class="loading-text"><div class="loading"></div>正在完善小红书封面...</div>`);
            publishBtn.disabled = true;
            xhsPerfectBtn.disabled = true;

            try {
                const response = await fetch(`/api/publish/xhs_perfect/${encodeURIComponent(selectedFolder)}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const data = await response.json();

                if (data.success) {
                    showStatus('success', `小红书封面指令：${data.message}`);
                } else {
                    showStatus('error', `操作失败：${data.message}`);
                }
            } catch (error) {
                showStatus('error', `网络错误：${error.message}`);
            } finally {
                publishBtn.disabled = false;
                xhsPerfectBtn.disabled = false;
            }
        });
    }

    // 显示状态消息
    function showStatus(type, message) {
        statusMessage.className = `status-message ${type}`;
        statusMessage.innerHTML = message;
        statusMessage.classList.add('show');

        // 如果是info类型的消息，5秒后自动隐藏
        if (type === 'info') {
            setTimeout(() => {
                statusMessage.classList.remove('show');
            }, 5000);
        }
    }
});