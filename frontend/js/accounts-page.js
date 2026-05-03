document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('back-btn').addEventListener('click', () => {
        window.location.href = 'index.html';
    });

    const addBtn     = document.getElementById('add-btn');
    const modal      = document.getElementById('add-modal');
    const cancelBtn  = document.getElementById('modal-cancel');
    const confirmBtn = document.getElementById('modal-confirm');
    const statusBar  = document.getElementById('status-bar');

    const tabLocal  = document.getElementById('tab-local');
    const tabCloud  = document.getElementById('tab-cloud');
    const localFields = document.getElementById('local-fields');
    const cloudFields = document.getElementById('cloud-fields');

    const getQrBtn  = document.getElementById('get-qr-btn');
    const qrImgWrap = document.getElementById('qr-image-wrap');
    const qrImg     = document.getElementById('qr-img');
    const qrStatus  = document.getElementById('qr-status');

    let currentMode = 'local';
    let qrSessionId = null;
    let qrPollTimer = null;

    // ── load accounts ────────────────────────────────────────────────────────
    loadAccounts();

    async function loadAccounts() {
        const list = document.getElementById('account-list');
        try {
            const res  = await fetch('/api/accounts');
            const data = await res.json();
            if (!data.success || !data.accounts.length) {
                list.innerHTML = '<div class="empty-state">暂无账号，点击"添加账号"开始配置</div>';
                return;
            }
            list.innerHTML = data.accounts.map(a => `
                <div class="account-card">
                    <div class="account-info">
                        <h4>${a.name}
                            <span class="account-mode ${a.mode}">${a.mode === 'cloud' ? '云端' : '本地'}</span>
                        </h4>
                        <small>最后更新：${a.last_refreshed || '—'}</small>
                    </div>
                    <button class="btn-delete" data-id="${a.id}"><i class="fas fa-trash"></i> 删除</button>
                </div>
            `).join('');

            list.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', () => deleteAccount(btn.dataset.id));
            });
        } catch (e) {
            list.innerHTML = `<div class="empty-state" style="color:#e74c3c">加载失败：${e.message}</div>`;
        }
    }

    async function deleteAccount(id) {
        if (!confirm('确认删除该账号？')) return;
        const res  = await fetch(`/api/accounts/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showStatus('success', '已删除');
            loadAccounts();
        } else {
            showStatus('error', data.message || '删除失败');
        }
    }

    // ── modal open / close ───────────────────────────────────────────────────
    addBtn.addEventListener('click', () => {
        resetModal();
        modal.classList.add('open');
    });
    cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    function closeModal() {
        stopQrPoll();
        modal.classList.remove('open');
    }

    function resetModal() {
        document.getElementById('modal-name').value = '';
        document.getElementById('modal-profile-dir').value = '';
        currentMode = 'local';
        setMode('local');
        qrSessionId = null;
        qrImgWrap.style.display = 'none';
        qrStatus.textContent = '等待扫码…';
        qrStatus.className = 'qr-status';
        document.getElementById('refresh-qr-btn').style.display = 'none';
        confirmBtn.disabled = false;
        confirmBtn.textContent = '保存';
    }

    // ── mode tabs ────────────────────────────────────────────────────────────
    tabLocal.addEventListener('click', () => setMode('local'));
    tabCloud.addEventListener('click', () => setMode('cloud'));

    function setMode(mode) {
        currentMode = mode;
        tabLocal.classList.toggle('active', mode === 'local');
        tabCloud.classList.toggle('active', mode === 'cloud');
        localFields.style.display = mode === 'local' ? '' : 'none';
        cloudFields.style.display = mode === 'cloud' ? '' : 'none';
        confirmBtn.style.display = mode === 'local' ? '' : 'none';
    }

    // ── QR login (cloud) ─────────────────────────────────────────────────────
    getQrBtn.addEventListener('click', startQrLogin);
    document.getElementById('refresh-qr-btn').addEventListener('click', startQrLogin);

    async function startQrLogin() {
        const name = document.getElementById('modal-name').value.trim();
        if (!name) { alert('请先填写账号名称'); return; }
        stopQrPoll();
        getQrBtn.disabled = true;
        getQrBtn.textContent = '启动中…';
        qrImgWrap.style.display = 'none';

        try {
            const res  = await fetch('/api/accounts/start-qr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.message);

            qrSessionId = data.session_id;
            qrImg.src = data.qr_image;
            qrImgWrap.style.display = '';
            qrStatus.textContent = '等待手机扫码…';
            qrStatus.className = 'qr-status';
            startQrPoll();
        } catch (e) {
            showStatus('error', `启动失败：${e.message}`);
        } finally {
            getQrBtn.disabled = false;
            getQrBtn.textContent = '获取二维码';
        }
    }

    function startQrPoll() {
        qrPollTimer = setInterval(async () => {
            if (!qrSessionId) return;
            try {
                const res  = await fetch(`/api/accounts/qr-status?session_id=${qrSessionId}`);
                const data = await res.json();
                if (!data.success) { stopQrPoll(); return; }

                if (data.status === 'done') {
                    stopQrPoll();
                    qrStatus.textContent = '✓ 登录成功，账号已保存';
                    qrStatus.className = 'qr-status success';
                    showStatus('success', `账号 "${data.account?.name}" 添加成功`);
                    setTimeout(() => { closeModal(); loadAccounts(); }, 1500);
                } else if (data.qr_image) {
                    // Refresh screenshot in case QR expired
                    qrImg.src = data.qr_image;
                }
            } catch (e) {
                // Ignore poll errors, keep trying
            }
        }, 3000);
    }

    function stopQrPoll() {
        if (qrPollTimer) { clearInterval(qrPollTimer); qrPollTimer = null; }
    }

    // ── save local account ───────────────────────────────────────────────────
    confirmBtn.addEventListener('click', async () => {
        const name       = document.getElementById('modal-name').value.trim();
        const profileDir = document.getElementById('modal-profile-dir').value.trim();
        if (!name) { alert('请填写账号名称'); return; }

        confirmBtn.disabled = true;
        confirmBtn.textContent = '保存中…';
        try {
            const res  = await fetch('/api/accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, profile_dir: profileDir }),
            });
            const data = await res.json();
            if (data.success) {
                showStatus('success', `账号 "${name}" 已添加`);
                closeModal();
                loadAccounts();
            } else {
                showStatus('error', data.message || '添加失败');
            }
        } catch (e) {
            showStatus('error', e.message);
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.textContent = '保存';
        }
    });

    function showStatus(type, msg) {
        statusBar.className = `status-bar ${type}`;
        statusBar.textContent = msg;
        setTimeout(() => { statusBar.className = 'status-bar'; statusBar.textContent = ''; }, 4000);
    }
});
