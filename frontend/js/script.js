// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    // 导航按钮点击事件
    const navBtns = document.querySelectorAll('.nav-btn');
    // 中央按钮点击事件
    const centralBtns = document.querySelectorAll('.central-btn');
    const confirmModal = document.getElementById('confirm-modal');
    const closeModal = document.getElementById('close-modal');
    const cancelClean = document.getElementById('cancel-clean');
    const confirmClean = document.getElementById('confirm-clean');
    const successToast = document.getElementById('success-toast');

    // 由于导航栏按钮已删除，不再需要导航按钮事件监听

    // 中央按钮点击事件
    centralBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            // 根据按钮ID执行相应操作
            const btnId = this.id;

            // 执行按钮操作
            handleButtonAction(btnId);
        });
    });

    // 处理按钮操作
    function handleButtonAction(btnId) {
        // 中央按钮ID映射
        const centralBtnMap = {
            'cleanFiles': 'clean',
            'generateContent': 'content',
            'generateCover': 'cover',
            'publishContent': 'publish',
            'generateAd': 'ad'
        };

        // 确定按钮类型
        const actionType = centralBtnMap[btnId];

        switch (actionType) {
            case 'clean':
                // 显示清理确认对话框
                showModal();
                break;
            case 'content':
                // 跳转到内容生成页
                window.location.href = 'content-generator.html';
                break;
            case 'cover':
                // 跳转到封面生成页
                window.location.href = 'cover-generator.html';
                break;
            case 'publish':
                // 跳转到发布完善页
                window.location.href = 'publish-page.html';
                break;
            case 'ad':
                // 跳转到广告页
                console.log('跳转到广告页');
                break;
        }
    };

    // 显示模态框
    function showModal() {
        confirmModal.classList.add('show');
    }

    // 隐藏模态框
    function hideModal() {
        confirmModal.classList.remove('show');
    }

    // 关闭模态框事件
    closeModal.addEventListener('click', hideModal);
    cancelClean.addEventListener('click', hideModal);

    // 点击模态框外部关闭模态框
    window.addEventListener('click', function (e) {
        if (e.target === confirmModal) {
            hideModal();
        }
    });

    // 确认清理事件
    confirmClean.addEventListener('click', async function () {
        // 获取选中的目标
        const targets = [];
        const checkboxes = document.querySelectorAll('input[name="clean-target"]:checked');
        checkboxes.forEach(cb => {
            targets.push(cb.value);
        });

        if (targets.length === 0) {
            alert('请至少选择一项要清理的内容');
            return;
        }

        const originalText = confirmClean.innerHTML;
        confirmClean.disabled = true;
        confirmClean.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 清理中...';

        try {
            const response = await fetch('/api/clean-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ targets: targets })
            });
            const result = await response.json();

            if (result.success) {
                console.log('清理结果:', result.data);
                hideModal();
                showSuccessToast();
            } else {
                alert('清理失败: ' + result.error);
            }
        } catch (error) {
            console.error('清理请求异常:', error);
            alert('清理请求发生错误');
        } finally {
            confirmClean.disabled = false;
            confirmClean.innerHTML = originalText;
        }
    });

    // 显示成功提示
    function showSuccessToast() {
        successToast.classList.add('show');

        // 3秒后自动隐藏提示
        setTimeout(() => {
            successToast.classList.remove('show');
        }, 3000);
    }

    // 添加键盘事件支持
    document.addEventListener('keydown', function (e) {
        // ESC键关闭模态框
        if (e.key === 'Escape' && confirmModal.classList.contains('show')) {
            hideModal();
        }
    });

    // 初始化页面
    console.log('导航页加载完成');
});