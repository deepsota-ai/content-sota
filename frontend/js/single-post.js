/* single-post.js — 单篇创作向导状态机 */

(function () {
    'use strict';

    // ─── State ───────────────────────────────────────────────────────────────
    const state = {
        selectedModel: '',
        drafts: [],
        selectedDraftIdx: -1,
        titles: [],
        selectedTitleIdx: -1,
        hooks: [],
        selectedHookIdx: -1,
        currentStep: 1,
        // Cover
        coverFilename: '',
        coverSkipped: false,
        // Extra images
        extraFiles: [],             // File objects
        extraSkipped: false,
        // Folder assigned after first image save
        folderName: null,
        currentDate: null,
        // Hashtags
        hashtags: '',
    };

    // ─── DOM helpers ─────────────────────────────────────────────────────────
    const $ = id => document.getElementById(id);

    function revealStep(n) {
        const section = $(`step-section-${n}`);
        if (!section) return;
        section.style.display = '';
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        updateStepIndicator(n);
        state.currentStep = n;
    }

    function updateStepIndicator(activeStep) {
        document.querySelectorAll('.step-item').forEach(el => {
            const s = parseInt(el.dataset.step);
            el.classList.remove('active', 'completed');
            if (s < activeStep) {
                el.classList.add('completed');
                el.querySelector('.step-circle').innerHTML = '<i class="fas fa-check"></i>';
            } else if (s === activeStep) {
                el.classList.add('active');
                el.querySelector('.step-circle').textContent = s;
            } else {
                el.querySelector('.step-circle').textContent = s;
            }
        });
        document.querySelectorAll('.step-connector').forEach((el, i) => {
            el.classList.toggle('completed', i + 1 < activeStep);
        });
    }

    function setHtml(id, html) { $(id).innerHTML = html; }

    function showMsg(id, text, type = 'info') {
        $(id).innerHTML = `<div class="msg msg-${type}">${text}</div>`;
    }

    function loadingHtml(text) {
        return `<div class="loading-overlay"><i class="fas fa-spinner"></i><span>${text}</span></div>`;
    }

    // ─── Model selector ──────────────────────────────────────────────────────
    async function loadModels() {
        try {
            const cached = localStorage.getItem('selectedModel');
            const res = await fetch('/api/models');
            const data = await res.json();
            const sel = $('model-select');
            sel.innerHTML = '';
            (data.models || []).forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = m.name || m.id;
                if (cached && cached === m.id) opt.selected = true;
                sel.appendChild(opt);
            });
            if (!cached && sel.options.length) sel.options[0].selected = true;
            state.selectedModel = sel.value;
            sel.addEventListener('change', () => {
                state.selectedModel = sel.value;
                localStorage.setItem('selectedModel', sel.value);
            });
        } catch (e) {
            console.warn('loadModels failed:', e);
        }
    }

    // ─── Step 1: Draft generation ─────────────────────────────────────────────
    function renderDraftOptions(drafts) {
        const area = $('draft-area');
        if (!drafts || drafts.length === 0) {
            area.innerHTML = '<div class="msg msg-error">未能生成草稿，请重试。</div>';
            return;
        }
        const cards = drafts.map((d, i) => `
            <div class="option-card" data-idx="${i}">${escHtml(d)}</div>
        `).join('');
        area.innerHTML = `<div class="option-cards">${cards}</div>`;
        area.querySelectorAll('.option-card').forEach(card => {
            card.addEventListener('click', () => selectDraft(parseInt(card.dataset.idx)));
        });
    }

    function selectDraft(idx) {
        state.selectedDraftIdx = idx;
        $('draft-area').querySelectorAll('.option-card').forEach((c, i) => {
            c.classList.toggle('selected', i === idx);
        });
        // Reveal step 2 and trigger parallel generation
        revealStep(2);
        generateTitlesAndHooks();
    }

    $('gen-draft-btn').addEventListener('click', async () => {
        const prompt = $('user-prompt').value.trim();
        if (!prompt) { alert('请先输入创作需求'); return; }
        $('draft-area').innerHTML = loadingHtml('正在生成草稿…');
        $('gen-draft-btn').disabled = true;
        try {
            const res = await fetch('/api/generate-drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_prompt: prompt, model_name: state.selectedModel || undefined }),
            });
            const data = await res.json();
            state.drafts = (data.data && data.data.drafts) || [];
            renderDraftOptions(state.drafts);
        } catch (e) {
            $('draft-area').innerHTML = `<div class="msg msg-error">请求失败：${e.message}</div>`;
        }
        $('gen-draft-btn').disabled = false;
    });

    // ─── Step 2 & 3: Titles and Hooks (parallel) ─────────────────────────────
    async function generateTitlesAndHooks() {
        const draft = state.drafts[state.selectedDraftIdx] || '';
        // Parallel calls
        const [titleResult, hookResult] = await Promise.allSettled([
            generateContent(draft, 'title'),
            generateContent(draft, 'hook'),
        ]);

        // Titles
        if (titleResult.status === 'fulfilled' && titleResult.value) {
            state.titles = titleResult.value.titles || [];
        } else {
            state.titles = [];
        }
        renderTitleOptions(state.titles);

        // Hooks
        if (hookResult.status === 'fulfilled' && hookResult.value) {
            state.hooks = hookResult.value.hooks || [];
        } else {
            state.hooks = [];
        }
        // Hook area rendered after title selection to avoid overwhelming UX
        // But pre-populate so it's ready
        _pendingHooks = state.hooks;
    }

    let _pendingHooks = [];

    async function generateContent(material, type) {
        const res = await fetch('/api/generate-content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                material_contents: [material],
                generate_type: type,
                model_name: state.selectedModel || undefined,
            }),
        });
        const data = await res.json();
        const results = (data.data && data.data.results) || [];
        return results[0] || null;
    }

    function renderTitleOptions(titles) {
        const area = $('title-area');
        if (!titles || titles.length === 0) {
            area.innerHTML = '<div class="msg msg-error">未能生成标题，请点击「重新生成」。</div>';
            $('regen-title-btn').style.display = 'inline-flex';
            return;
        }
        const cards = titles.map((t, i) => `
            <div class="option-card" data-idx="${i}">${escHtml(t)}</div>
        `).join('');
        area.innerHTML = `<div class="option-cards">${cards}</div>`;
        $('regen-title-btn').style.display = 'inline-flex';
        area.querySelectorAll('.option-card').forEach(card => {
            card.addEventListener('click', () => selectTitle(parseInt(card.dataset.idx)));
        });
    }

    function selectTitle(idx) {
        state.selectedTitleIdx = idx;
        $('title-area').querySelectorAll('.option-card').forEach((c, i) => {
            c.classList.toggle('selected', i === idx);
        });
        revealStep(3);
        renderHookOptions(_pendingHooks);
    }

    function renderHookOptions(hooks) {
        const area = $('hook-area');
        if (!hooks || hooks.length === 0) {
            area.innerHTML = '<div class="msg msg-error">未能生成钩子，请点击「重新生成」。</div>';
            $('regen-hook-btn').style.display = 'inline-flex';
            return;
        }
        const cards = hooks.map((h, i) => `
            <div class="option-card" data-idx="${i}">${escHtml(h)}</div>
        `).join('');
        area.innerHTML = `<div class="option-cards">${cards}</div>`;
        $('regen-hook-btn').style.display = 'inline-flex';
        area.querySelectorAll('.option-card').forEach(card => {
            card.addEventListener('click', () => selectHook(parseInt(card.dataset.idx)));
        });
    }

    function selectHook(idx) {
        state.selectedHookIdx = idx;
        $('hook-area').querySelectorAll('.option-card').forEach((c, i) => {
            c.classList.toggle('selected', i === idx);
        });
        revealStep(4);
    }

    // Re-generate buttons
    $('regen-title-btn').addEventListener('click', async () => {
        $('title-area').innerHTML = loadingHtml('重新生成标题…');
        const draft = state.drafts[state.selectedDraftIdx] || '';
        const result = await generateContent(draft, 'title');
        state.titles = (result && result.titles) || [];
        renderTitleOptions(state.titles);
    });

    $('regen-hook-btn').addEventListener('click', async () => {
        $('hook-area').innerHTML = loadingHtml('重新生成钩子…');
        const draft = state.drafts[state.selectedDraftIdx] || '';
        const result = await generateContent(draft, 'hook');
        state.hooks = (result && result.hooks) || [];
        _pendingHooks = state.hooks;
        renderHookOptions(state.hooks);
    });

    // ─── Step 4: Canvas cover editor ─────────────────────────────────────────
    const coverCanvas = $('cover-canvas');
    const coverCtx = coverCanvas.getContext('2d');

    // Cover editor state
    const coverEdit = {
        img: null,          // original Image object
        ratio: 'free',      // current crop ratio
        maskOn: false,
        textLayers: [],     // [{text, size, pos, color}]
        selectedColor: '#ffffff',
    };

    function redrawCoverCanvas() {
        if (!coverEdit.img) return;
        const img = coverEdit.img;

        // Determine crop box (always centered)
        let sx = 0, sy = 0, sw = img.naturalWidth, sh = img.naturalHeight;
        if (coverEdit.ratio !== 'free') {
            const [rw, rh] = coverEdit.ratio.split(':').map(Number);
            const targetAspect = rw / rh;
            const srcAspect = img.naturalWidth / img.naturalHeight;
            if (srcAspect > targetAspect) {
                sw = Math.round(img.naturalHeight * targetAspect);
                sx = Math.round((img.naturalWidth - sw) / 2);
            } else {
                sh = Math.round(img.naturalWidth / targetAspect);
                sy = Math.round((img.naturalHeight - sh) / 2);
            }
        }

        // Resize canvas to match cropped aspect ratio (max display 400px wide)
        const displayW = 400;
        const displayH = Math.round(displayW * (sh / sw));
        coverCanvas.width = sw;
        coverCanvas.height = sh;
        coverCanvas.style.width = displayW + 'px';
        coverCanvas.style.height = displayH + 'px';

        // Draw image
        coverCtx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);

        // Mask layer
        if (coverEdit.maskOn) {
            coverCtx.fillStyle = 'rgba(0,0,0,0.6)';
            coverCtx.fillRect(0, 0, sw, sh);
        }

        // Text layers
        coverEdit.textLayers.forEach(({ text, size, pos, color }) => {
            coverCtx.save();
            coverCtx.font = `bold ${size}px "PingFang SC", "Microsoft YaHei", sans-serif`;
            coverCtx.fillStyle = color;
            coverCtx.strokeStyle = 'rgba(0,0,0,0.6)';
            coverCtx.lineWidth = Math.max(2, size / 16);
            coverCtx.textAlign = 'center';
            coverCtx.textBaseline = 'middle';
            const x = sw / 2;
            let y;
            if (pos === 'top')        y = size * 1.2;
            else if (pos === 'bottom') y = sh - size * 1.2;
            else                       y = sh / 2;
            coverCtx.strokeText(text, x, y);
            coverCtx.fillText(text, x, y);
            coverCtx.restore();
        });
    }

    $('cover-file-input').addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;
        state.coverFilename = file.name;
        const reader = new FileReader();
        reader.onload = e => {
            const img = new Image();
            img.onload = () => {
                coverEdit.img = img;
                coverEdit.maskOn = false;
                coverEdit.textLayers = [];
                coverEdit.ratio = 'free';
                document.querySelectorAll('[data-ratio]').forEach(b => b.classList.toggle('active', b.dataset.ratio === 'free'));
                $('toggle-mask-btn').classList.remove('active');
                redrawCoverCanvas();
                $('cover-upload-zone').style.display = 'none';
                $('cover-editor-wrap').style.display = 'flex';
                $('save-cover-btn').style.display = 'inline-flex';
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });

    // Crop ratio buttons
    document.querySelectorAll('[data-ratio]').forEach(btn => {
        btn.addEventListener('click', () => {
            coverEdit.ratio = btn.dataset.ratio;
            document.querySelectorAll('[data-ratio]').forEach(b => b.classList.toggle('active', b === btn));
            redrawCoverCanvas();
        });
    });

    // Mask toggle
    $('toggle-mask-btn').addEventListener('click', () => {
        coverEdit.maskOn = !coverEdit.maskOn;
        $('toggle-mask-btn').classList.toggle('active', coverEdit.maskOn);
        redrawCoverCanvas();
    });

    // Text panel toggle
    $('toggle-text-btn').addEventListener('click', () => {
        const panel = $('text-panel');
        const showing = panel.style.display !== 'none';
        panel.style.display = showing ? 'none' : 'flex';
        $('toggle-text-btn').classList.toggle('active', !showing);
    });

    // Color swatches
    document.querySelectorAll('.color-swatch').forEach(sw => {
        sw.addEventListener('click', () => {
            document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
            sw.classList.add('active');
            coverEdit.selectedColor = sw.dataset.color;
        });
    });

    // Add text layer
    $('add-text-btn').addEventListener('click', () => {
        const text = $('cover-text-input').value.trim();
        if (!text) return;
        coverEdit.textLayers.push({
            text,
            size: parseInt($('cover-text-size').value),
            pos: $('cover-text-pos').value,
            color: coverEdit.selectedColor,
        });
        $('cover-text-input').value = '';
        redrawCoverCanvas();
    });

    // Undo last text
    $('undo-text-btn').addEventListener('click', () => {
        if (coverEdit.textLayers.length > 0) {
            coverEdit.textLayers.pop();
            redrawCoverCanvas();
        }
    });

    // Save cover
    $('save-cover-btn').addEventListener('click', async () => {
        if (!coverEdit.img) return;
        showMsg('cover-msg', '正在保存封面…', 'info');
        const b64 = coverCanvas.toDataURL('image/jpeg', 0.92);
        const res = await saveCoverImage(b64);
        if (res.success) {
            showMsg('cover-msg', '封面已保存！', 'success');
            setTimeout(() => { revealStep(5); }, 800);
        } else {
            showMsg('cover-msg', '保存失败：' + (res.error || ''), 'error');
        }
    });

    $('skip-cover-btn').addEventListener('click', () => {
        state.coverSkipped = true;
        revealStep(5);
    });

    // ─── Step 5: Extra images ─────────────────────────────────────────────────
    $('extra-file-input').addEventListener('change', function () {
        state.extraFiles = Array.from(this.files);
        const list = $('extra-images-list');
        list.innerHTML = '';
        state.extraFiles.forEach(file => {
            const reader = new FileReader();
            reader.onload = e => {
                const img = document.createElement('img');
                img.className = 'extra-image-thumb';
                img.src = e.target.result;
                list.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
        if (state.extraFiles.length > 0) {
            $('upload-extra-btn').style.display = 'inline-flex';
        }
    });

    $('upload-extra-btn').addEventListener('click', async () => {
        if (state.extraFiles.length === 0) return;
        $('upload-extra-btn').disabled = true;
        showMsg('extra-msg', '正在上传配图…', 'info');
        try {
            for (let i = 0; i < state.extraFiles.length; i++) {
                const file = state.extraFiles[i];
                const b64 = await fileToBase64(file);
                const idx = i + 2; // starts at 2
                const res = await saveImage(b64, String(idx), state.currentDate, state.folderName);
                if (!res.success) throw new Error(`第${idx}张图片保存失败：${res.error}`);
                // pick up folder if not yet assigned
                if (!state.folderName) state.folderName = res.folderName;
                if (!state.currentDate) state.currentDate = res.date;
            }
            showMsg('extra-msg', `${state.extraFiles.length} 张配图上传成功！`, 'success');
            setTimeout(() => { revealStep(6); populateReview(); }, 800);
        } catch (e) {
            showMsg('extra-msg', '上传失败：' + e.message, 'error');
        }
        $('upload-extra-btn').disabled = false;
    });

    $('skip-extra-btn').addEventListener('click', () => {
        state.extraSkipped = true;
        revealStep(6);
        populateReview();
    });

    // ─── Step 6: Review and Save ──────────────────────────────────────────────
    async function populateReview() {
        $('review-title').textContent = state.titles[state.selectedTitleIdx] || '（未选择）';
        $('review-hook').textContent = state.hooks[state.selectedHookIdx] || '（未选择）';
        $('review-draft').textContent = state.drafts[state.selectedDraftIdx] || '（未选择）';
        // Load hashtags
        try {
            const res = await fetch('/api/hashtags');
            const data = await res.json();
            state.hashtags = data.hashtags || '';
        } catch (e) {
            state.hashtags = '';
        }
        $('review-hashtags').textContent = state.hashtags || '（未配置标签）';
        $('review-hashtags').style.color = state.hashtags ? '#dde' : '#8090a0';
    }

    $('save-btn').addEventListener('click', async () => {
        const title = state.titles[state.selectedTitleIdx] || '';
        const hook = state.hooks[state.selectedHookIdx] || '';
        const draft = state.drafts[state.selectedDraftIdx] || '';
        if (!title && !hook && !draft) {
            showMsg('save-msg', '请先完成草稿、标题和钩子的选择', 'error');
            return;
        }

        const descParts = [hook, draft].filter(Boolean);
        if (state.hashtags) descParts.push(state.hashtags);
        const desc = descParts.join('\n\n');

        $('save-btn').disabled = true;
        showMsg('save-msg', '正在保存…', 'info');
        try {
            const res = await fetch('/api/organize-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ materials: [{ title, desc }] }),
            });
            const data = await res.json();
            if (data.success) {
                showMsg('save-msg', `保存成功！已存入发布目录 ${data.date || ''}`, 'success');
                $('save-btn').style.display = 'none';
                $('post-save-actions').style.display = 'flex';
            } else {
                showMsg('save-msg', '保存失败：' + (data.message || data.error || ''), 'error');
                $('save-btn').disabled = false;
            }
        } catch (e) {
            showMsg('save-msg', '请求失败：' + e.message, 'error');
            $('save-btn').disabled = false;
        }
    });

    $('goto-publish-btn').addEventListener('click', () => {
        window.location.href = '../publish-page.html';
    });
    $('new-post-btn').addEventListener('click', () => {
        window.location.reload();
    });
    $('goto-home-btn').addEventListener('click', () => {
        window.location.href = '../index.html';
    });

    // ─── API helpers ──────────────────────────────────────────────────────────
    async function saveCoverImage(imageData) {
        try {
            const res = await saveImage(imageData, '1', state.currentDate, state.folderName);
            if (res.success) {
                state.folderName = res.folderName || state.folderName;
                state.currentDate = res.date || state.currentDate;
            }
            return res;
        } catch (e) {
            return { success: false, error: e.message };
        }
    }

    async function saveImage(imageData, filename, date, folderName) {
        const body = { imageData, filename };
        if (date) body.date = date;
        if (folderName) body.folder_name = folderName;
        const res = await fetch('/api/save-edited-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await res.json();
        // Try to extract date and folder from file_path
        if (data.success && data.file_path) {
            const parts = data.file_path.replace(/\\/g, '/').split('/');
            const publishIdx = parts.indexOf('publish');
            if (publishIdx !== -1) {
                data.date = data.date || parts[publishIdx + 1];
                data.folderName = data.folderName || parts[publishIdx + 2];
            }
        }
        return data;
    }

    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    function escHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // ─── Navigation ───────────────────────────────────────────────────────────
    $('back-btn').addEventListener('click', () => { window.location.href = '../index.html'; });
    $('main-btn').addEventListener('click', () => { window.location.href = '../content-generator.html'; });

    // ─── Init ─────────────────────────────────────────────────────────────────
    loadModels();
})();
