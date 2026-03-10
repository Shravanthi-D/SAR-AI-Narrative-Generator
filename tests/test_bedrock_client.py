import json
import os
import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("BEDROCK_MODEL_ID", "meta.llama3-1-70b-instruct-v1:0")

from backend.agents.bedrock_client import _build_prompt, call_llama


def _make_mock_client(generation_text: str) -> MagicMock:
    body_bytes = json.dumps({"generation": generation_text}).encode()
    mock_response = {"body": BytesIO(body_bytes)}
    mock_client = MagicMock()
    mock_client.invoke_model.return_value = mock_response
    return mock_client


class TestBuildPrompt:
    def test_contains_begin_of_text(self):
        result = _build_prompt("Hello", "")
        assert result.startswith("<|begin_of_text|>")

    def test_user_header_present(self):
        result = _build_prompt("Hello", "")
        assert "<|start_header_id|>user<|end_header_id|>" in result

    def test_user_content_present(self):
        result = _build_prompt("Hello", "")
        assert "Hello" in result

    def test_assistant_header_at_end(self):
        result = _build_prompt("Hello", "")
        assert result.endswith("<|start_header_id|>assistant<|end_header_id|>\n\n")

    def test_system_header_included_when_provided(self):
        result = _build_prompt("Hello", "You are an expert.")
        assert "<|start_header_id|>system<|end_header_id|>" in result
        assert "You are an expert." in result

    def test_system_header_absent_when_empty(self):
        result = _build_prompt("Hello", "")
        assert "<|start_header_id|>system<|end_header_id|>" not in result

    def test_system_appears_before_user(self):
        result = _build_prompt("user msg", "system msg")
        system_pos = result.index("<|start_header_id|>system<|end_header_id|>")
        user_pos = result.index("<|start_header_id|>user<|end_header_id|>")
        assert system_pos < user_pos

    def test_eot_id_after_system(self):
        result = _build_prompt("Hello", "Be helpful.")
        system_end = result.index("<|start_header_id|>system<|end_header_id|>")
        eot_pos = result.index("<|eot_id|>", system_end)
        user_pos = result.index("<|start_header_id|>user<|end_header_id|>")
        assert eot_pos < user_pos

    def test_eot_id_after_user(self):
        result = _build_prompt("Hello", "")
        user_pos = result.index("<|start_header_id|>user<|end_header_id|>")
        eot_pos = result.index("<|eot_id|>", user_pos)
        assert eot_pos > user_pos


class TestCallLlama:
    @patch("backend.agents.bedrock_client.boto3.client")
    def test_returns_generation_text(self, mock_boto_client):
        mock_boto_client.return_value = _make_mock_client("This is the answer.")
        result = call_llama("What is 2+2?")
        assert result == "This is the answer."

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_uses_region_from_env(self, mock_boto_client):
        mock_boto_client.return_value = _make_mock_client("ok")
        call_llama("test")
        mock_boto_client.assert_called_once_with(
            "bedrock-runtime", region_name=os.environ["AWS_REGION"]
        )

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_uses_model_id_from_env(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test")
        call_args = mock_client.invoke_model.call_args
        assert call_args.kwargs["modelId"] == os.environ["BEDROCK_MODEL_ID"]

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_prompt_formatted_in_body(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("Analyse this transaction.")
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert "Analyse this transaction." in body["prompt"]
        assert "<|begin_of_text|>" in body["prompt"]

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_system_prompt_in_body(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("user msg", system_prompt="You are a SAR analyst.")
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert "You are a SAR analyst." in body["prompt"]

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_default_temperature_is_0_1(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test")
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["temperature"] == 0.1

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_custom_temperature(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test", temperature=0.7)
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["temperature"] == 0.7

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_default_max_tokens_is_2048(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test")
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["max_gen_len"] == 2048

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_custom_max_tokens(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test", max_tokens=512)
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["max_gen_len"] == 512

    @patch("backend.agents.bedrock_client.boto3.client")
    def test_content_type_and_accept_headers(self, mock_boto_client):
        mock_client = _make_mock_client("ok")
        mock_boto_client.return_value = mock_client
        call_llama("test")
        call_args = mock_client.invoke_model.call_args
        assert call_args.kwargs["contentType"] == "application/json"
        assert call_args.kwargs["accept"] == "application/json"
