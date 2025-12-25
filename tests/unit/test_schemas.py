"""Unit tests for Pydantic schemas and validation."""

import pytest
from pydantic import ValidationError

from app.schemas.execution import ExecutionRequest


class TestExecutionRequestSchema:
    """Tests for ExecutionRequest schema validation."""

    def test_valid_request_with_defaults(self):
        """Should accept valid request with default temperature and max_tokens."""
        request = ExecutionRequest(prompt="Test prompt", model="gpt-4o-mini")

        assert request.prompt == "Test prompt"
        assert request.model == "gpt-4o-mini"
        assert request.temperature == 0.7  # Default
        assert request.max_tokens is None  # Default

    def test_valid_request_with_custom_params(self):
        """Should accept custom temperature and max_tokens."""
        request = ExecutionRequest(
            prompt="Test",
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=500,
        )

        assert request.temperature == 0.3
        assert request.max_tokens == 500

    def test_rejects_invalid_model(self):
        """Should reject model not in allowed list."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="Test", model="invalid-model")

        errors = exc_info.value.errors()
        assert any("Invalid model" in str(e["ctx"]) for e in errors)

    def test_rejects_empty_prompt(self):
        """Should reject empty prompt."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="", model="gpt-4o-mini")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("prompt",) for e in errors)

    def test_rejects_temperature_below_zero(self):
        """Should reject temperature < 0.0."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="Test", model="gpt-4o-mini", temperature=-0.1)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("temperature",) for e in errors)

    def test_rejects_temperature_above_two(self):
        """Should reject temperature > 2.0."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="Test", model="gpt-4o-mini", temperature=2.1)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("temperature",) for e in errors)

    def test_accepts_temperature_boundaries(self):
        """Should accept temperature at boundaries (0.0, 2.0)."""
        request_min = ExecutionRequest(
            prompt="Test", model="gpt-4o-mini", temperature=0.0
        )
        request_max = ExecutionRequest(
            prompt="Test", model="gpt-4o-mini", temperature=2.0
        )

        assert request_min.temperature == 0.0
        assert request_max.temperature == 2.0

    def test_rejects_max_tokens_zero(self):
        """Should reject max_tokens = 0."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="Test", model="gpt-4o-mini", max_tokens=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_tokens",) for e in errors)

    def test_rejects_max_tokens_above_limit(self):
        """Should reject max_tokens > 4096."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt="Test", model="gpt-4o-mini", max_tokens=5000)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("max_tokens",) for e in errors)

    def test_accepts_max_tokens_boundaries(self):
        """Should accept max_tokens at boundaries (1, 4096)."""
        request_min = ExecutionRequest(
            prompt="Test", model="gpt-4o-mini", max_tokens=1
        )
        request_max = ExecutionRequest(
            prompt="Test", model="gpt-4o-mini", max_tokens=4096
        )

        assert request_min.max_tokens == 1
        assert request_max.max_tokens == 4096

    def test_accepts_all_allowed_models(self):
        """Should accept all models in allowed list."""
        allowed_models = [
            "gpt-4o-mini",
            "gpt-5",
            "gpt-3.5-turbo",
            "claude-4-opus",
            "claude-4.5-sonnet",
            "gemini-2.5-pro",
        ]

        for model in allowed_models:
            request = ExecutionRequest(prompt="Test", model=model)
            assert request.model == model

    def test_prompt_has_max_length(self):
        """Should reject prompt exceeding max length."""
        long_prompt = "x" * 10001  # Assuming max is 10000

        with pytest.raises(ValidationError) as exc_info:
            ExecutionRequest(prompt=long_prompt, model="gpt-4o-mini")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("prompt",) for e in errors)
