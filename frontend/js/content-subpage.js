// 优化文案子页面JavaScript

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

    // 生成钩子按钮点击事件
    const goToHookBtn = document.getElementById('go-to-hook-btn');
    if (goToHookBtn) {
        goToHookBtn.addEventListener('click', () => {
            window.location.href = 'hook-subpage.html';
        });
    }

    // 内容容器
    const materialCarousel = document.getElementById('material-carousel');
    const resultCarousel = document.getElementById('result-carousel');
    const filterGrid = document.getElementById('filter-grid');
    const organizeBtn = document.getElementById('organize-btn');

    // 内容数据
    let materials = [];
    let generatedContents = [];

    // 页面加载时动态加载素材和模型列表
    loadMaterialsFromAPI();
    loadModels();

    // 生成按钮点击事件
    generateBtn.addEventListener('click', () => {
        generateContentFromAPI();
    });

    // 整理按钮点击事件
    organizeBtn.addEventListener('click', () => {
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
                        fullContent: block // 保存完整内容用于生成
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

    // 从API生成优化文案函数
    function generateContentFromAPI() {
        // 禁用按钮，显示加载状态
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';

        // 显示结果加载状态
        showLoading('result-carousel', '正在优化文案...');

        // 准备请求数据
        const modelSelect = document.getElementById('model-select');
        const requestData = {
            material_contents: materials.map(m => m.fullContent),
            generate_type: "content",
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
                        content: result.content || '',
                        error: result.error,
                        id: Date.now() + index
                    }));

                    // 更新结果显示
                    renderResults();
                    renderFilterModules();
                    organizeBtn.disabled = false;
                } else {
                    showError('result-carousel', data.error);
                }
            })
            .catch(error => {
                showError('result-carousel', `优化文案失败: ${error.message}`);
            })
            .finally(() => {
                // 恢复按钮状态
                generateBtn.disabled = false;
                generateBtn.innerHTML = '<i class="fas fa-magic"></i> 优化文案';
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

    // 渲染筛选模块（desc 预填优化后的文案）
    function renderFilterModules() {
        filterGrid.innerHTML = '';
        generatedContents.forEach((content, index) => {
            const card = document.createElement('div');
            card.className = 'filter-card';
            const contentText = Array.isArray(content.content)
                ? content.content.join('\n')
                : (content.content || '');
            card.innerHTML = `
                <h3>素材 ${content.materialIndex} 筛选结果</h3>
                <div class="filter-field">
                    <label for="title-${index}">标题 (title)</label>
                    <textarea id="title-${index}" placeholder="请输入标题（从生成标题页复制，或手动填写）" class="filter-textarea"></textarea>
                </div>
                <div class="filter-field">
                    <label for="desc-${index}">优化文案/描述 (desc)</label>
                    <textarea id="desc-${index}" class="filter-textarea">${contentText}</textarea>
                </div>
            `;
            filterGrid.appendChild(card);

            const titleInput = card.querySelector(`#title-${index}`);
            const descInput  = card.querySelector(`#desc-${index}`);
            titleInput.addEventListener('input', e => { materials[content.materialIndex - 1].filterTitle = e.target.value; });
            descInput.addEventListener('input',  e => { materials[content.materialIndex - 1].filterDesc  = e.target.value; });
            // 初始化 filterDesc 为预填的优化文案
            materials[content.materialIndex - 1].filterDesc = contentText;
        });
    }

    // 整理内容
    function organizeContent() {
        organizeBtn.disabled = true;
        organizeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 整理中...';
        const requestData = {
            materials: materials.map(m => ({
                title: m.filterTitle || '',
                desc:  m.filterDesc  || '',
                fullContent: m.fullContent
            }))
        };
        fetch('/api/organize-content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        })
            .then(r => r.json())
            .then(data => {
                if (data.success) alert('整理成功！内容已保存到 data/publish 目录');
                else alert(`整理失败：${data.error}`);
            })
            .catch(e => alert(`整理失败：${e.message}`))
            .finally(() => {
                organizeBtn.disabled = false;
                organizeBtn.innerHTML = '<i class="fas fa-folder-plus"></i> 整理';
            });
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
                        优化后的文案
                    </h3>
                    <div class="result-content">
                        <div class="result-content-text" id="content-result-text">
                            <p class="placeholder">点击"优化文案"按钮获取优化后的文案</p>
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
                // 生成优化文案HTML，处理数组格式的content
                let contentHtml = '';
                if (Array.isArray(content.content)) {
                    // 如果是数组，遍历生成多个文案项
                    content.content.forEach((item, index) => {
                        contentHtml += `
                            <div class="result-item">
                                <h5 class="item-number">优化文案 ${index + 1}</h5>
                                <p class="item-content">${item}</p>
                            </div>
                        `;
                    });
                } else {
                    // 如果是单个字符串，直接显示
                    contentHtml = `
                        <div class="result-item">
                            <p class="item-content">${content.content}</p>
                        </div>
                    `;
                }

                card.innerHTML = `
                    <h3 class="result-card-title">
                        素材 ${content.materialIndex} 优化后的文案
                    </h3>
                    <div class="result-content">
                        <div class="result-content-text">
                            <h4>优化文案</h4>
                            <div class="result-list">${contentHtml}</div>
                        </div>
                    </div>
                `;
            }

            resultCarousel.appendChild(card);
        });
    }
});