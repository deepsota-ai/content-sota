// 生成标题子页面JavaScript

// 页面加载完成事件
window.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const backBtn = document.getElementById('back-btn');
    const mainBtn = document.getElementById('main-btn');

    // 返回按钮点击事件
    backBtn.addEventListener('click', () => {
        window.location.href = '../index.html';
    });

    // 返回主页面按钮点击事件
    mainBtn.addEventListener('click', () => {
        window.location.href = '../content-generator.html';
    });

    // 内容容器
    const materialCarousel = document.getElementById('material-carousel');
    const resultCarousel = document.getElementById('result-carousel');
    const filterGrid = document.getElementById('filter-grid');
    const organizeBtn = document.getElementById('organize-btn');

    // 初始禁用整理按钮
    organizeBtn.disabled = true;

    // 内容数据
    let materials = [];
    let generatedContents = [];

    // 页面加载时动态加载素材和模型列表
    loadMaterialsFromAPI();
    loadModels();

    // 生成按钮点击事件
    generateBtn.addEventListener('click', () => {
        // 调用API生成标题
        generateTitleFromAPI();
    });

    // 整理按钮点击事件
    organizeBtn.addEventListener('click', () => {
        // 调用整理功能
        organizeContent();
    });

    // 加载模型列表
    function loadModels() {
        const modelSelect = document.getElementById('model-select');
        if (!modelSelect) return;
        fetch('/api/models')
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const saved = localStorage.getItem('selectedModel');
                    modelSelect.innerHTML = data.models.map(m =>
                        `<option value="${m.id}" ${m.id === saved ? 'selected' : ''}>${m.name}</option>`
                    ).join('');
                }
            })
            .catch(() => {
                modelSelect.innerHTML = '<option value="">获取模型失败</option>';
            });
        modelSelect.addEventListener('change', () => {
            localStorage.setItem('selectedModel', modelSelect.value);
        });
    }

    // 从API加载素材函数
    function loadMaterialsFromAPI() {
        // 显示加载状态
        showLoading('material-carousel', '正在加载素材...');

        // 调用API获取素材
        fetch('/api/load-material')
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 将API返回的素材块转换为素材数组
                    materials = data.blocks.map((block, index) => ({
                        id: index + 1,
                        title: `素材 ${index + 1}`,
                        content: block.substring(0, 50) + '...', // 截取前50个字符作为预览
                        fullContent: block, // 保存完整内容用于生成
                        // 添加筛选字段
                        filterTitle: '',
                        filterDesc: ''
                    }));

                    // 生成素材卡片
                    renderMaterialCards();
                } else {
                    showError('material-carousel', data.error);
                }
            })
            .catch(error => {
                showError('material-carousel', `加载素材失败: ${error.message}`);
            });
    }

    // 从API生成标题函数
    function generateTitleFromAPI() {
        // 禁用按钮，显示加载状态
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';

        // 显示结果加载状态
        showLoading('result-carousel', '正在生成标题...');

        // 准备请求数据
        const modelSelect = document.getElementById('model-select');
        const requestData = {
            material_contents: materials.map(m => m.fullContent),
            generate_type: "title",
            model_name: modelSelect ? modelSelect.value : null
        };

        // 调用实际的内容生成API
        fetch('/api/generate-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // 创建生成结果对象，包含所有素材的生成结果
                    generatedContents = data.data.results.map((result, index) => ({
                        materialIndex: result.material_index,
                        titles: result.titles || [],
                        error: result.error,
                        id: Date.now() + index
                    }));

                    // 更新结果显示
                    renderResults();
                    // 生成筛选结果模块
                    renderFilterModules();
                    // 启用整理按钮
                    organizeBtn.disabled = false;
                } else {
                    showError('result-carousel', data.error);
                }
            })
            .catch(error => {
                showError('result-carousel', `生成标题失败: ${error.message}`);
            })
            .finally(() => {
                // 恢复按钮状态
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> 生成标题';
            });
    }

    // 显示加载状态
    function showLoading(elementSelector, message) {
        const element = document.querySelector(`#${elementSelector}`) || document.querySelector(elementSelector);
        if (element) {
            element.innerHTML = `
                <div class="loading-state">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    // 显示错误信息
    function showError(elementSelector, message) {
        const element = document.querySelector(`#${elementSelector}`) || document.querySelector(elementSelector);
        if (element) {
            element.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    // 生成素材卡片
    function renderMaterialCards() {
        materialCarousel.innerHTML = '';

        materials.forEach(material => {
            const card = document.createElement('div');
            card.className = 'material-card';
            card.innerHTML = `
                <div class="material-info">
                    <h3>${material.title}</h3>
                    <p class="material-preview-text">${material.content}</p>
                </div>
            `;
            materialCarousel.appendChild(card);
        });
    }

    // 渲染生成结果
    function renderResults() {
        // 如果没有结果，显示默认提示
        if (generatedContents.length === 0) {
            resultCarousel.innerHTML = `
                <div class="result-card" id="content-result">
                    <h3 class="result-card-title">
                        生成的标题
                    </h3>
                    <div class="result-content">
                        <div class="result-title" id="title-result">
                            <p class="placeholder">点击"生成标题"按钮获取生成的标题</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        // 清空结果网格
        resultCarousel.innerHTML = '';

        // 生成结果卡片
        generatedContents.forEach(content => {
            const card = document.createElement('div');
            card.className = 'result-card';

            // 检查是否有错误
            if (content.error) {
                card.innerHTML = `
                    <h3 class="result-card-title">
                        素材 ${content.materialIndex} - 生成失败
                    </h3>
                    <div class="result-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>${content.error}</p>
                    </div>
                `;
            } else {
                // 合并标题为一个连续的文本，并添加编号，序号之间使用换行
                const mergedTitles = content.titles.map((title, index) => `${index + 1}. ${title}`).join('\n');

                // 生成标题HTML
                const titlesHtml = `
                    <div class="result-item">
                        <p class="item-content">${mergedTitles}</p>
                    </div>
                `;

                card.innerHTML = `
                    <h3 class="result-card-title">
                        素材 ${content.materialIndex} 生成的标题
                    </h3>
                    <div class="result-content">
                        <div class="result-title">
                            <h4>标题</h4>
                            <div class="result-list">${titlesHtml}</div>
                        </div>
                    </div>
                `;
            }

            resultCarousel.appendChild(card);
        });
    }

    // 渲染筛选结果模块
    function renderFilterModules() {
        // 清空筛选网格
        filterGrid.innerHTML = '';

        // 为每个素材生成一个筛选模块
        generatedContents.forEach((content, index) => {
            const card = document.createElement('div');
            card.className = 'filter-card';
            card.innerHTML = `
                <h3>素材 ${content.materialIndex} 筛选结果</h3>
                <div class="filter-field">
                    <label for="title-${index}">标题 (title)</label>
                    <textarea id="title-${index}" placeholder="请输入标题（支持多行）" class="filter-textarea"></textarea>
                </div>
                <div class="filter-field">
                    <label for="desc-${index}">描述 (desc)</label>
                    <input type="text" id="desc-${index}" placeholder="请输入描述" class="filter-input">
                </div>
            `;
            filterGrid.appendChild(card);

            // 为输入框添加事件监听，保存输入值到materials数组
            const titleInput = card.querySelector(`#title-${index}`);
            const descInput = card.querySelector(`#desc-${index}`);

            titleInput.addEventListener('input', (e) => {
                materials[content.materialIndex - 1].filterTitle = e.target.value;
            });

            descInput.addEventListener('input', (e) => {
                materials[content.materialIndex - 1].filterDesc = e.target.value;
            });
        });
    }

    // 整理内容函数
    function organizeContent() {
        // 禁用整理按钮，显示加载状态
        organizeBtn.disabled = true;
        organizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 整理中...';

        // 准备请求数据
        const requestData = {
            materials: materials.map(material => ({
                title: material.filterTitle,
                desc: material.filterDesc,
                fullContent: material.fullContent
            }))
        };

        // 调用整理API
        fetch('/api/organize-content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    organizeBtn.innerHTML = '<i class="fas fa-check"></i> 已整理';
                    showNextStepHint('publish');
                } else {
                    alert(`整理失败：${data.error}`);
                    organizeBtn.disabled = false;
                    organizeBtn.innerHTML = '<i class="fas fa-folder-plus"></i> 整理';
                }
            })
            .catch(error => {
                alert(`整理失败：${error.message}`);
                organizeBtn.disabled = false;
                organizeBtn.innerHTML = '<i class="fas fa-folder-plus"></i> 整理';
            });
    }

    function showNextStepHint(next) {
        const existing = document.getElementById('next-step-hint');
        if (existing) return;
        const map = {
            hook: { label: '→ 继续生成钩子', href: 'hook-subpage.html' },
            title: { label: '→ 继续生成标题', href: 'title-subpage.html' },
            publish: { label: '→ 前往发布管理', href: '../../html/publish-page.html' },
        };
        const item = map[next];
        if (!item) return;
        const btn = document.createElement('button');
        btn.id = 'next-step-hint';
        btn.className = 'btn generate-btn';
        btn.style.cssText = 'margin-top:16px;background:linear-gradient(135deg,#2ecc71,#27ae60);';
        btn.innerHTML = `<i class="fas fa-arrow-right"></i> ${item.label}`;
        btn.addEventListener('click', () => { window.location.href = item.href; });
        organizeBtn.parentElement.appendChild(btn);
    }
});