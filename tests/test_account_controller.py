"""Unit tests for AccountController — no Chrome, no network, no file I/O outside tmp_path."""
import os
import json
import sys
import types
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub DrissionPage before any project imports
_dp_stub = types.ModuleType('DrissionPage')
_dp_stub.ChromiumPage    = type('ChromiumPage', (), {})
_dp_stub.ChromiumOptions = type('ChromiumOptions', (), {'set_local_port': lambda s, p: None})
sys.modules.setdefault('DrissionPage', _dp_stub)

# Stub cryptography so tests work even before `pip install cryptography`
try:
    from cryptography.fernet import Fernet  # noqa: F401
except ImportError:
    import base64, hashlib
    class _FakeFernet:
        def __init__(self, key): self._key = key
        def encrypt(self, data: bytes) -> bytes: return base64.b64encode(data)
        def decrypt(self, token: bytes) -> bytes: return base64.b64decode(token)
    crypto_stub = types.ModuleType('cryptography')
    fernet_mod  = types.ModuleType('cryptography.fernet')
    fernet_mod.Fernet = _FakeFernet
    crypto_stub.fernet = fernet_mod
    sys.modules.setdefault('cryptography', crypto_stub)
    sys.modules.setdefault('cryptography.fernet', fernet_mod)

from backend.controller.account import account_controller as _mod
from backend.controller.account.account_controller import AccountController, _encrypt, _decrypt


@pytest.fixture()
def ctrl(tmp_path, monkeypatch):
    """AccountController wired to a temporary accounts.json."""
    monkeypatch.setattr(_mod, '_ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    return AccountController()


# ── encryption round-trip ─────────────────────────────────────────────────────

class TestEncryption:
    def test_roundtrip_ascii(self):
        plain = 'hello world'
        assert _decrypt(_encrypt(plain)) == plain

    def test_roundtrip_json(self):
        payload = json.dumps([{'name': 'token', 'value': 'abc123', 'domain': '.xiaohongshu.com'}])
        assert _decrypt(_encrypt(payload)) == payload

    def test_encrypt_produces_different_output(self):
        # Fernet produces ciphertext ≠ plaintext (basic sanity)
        plain = 'secret'
        assert _encrypt(plain) != plain


# ── list_accounts ─────────────────────────────────────────────────────────────

class TestListAccounts:
    def test_empty_returns_empty_list(self, ctrl):
        ok, data = ctrl.list_accounts()
        assert ok is True
        assert data['accounts'] == []

    def test_lists_added_account(self, ctrl):
        ctrl.add_account_local('官号', '/tmp/profile_a')
        ok, data = ctrl.list_accounts()
        assert ok is True
        assert len(data['accounts']) == 1
        assert data['accounts'][0]['name'] == '官号'

    def test_does_not_expose_cookies(self, ctrl, tmp_path, monkeypatch):
        # Manually write a cloud account with a cookies field
        accounts_file = str(tmp_path / 'accounts.json')
        monkeypatch.setattr(_mod, '_ACCOUNTS_FILE', accounts_file)
        ctrl2 = AccountController()
        raw = [{'id': 'x1', 'name': '测试号', 'mode': 'cloud',
                'cookies': _encrypt('{"token":"secret"}'), 'last_refreshed': '2026-05-03'}]
        with open(accounts_file, 'w', encoding='utf-8') as f:
            json.dump(raw, f)

        _, data = ctrl2.list_accounts()
        assert 'cookies' not in data['accounts'][0]


# ── add_account_local ─────────────────────────────────────────────────────────

class TestAddAccountLocal:
    def test_adds_account_to_file(self, ctrl, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, '_ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
        ctrl2 = AccountController()
        ok, data = ctrl2.add_account_local('纹眉号', r'C:\profiles\b')
        assert ok is True
        assert 'id' in data['account']

    def test_persists_across_instances(self, ctrl, tmp_path, monkeypatch):
        path = str(tmp_path / 'accounts.json')
        monkeypatch.setattr(_mod, '_ACCOUNTS_FILE', path)
        ctrl_a = AccountController()
        ctrl_a.add_account_local('A', '/p/a')
        ctrl_b = AccountController()
        _, data = ctrl_b.list_accounts()
        assert any(a['name'] == 'A' for a in data['accounts'])

    def test_empty_name_returns_error(self, ctrl):
        ok, data = ctrl.add_account_local('', '/some/path')
        assert ok is False
        assert 'message' in data

    def test_multiple_accounts(self, ctrl):
        ctrl.add_account_local('账号A', '/p/a')
        ctrl.add_account_local('账号B', '/p/b')
        _, data = ctrl.list_accounts()
        assert len(data['accounts']) == 2


# ── delete_account ────────────────────────────────────────────────────────────

class TestDeleteAccount:
    def test_delete_existing(self, ctrl):
        ctrl.add_account_local('删除测试', '/p/del')
        _, list_data = ctrl.list_accounts()
        account_id = list_data['accounts'][0]['id']

        ok, _ = ctrl.delete_account(account_id)
        assert ok is True
        _, after = ctrl.list_accounts()
        assert after['accounts'] == []

    def test_delete_nonexistent_returns_error(self, ctrl):
        ok, data = ctrl.delete_account('no-such-id')
        assert ok is False
        assert 'message' in data

    def test_delete_only_removes_target(self, ctrl):
        ctrl.add_account_local('保留', '/p/keep')
        ctrl.add_account_local('删除', '/p/del')
        _, list_data = ctrl.list_accounts()
        del_id = next(a['id'] for a in list_data['accounts'] if a['name'] == '删除')

        ctrl.delete_account(del_id)
        _, after = ctrl.list_accounts()
        assert len(after['accounts']) == 1
        assert after['accounts'][0]['name'] == '保留'


# ── get_account_by_id ─────────────────────────────────────────────────────────

class TestGetAccountById:
    def test_returns_account(self, ctrl):
        ctrl.add_account_local('查找账号', '/p/find')
        _, list_data = ctrl.list_accounts()
        account_id = list_data['accounts'][0]['id']

        account = ctrl.get_account_by_id(account_id)
        assert account is not None
        assert account['name'] == '查找账号'
        assert account['profile_dir'] == '/p/find'

    def test_returns_none_for_missing_id(self, ctrl):
        assert ctrl.get_account_by_id('ghost') is None

    def test_cloud_account_decrypts_cookies(self, ctrl, tmp_path, monkeypatch):
        accounts_file = str(tmp_path / 'accounts_cloud.json')
        monkeypatch.setattr(_mod, '_ACCOUNTS_FILE', accounts_file)
        ctrl2 = AccountController()
        raw_cookies = '[{"name":"a_t","value":"tok123","domain":".xiaohongshu.com"}]'
        raw = [{'id': 'c1', 'name': '云端号', 'mode': 'cloud',
                'cookies': _encrypt(raw_cookies), 'last_refreshed': '2026-05-03'}]
        with open(accounts_file, 'w', encoding='utf-8') as f:
            json.dump(raw, f)

        account = ctrl2.get_account_by_id('c1')
        assert account is not None
        assert account.get('cookies_decrypted') == raw_cookies
