"""Tests for air_reader.config — deferred validation."""

import pytest

from air_reader import config
from air_reader.config import ConfigError


class TestValidate:
    def test_validate_succeeds_with_all_vars(self, monkeypatch):
        monkeypatch.setattr(config, "WHATSAPP_TOKEN", "tok")
        monkeypatch.setattr(config, "WHATSAPP_PHONE_NUMBER_ID", "123")
        monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", "verify")
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")

        config.validate()
        assert "123" in config.WHATSAPP_API_URL

    def test_validate_raises_when_missing(self, monkeypatch):
        monkeypatch.setattr(config, "WHATSAPP_TOKEN", "")
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")

        with pytest.raises(ConfigError, match="WHATSAPP_TOKEN"):
            config.validate()

    def test_builds_api_url(self, monkeypatch):
        monkeypatch.setattr(config, "WHATSAPP_TOKEN", "tok")
        monkeypatch.setattr(config, "WHATSAPP_PHONE_NUMBER_ID", "99999")
        monkeypatch.setattr(config, "WHATSAPP_VERIFY_TOKEN", "verify")
        monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-test")

        config.validate()
        assert config.WHATSAPP_API_URL == "https://graph.facebook.com/v21.0/99999/messages"
