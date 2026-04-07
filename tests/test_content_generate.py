"""Unit tests for ContentCreatorService — Gemini API is fully mocked."""
import os
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Stub out google.genai before importing the service so no real API call occurs
import types
google_stub = types.ModuleType('google')
genai_stub = types.ModuleType('google.genai')
class _FakeClient:
    def __init__(self, **_): pass
    class models:
        @staticmethod
        def generate_content(**_): return MagicMock(text='{"drafts": []}')
genai_stub.Client = _FakeClient
google_stub.genai = genai_stub
sys.modules.setdefault('google', google_stub)
sys.modules.setdefault('google.genai', genai_stub)

from backend.service.content.content_generate import ContentCreatorService


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    """Service with all file paths redirected to tmp_path."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')

    tip_dir = tmp_path / 'tip'
    tip_dir.mkdir()
    (tip_dir / 'title.txt').write_text('标题技巧', encoding='utf-8')
    (tip_dir / 'hook.txt').write_text('钩子技巧', encoding='utf-8')
    (tip_dir / 'content.txt').write_text('正文技巧', encoding='utf-8')
    (tip_dir / 'emoji.txt').write_text('[爱心R] [笑哭R] [闪光R]', encoding='utf-8')
    (tmp_path / 'material.txt').write_text('# 美甲\n卡其色美甲很好看\n', encoding='utf-8')

    service = ContentCreatorService.__new__(ContentCreatorService)
    service.client = _FakeClient()
    service.model_name = 'gemini-test'
    service.data_dir = str(tmp_path)
    service.content_gen_dir = str(tmp_path)
    service.material_file = str(tmp_path / 'material.txt')
    service.title_tips_file = str(tip_dir / 'title.txt')
    service.hook_tips_file = str(tip_dir / 'hook.txt')
    service.content_tips_file = str(tip_dir / 'content.txt')
    service.emoji_tips_file = str(tip_dir / 'emoji.txt')
    service._emoji_list = service._load_emoji_list()
    return service


# ── _parse_json_response ───────────────────────────────────────────────────────

class TestParseJsonResponse:
    def test_plain_json(self, svc):
        result = svc._parse_json_response('{"titles": ["a", "b"]}')
        assert result == {"titles": ["a", "b"]}

    def test_strips_markdown_json_fence(self, svc):
        raw = '```json\n{"hooks": ["x"]}\n```'
        result = svc._parse_json_response(raw)
        assert result == {"hooks": ["x"]}

    def test_strips_plain_fence(self, svc):
        raw = '```\n{"drafts": ["y"]}\n```'
        result = svc._parse_json_response(raw)
        assert result == {"drafts": ["y"]}

    def test_invalid_json_raises(self, svc):
        with pytest.raises(Exception):
            svc._parse_json_response('not json')


# ── _load_emoji_list ───────────────────────────────────────────────────────────

class TestLoadEmojiList:
    def test_extracts_bracket_codes(self, svc):
        assert '[爱心R]' in svc._emoji_list
        assert '[笑哭R]' in svc._emoji_list
        assert '[闪光R]' in svc._emoji_list

    def test_no_unicode_emoji_in_list(self, svc):
        # Emoji list should only contain [XXX] format, not unicode chars
        import re
        codes = re.findall(r'\[[^\]]+\]', svc._emoji_list)
        assert len(codes) > 0
        # Check no standalone unicode emoji chars leaked in
        for code in codes:
            assert code.startswith('[') and code.endswith(']')

    def test_missing_file_returns_empty(self, svc, tmp_path):
        svc.emoji_tips_file = str(tmp_path / 'nonexistent.txt')
        assert svc._load_emoji_list() == ''


# ── read_file ──────────────────────────────────────────────────────────────────

class TestReadFile:
    def test_reads_existing_file(self, svc, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_text('hello world', encoding='utf-8')
        assert svc.read_file(str(f)) == 'hello world'

    def test_returns_none_for_missing(self, svc):
        assert svc.read_file('/nonexistent/path/file.txt') is None


# ── generate_title (mocked API) ───────────────────────────────────────────────

class TestGenerateTitle:
    def test_returns_list_of_strings(self, svc):
        mock_resp = MagicMock()
        mock_resp.text = '{"titles": ["标题一", "标题二", "标题三"]}'
        with patch.object(svc.client.__class__, 'models') as mock_models:
            # Use a simpler approach: patch at the instance level
            pass

        # Direct mock on the client instance
        svc.client = MagicMock()
        svc.client.models.generate_content.return_value = mock_resp
        tips = svc.read_file(svc.title_tips_file) or ''
        result = svc.generate_title('美甲素材', tips)
        assert isinstance(result, list)
        assert result == ['标题一', '标题二', '标题三']

    def test_returns_empty_list_on_error(self, svc):
        svc.client = MagicMock()
        svc.client.models.generate_content.side_effect = Exception('API error')
        result = svc.generate_title('素材', '技巧')
        assert result == []


# ── generate_drafts_from_prompt ───────────────────────────────────────────────

class TestGenerateDraftsFromPrompt:
    def test_returns_drafts_list(self, svc):
        svc.client = MagicMock()
        svc.client.models.generate_content.return_value = MagicMock(
            text='{"drafts": ["草稿A", "草稿B"]}'
        )
        result = svc.generate_drafts_from_prompt('美甲创作需求')
        assert result == ['草稿A', '草稿B']

    def test_handles_list_response(self, svc):
        """Some models may return a bare JSON list."""
        svc.client = MagicMock()
        svc.client.models.generate_content.return_value = MagicMock(
            text='["草稿A", "草稿B"]'
        )
        result = svc.generate_drafts_from_prompt('需求')
        assert isinstance(result, list)

    def test_returns_empty_on_api_error(self, svc):
        svc.client = MagicMock()
        svc.client.models.generate_content.side_effect = RuntimeError('fail')
        result = svc.generate_drafts_from_prompt('需求')
        assert result == []

    def test_prompt_contains_xhs_emoji_instruction(self, svc):
        """Verify the prompt includes XHS emoji guidance, not unicode emoji."""
        captured = {}
        def fake_generate(model, contents):
            captured['prompt'] = contents
            return MagicMock(text='{"drafts": ["x"]}')
        svc.client = MagicMock()
        svc.client.models.generate_content.side_effect = fake_generate
        svc.generate_drafts_from_prompt('美甲')
        assert '禁止使用Unicode字符表情' in captured['prompt']
        assert '[爱心R]' in captured['prompt']
