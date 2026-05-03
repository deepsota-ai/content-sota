import os
import json
import uuid
import base64
import hashlib
import threading
import time
from datetime import date

DEPLOY_MODE = os.getenv('DEPLOY_MODE', 'local')

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_ACCOUNTS_FILE = os.path.join(_root, 'data', 'accounts.json')

# Active QR login sessions: {session_id: {xvfb_proc, chrome_proc, display, page, name}}
_qr_sessions: dict = {}
_sessions_lock = threading.Lock()


def _make_fernet():
    from cryptography.fernet import Fernet
    raw = os.getenv('ACCOUNT_ENCRYPT_KEY', 'content-creator-helper-default')
    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return Fernet(key)


def _encrypt(text: str) -> str:
    return _make_fernet().encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    return _make_fernet().decrypt(token.encode()).decode()


class AccountController:
    def __init__(self):
        self.accounts_file = _ACCOUNTS_FILE
        os.makedirs(os.path.dirname(self.accounts_file), exist_ok=True)

    # ── persistence helpers ──────────────────────────────────────────────────

    def _load(self) -> list:
        if not os.path.exists(self.accounts_file):
            return []
        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, accounts: list):
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)

    # ── public API ───────────────────────────────────────────────────────────

    def list_accounts(self):
        """Return accounts without exposing cookie/credential data."""
        accounts = self._load()
        safe = []
        for a in accounts:
            safe.append({
                'id': a['id'],
                'name': a['name'],
                'last_refreshed': a.get('last_refreshed', ''),
                'mode': a.get('mode', DEPLOY_MODE),
            })
        return True, {'success': True, 'accounts': safe}

    def add_account_local(self, name: str, profile_dir: str):
        """Local mode: add an account pointing to a Chrome profile directory."""
        if not name:
            return False, {'success': False, 'message': '账号名称不能为空'}
        accounts = self._load()
        account = {
            'id': str(uuid.uuid4())[:8],
            'name': name,
            'mode': 'local',
            'profile_dir': profile_dir,
            'last_refreshed': str(date.today()),
        }
        accounts.append(account)
        self._save(accounts)
        return True, {'success': True, 'account': {'id': account['id'], 'name': name}}

    def start_qr_login(self, name: str):
        """
        Cloud mode: start Chrome+Xvfb, navigate to XHS login, screenshot QR.
        Returns {session_id, qr_image} where qr_image is a base64 PNG data-URL.
        """
        if not name:
            return False, {'success': False, 'message': '账号名称不能为空'}

        from backend.service.publish.ibeike_extension import _allocate_xvfb_display, _start_xvfb
        from DrissionPage import ChromiumPage, ChromiumOptions

        session_id = str(uuid.uuid4())[:12]
        display = _allocate_xvfb_display()
        xvfb_proc = _start_xvfb(display)
        time.sleep(1)

        # Start Chrome (headless-ish via Xvfb)
        from backend.service.publish.ibeike_extension import _get_config
        chrome_path, _, _ = _get_config()
        import subprocess, tempfile
        user_data_dir = tempfile.mkdtemp(prefix=f'xhs_login_{session_id}_')
        env = {**os.environ, 'DISPLAY': display}
        chrome_proc = subprocess.Popen(
            [chrome_path,
             '--remote-debugging-port=9224',  # separate port for login
             f'--user-data-dir={user_data_dir}',
             '--no-first-run', '--no-default-browser-check',
             '--no-sandbox', '--disable-dev-shm-usage',
             'https://www.xiaohongshu.com'],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        try:
            co = ChromiumOptions()
            co.set_local_port(9224)
            page = ChromiumPage(addr_or_opts=co)

            # Navigate to creator login page and wait for QR code
            page.get('https://creator.xiaohongshu.com')
            time.sleep(3)

            # Screenshot the full page and return; user will see the QR
            screenshot = page.get_screenshot(as_bytes='png')
            qr_b64 = 'data:image/png;base64,' + base64.b64encode(screenshot).decode()

            with _sessions_lock:
                _qr_sessions[session_id] = {
                    'xvfb_proc': xvfb_proc,
                    'chrome_proc': chrome_proc,
                    'user_data_dir': user_data_dir,
                    'display': display,
                    'page': page,
                    'name': name,
                    'status': 'pending',
                }

            return True, {'success': True, 'session_id': session_id, 'qr_image': qr_b64}

        except Exception as e:
            xvfb_proc.terminate()
            chrome_proc.terminate()
            return False, {'success': False, 'message': f'启动失败：{e}'}

    def check_qr_status(self, session_id: str):
        """Poll login state. When logged in, saves cookies and cleans up."""
        with _sessions_lock:
            session = _qr_sessions.get(session_id)
        if not session:
            return False, {'success': False, 'message': '会话不存在或已过期'}

        page = session['page']
        try:
            current_url = page.url
        except Exception as e:
            return False, {'success': False, 'message': f'浏览器连接失败：{e}'}

        # Detect successful login by URL change
        logged_in = any(kw in current_url for kw in [
            'creator.xiaohongshu.com/creator',
            'creator.xiaohongshu.com/home',
            'creator.xiaohongshu.com/publish',
            'xiaohongshu.com/user/profile',
        ])

        if not logged_in:
            # Refresh screenshot so user can re-scan if QR expired
            try:
                screenshot = page.get_screenshot(as_bytes='png')
                qr_b64 = 'data:image/png;base64,' + base64.b64encode(screenshot).decode()
            except Exception:
                qr_b64 = None
            return True, {'success': True, 'status': 'pending', 'qr_image': qr_b64}

        # Logged in: extract cookies
        try:
            cookies = page.cookies()
            cookies_json = json.dumps(cookies)
            encrypted = _encrypt(cookies_json)

            accounts = self._load()
            account = {
                'id': str(uuid.uuid4())[:8],
                'name': session['name'],
                'mode': 'cloud',
                'cookies': encrypted,
                'last_refreshed': str(date.today()),
            }
            accounts.append(account)
            self._save(accounts)
        except Exception as e:
            return False, {'success': False, 'message': f'保存Cookie失败：{e}'}
        finally:
            self._cleanup_session(session_id)

        return True, {'success': True, 'status': 'done',
                      'account': {'id': account['id'], 'name': account['name']}}

    def delete_account(self, account_id: str):
        accounts = self._load()
        before = len(accounts)
        accounts = [a for a in accounts if a['id'] != account_id]
        if len(accounts) == before:
            return False, {'success': False, 'message': '账号不存在'}
        self._save(accounts)
        return True, {'success': True}

    def get_account_by_id(self, account_id: str) -> dict | None:
        """Return account dict with decrypted cookies (cloud) or profile_dir (local)."""
        for a in self._load():
            if a['id'] == account_id:
                result = dict(a)
                if result.get('mode') == 'cloud' and result.get('cookies'):
                    result['cookies_decrypted'] = _decrypt(result['cookies'])
                return result
        return None

    def _cleanup_session(self, session_id: str):
        import shutil
        with _sessions_lock:
            session = _qr_sessions.pop(session_id, None)
        if session:
            try:
                session['page'].close()
            except Exception:
                pass
            try:
                session['chrome_proc'].terminate()
            except Exception:
                pass
            try:
                session['xvfb_proc'].terminate()
            except Exception:
                pass
            try:
                shutil.rmtree(session['user_data_dir'], ignore_errors=True)
            except Exception:
                pass
