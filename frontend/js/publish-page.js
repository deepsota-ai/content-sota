// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 获取页面元素
    const folderList = document.getElementById('folder-list');
    const publishBtn = document.getElementById('publish-btn');
    const statusMessage = document.getElementById('status-message');
    const infoMessage = document.getElementById('info-message');
    const backBtn = document.getElementById('back-btn');

    let selectedFolder = null;

    // 返回首页按钮点击事件
    backBtn.addEventListener('click', function () {
        window.location.href = 'index.html';
    });

    // 初始化页面
    initPage();

    // 初始化页面
    function initPage() {
        showStatus('info', '正在加载文件夹列表...');

        // 获取文件夹列表
        fetchFolders();
    }

    // 获取文件夹列表
    async function fetchFolders() {
        try {
            const response = await fetch('/api/publish/folders');
            const data = await response.json();

            if (data.success) {
                renderFolderList(data.folders);
                showStatus('success', `成功加载 ${data.folders.length} 个文件夹`);
            } else {
                showStatus('error', `加载文件夹失败：${data.message}`);
            }
        } catch (error) {
            showStatus('error', `加载文件夹失败：${error.message}`);
        }
    }

    // 渲染文件夹列表
    function renderFolderList(folders) {
        folderList.innerHTML = '';

        folders.forEach(folder => {
            const folderItem = document.createElement('div');
            folderItem.className = 'folder-item';
            folderItem.dataset.folderName = folder.name;

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

            // 添加点击事件
            folderItem.addEventListener('click', function () {
                // 移除其他文件夹的选中状态
                document.querySelectorAll('.folder-item').forEach(item => {
                    item.classList.remove('selected');
                });

                // 添加当前文件夹的选中状态
                this.classList.add('selected');
                selectedFolder = this.dataset.folderName;

                // 启用发布按钮
                publishBtn.disabled = false;

                showStatus('info', `已选择文件夹：${selectedFolder}`);
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

        showStatus('info', `<div class="loading-text"><div class="loading"></div>正在发布内容...</div>`);
        publishBtn.disabled = true;

        try {
            const response = await fetch(`/api/publish/${selectedFolder}`, {
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
        }
    });

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