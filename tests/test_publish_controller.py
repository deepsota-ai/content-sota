"""Unit tests for PublishController — no file system or network required."""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Resolve project root so imports work from any working directory
import sys
import types
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub DrissionPage before publish_controller imports it
_dp_stub = types.ModuleType('DrissionPage')
_dp_stub.ChromiumPage = type('ChromiumPage', (), {})
_dp_stub.ChromiumOptions = type('ChromiumOptions', (), {'set_local_port': lambda s, p: None})
sys.modules.setdefault('DrissionPage', _dp_stub)

from backend.controller.publish.publish_controller import PublishController


@pytest.fixture()
def tmp_publish_dir(tmp_path):
    """Create a temporary publish base directory and patch the controller."""
    return tmp_path


@pytest.fixture()
def controller(tmp_publish_dir):
    ctrl = PublishController.__new__(PublishController)
    ctrl.base_path = str(tmp_publish_dir)
    # Patch _read_hashtags to avoid file I/O
    ctrl._read_hashtags = lambda: '#安吉美甲 #安吉纹眉'
    return ctrl


# ── get_content ────────────────────────────────────────────────────────────────

class TestGetContent:
    def test_returns_title_and_desc(self, controller, tmp_publish_dir):
        folder = tmp_publish_dir / '2026.1.1' / '素材_1'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: 好看美甲\ndesc: 正文第一行\n第二行\n', encoding='utf-8')

        ok, data = controller.get_content('2026.1.1/素材_1')

        assert ok is True
        assert data['title'] == '好看美甲'
        assert '正文第一行' in data['desc']
        assert '第二行' in data['desc']

    def test_missing_file_returns_error(self, controller):
        ok, data = controller.get_content('2026.1.1/不存在的素材')
        assert ok is False
        assert 'message' in data

    def test_empty_desc_returns_empty_string(self, controller, tmp_publish_dir):
        folder = tmp_publish_dir / '2026.1.2' / '素材_1'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: 仅标题\ndesc: \n', encoding='utf-8')

        ok, data = controller.get_content('2026.1.2/素材_1')
        assert ok is True
        assert data['title'] == '仅标题'


# ── update_content ─────────────────────────────────────────────────────────────

class TestUpdateContent:
    def test_overwrites_file(self, controller, tmp_publish_dir):
        folder = tmp_publish_dir / '2026.1.3' / '素材_1'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: 旧标题\ndesc: 旧正文\n', encoding='utf-8')

        ok, data = controller.update_content('2026.1.3/素材_1', '新标题', '新正文内容')

        assert ok is True
        content = (folder / '1.txt').read_text(encoding='utf-8')
        assert 'title: 新标题' in content
        assert 'desc: 新正文内容' in content
        assert '旧标题' not in content

    def test_missing_folder_returns_error(self, controller):
        ok, data = controller.update_content('不存在/素材_99', '标题', '内容')
        assert ok is False

    def test_roundtrip(self, controller, tmp_publish_dir):
        folder = tmp_publish_dir / '2026.1.4' / '素材_1'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: x\ndesc: y\n', encoding='utf-8')

        controller.update_content('2026.1.4/素材_1', '新标题', '第一行\n第二行')
        ok, data = controller.get_content('2026.1.4/素材_1')
        assert ok is True
        assert data['title'] == '新标题'
        assert '第一行' in data['desc']


# ── publish_content mode detection ─────────────────────────────────────────────

class TestPublishContentMode:
    def _make_folder(self, tmp_publish_dir, name, files):
        folder = tmp_publish_dir / '2026.1.5' / name
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: t\ndesc: d\n', encoding='utf-8')
        for f in files:
            (folder / f).write_bytes(b'fake')
        return folder

    def test_image_mode_no_video_passes_check(self, controller, tmp_publish_dir):
        self._make_folder(tmp_publish_dir, '素材_img', ['1.jpg'])
        with patch('backend.controller.publish.publish_controller.start_chrome_with_extension'), \
             patch('backend.controller.publish.publish_controller.connect_to_extension', return_value=True):
            ok, data = controller.publish_content('2026.1.5/素材_img')
        assert ok is True

    def test_image_mode_missing_jpg_fails(self, controller, tmp_publish_dir):
        folder = tmp_publish_dir / '2026.1.5' / '素材_nojpg'
        folder.mkdir(parents=True)
        (folder / '1.txt').write_text('title: t\ndesc: d\n', encoding='utf-8')
        ok, data = controller.publish_content('2026.1.5/素材_nojpg')
        assert ok is False
        assert '1.jpg' in data['message']

    def test_video_mode_detected_when_mov_present(self, controller, tmp_publish_dir):
        self._make_folder(tmp_publish_dir, '素材_vid', ['1.jpg', 'video.MOV'])
        with patch('backend.controller.publish.publish_controller.start_chrome_with_extension'), \
             patch('backend.controller.publish.publish_controller.connect_to_extension', return_value=True) as mock_conn:
            controller.publish_content('2026.1.5/素材_vid')
        mock_conn.assert_called_once_with('2026.1.5/素材_vid', mode='video')

    def test_image_mode_passed_to_connect(self, controller, tmp_publish_dir):
        self._make_folder(tmp_publish_dir, '素材_imgmode', ['1.jpg'])
        with patch('backend.controller.publish.publish_controller.start_chrome_with_extension'), \
             patch('backend.controller.publish.publish_controller.connect_to_extension', return_value=True) as mock_conn:
            controller.publish_content('2026.1.5/素材_imgmode')
        mock_conn.assert_called_once_with('2026.1.5/素材_imgmode', mode='image')
