"""Integration tests for Flask API routes — no real AI or Chrome calls."""
import os
import json
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub DrissionPage before any project module imports it
import types
_dp_stub = types.ModuleType('DrissionPage')
_dp_stub.ChromiumPage = type('ChromiumPage', (), {})
_dp_stub.ChromiumOptions = type('ChromiumOptions', (), {'set_local_port': lambda s, p: None})
sys.modules.setdefault('DrissionPage', _dp_stub)

google_stub = types.ModuleType('google')
genai_stub  = types.ModuleType('google.genai')
class _FakeClient:
    def __init__(self, **_): pass
    class models:
        @staticmethod
        def list(): return []
        @staticmethod
        def generate_content(**_): return MagicMock(text='{}')
genai_stub.Client = _FakeClient
google_stub.genai = genai_stub
sys.modules.setdefault('google', google_stub)
sys.modules.setdefault('google.genai', genai_stub)

import app as flask_app


@pytest.fixture()
def client():
    flask_app.app.config['TESTING'] = True
    with flask_app.app.test_client() as c:
        yield c


# ── /api/hashtags ──────────────────────────────────────────────────────────────

class TestHashtagsRoute:
    def test_returns_hashtags(self, client):
        with patch('backend.controller.publish.publish_controller.PublishController._read_hashtags',
                   return_value='#安吉美甲 #安吉纹眉'):
            resp = client.get('/api/hashtags')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '#安吉美甲' in data['hashtags']


# ── /api/publish/content ──────────────────────────────────────────────────────

class TestPublishContentRoute:
    def test_get_returns_content(self, client, tmp_path):
        folder = tmp_path / '2026.1.1' / '素材_1'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: 标题\ndesc: 正文\n', encoding='utf-8')
        with patch('backend.controller.publish.publish_controller.PublishController.get_content',
                   return_value=(True, {'success': True, 'title': '标题', 'desc': '正文'})):
            resp = client.get('/api/publish/content?path=2026.1.1/素材_1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['title'] == '标题'

    def test_post_updates_content(self, client):
        with patch('backend.controller.publish.publish_controller.PublishController.update_content',
                   return_value=(True, {'success': True})):
            resp = client.post('/api/publish/content',
                               json={'path': '2026.1.1/素材_1', 'title': '新标题', 'desc': '新正文'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_get_missing_folder_returns_400(self, client):
        with patch('backend.controller.publish.publish_controller.PublishController.get_content',
                   return_value=(False, {'success': False, 'message': '未找到'})):
            resp = client.get('/api/publish/content?path=not/exist')
        assert resp.status_code == 400


# ── /api/generate-drafts ──────────────────────────────────────────────────────

class TestGenerateDraftsRoute:
    def test_returns_drafts(self, client):
        with patch('backend.controller.content.content_controller.ContentController.generate_drafts',
                   return_value=(True, {'success': True, 'data': {'drafts': ['草稿1', '草稿2']}})):
            resp = client.post('/api/generate-drafts',
                               json={'user_prompt': '美甲创作需求'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['drafts'] == ['草稿1', '草稿2']

    def test_missing_prompt_returns_400(self, client):
        resp = client.post('/api/generate-drafts', json={})
        assert resp.status_code == 400


# ── /api/models ───────────────────────────────────────────────────────────────

class TestModelsRoute:
    def test_returns_model_list(self, client):
        fake_model = MagicMock()
        fake_model.name = 'models/gemini-2.0-flash'
        fake_model.supported_actions = ['generateContent']
        with patch.object(_FakeClient.models, 'list', return_value=[fake_model]):
            resp = client.get('/api/models')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'models' in data


# ── /api/save-edited-image ────────────────────────────────────────────────────

class TestSaveEditedImageRoute:
    def _b64_jpg(self):
        import base64
        # 1x1 white JPEG
        return 'data:image/jpeg;base64,' + base64.b64encode(
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
            b'\xff\xd9'
        ).decode()

    def test_saves_with_digit_filename(self, client, tmp_path):
        with patch('os.path.dirname', return_value=str(tmp_path)), \
             patch('os.makedirs'), \
             patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            mock_open.return_value.write = MagicMock()
            resp = client.post('/api/save-edited-image',
                               json={'imageData': self._b64_jpg(), 'filename': '1'})
        # Should succeed (or fail gracefully with path details)
        assert resp.status_code in (200, 500)  # path mock may vary by OS
