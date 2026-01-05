// 裁剪子页面JavaScript

// 页面加载完成事件
window.addEventListener('DOMContentLoaded', () => {
    const backBtn = document.getElementById('back-btn');
    const backToMainBtn = document.getElementById('back-to-main-btn');

    // 返回首页按钮点击事件
    backBtn.addEventListener('click', () => {
        window.location.href = '../index.html';
    });

    // 返回主功能按钮点击事件
    backToMainBtn.addEventListener('click', () => {
        window.location.href = '../cover-generator.html';
    });

    // 进入蒙版功能按钮点击事件
    const goToMaskBtn = document.getElementById('go-to-mask-btn');
    if (goToMaskBtn) {
        goToMaskBtn.addEventListener('click', () => {
            window.location.href = 'mask-subpage.html';
        });
    }

    // 进入文字编辑功能按钮点击事件
    const goToTextEditBtn = document.getElementById('go-to-text-edit-btn');
    if (goToTextEditBtn) {
        goToTextEditBtn.addEventListener('click', () => {
            window.location.href = 'text-edit-subpage.html';
        });
    }

    // 生成裁剪图片按钮点击事件
    const cropBtn = document.getElementById('crop-btn');
    if (cropBtn) {
        cropBtn.addEventListener('click', () => {
            // 获取所有图片名称
            const imageItems = document.querySelectorAll('.image-item');
            if (!imageItems || imageItems.length === 0) {
                showNotification('没有找到图片', 'error');
                return;
            }

            // 收集所有图片名称
            const imageNames = Array.from(imageItems).map(item => item.dataset.imageName);

            // 调用生成裁剪图片API，固定使用3:4比例
            generateCroppedImage(imageNames);
        });
    }

    // 加载图片列表
    loadImageList();

    // 加载图片列表
    function loadImageList() {
        fetch('/api/get_mask_images')
            .then(response => response.json())
            .then(data => {
                if (data.images && data.images.length > 0) {
                    const imageList = document.getElementById('image-list');
                    if (imageList) {
                        // 清空现有列表
                        imageList.innerHTML = '';

                        // 遍历图片列表，创建图片项
                        data.images.forEach(imageName => {
                            const imageItem = document.createElement('div');
                            imageItem.className = 'image-item';
                            imageItem.dataset.imageName = imageName;

                            const imageLabel = document.createElement('div');
                            imageLabel.className = 'image-label';
                            imageLabel.textContent = imageName;

                            imageItem.appendChild(imageLabel);

                            // 添加点击选择事件
                            imageItem.addEventListener('click', () => {
                                // 移除其他图片的选中状态
                                document.querySelectorAll('.image-item').forEach(item => {
                                    item.classList.remove('selected');
                                });

                                // 添加当前图片的选中状态
                                imageItem.classList.add('selected');
                            });

                            imageList.appendChild(imageItem);
                        });

                        // 默认选中第一张图片
                        const firstImageItem = imageList.querySelector('.image-item');
                        if (firstImageItem) {
                            firstImageItem.classList.add('selected');
                        }
                    }
                } else {
                    showNotification('没有找到图片', 'info');
                }
            })
            .catch(error => {
                console.error('加载图片列表失败:', error);
                showNotification('加载图片列表失败', 'error');
            });
    }

    // 生成裁剪图片
    function generateCroppedImage(imageNames) {
        showNotification('正在生成裁剪图片...', 'info');

        // 获取结果列表元素
        const resultList = document.getElementById('crop-result-list');
        // 清空结果列表
        if (resultList) {
            resultList.innerHTML = '';
        }

        // 调用生成裁剪API，固定使用3:4比例
        fetch('/api/generate-cropped-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                images: imageNames,
                aspect_ratio: '4:3' // 固定使用3:4比例
            })
        })
            .then(response => response.json())
            .then(result => {
                if (result.results && result.results.length > 0) {
                    // 检查是否有生成成功的结果
                    const successResults = result.results.filter(item => item.success);
                    if (successResults.length > 0) {
                        showNotification(`成功生成 ${successResults.length} 个裁剪图片`, 'success');

                        // 在结果列表中显示所有成功生成的裁剪图片
                        if (resultList) {
                            successResults.forEach(item => {
                                const resultItem = document.createElement('div');
                                resultItem.className = 'crop-result-item';

                                // 创建图片预览
                                const img = document.createElement('img');
                                // 根据图片名称构建图片路径，直接使用文件路径访问
                                const imageName = item.image;
                                img.src = `/data/coverGeneration/cover/crop/${imageName}`;
                                img.alt = item.image;

                                // 仅添加图片到结果项
                                resultItem.appendChild(img);

                                resultList.appendChild(resultItem);
                            });
                        }
                    } else {
                        // 所有生成都失败了
                        const firstError = result.results[0].error || '未知错误';
                        showNotification('裁剪图片生成失败: ' + firstError, 'error');

                        // 在结果列表中显示错误
                        if (resultList) {
                            const errorItem = document.createElement('div');
                            errorItem.className = 'crop-result-item';
                            errorItem.textContent = `❌ 生成失败: ${firstError}`;
                            resultList.appendChild(errorItem);
                        }
                    }
                } else {
                    showNotification('裁剪图片生成失败', 'error');

                    // 在结果列表中显示无结果
                    if (resultList) {
                        const noResultItem = document.createElement('div');
                        noResultItem.className = 'crop-result-item';
                        noResultItem.textContent = '❌ 没有生成任何裁剪图片';
                        resultList.appendChild(noResultItem);
                    }
                }
            })
            .catch(error => {
                console.error('生成裁剪图片失败:', error);
                showNotification('生成裁剪图片失败', 'error');

                // 在结果列表中显示网络错误
                const resultList = document.getElementById('crop-result-list');
                if (resultList) {
                    const errorItem = document.createElement('div');
                    errorItem.className = 'crop-result-item';
                    errorItem.textContent = '❌ 网络错误，请稍后重试';
                    resultList.appendChild(errorItem);
                }
            });
    }

    // 显示通知
    function showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // 添加样式
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            background-color: ${type === 'info' ? '#4a90e2' : type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#f39c12'};
            color: white;
            font-size: 16px;
            font-weight: 500;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateY(-20px);
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 显示动画
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);

        // 自动隐藏
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
});