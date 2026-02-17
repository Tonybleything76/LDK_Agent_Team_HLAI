
import os
import json
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock
from io import BytesIO

# Import the class to be tested
# Need to ensure sys.path is correct if running directly, but pytest handles it usually.
# Assuming orchestrator is importable.
from orchestrator.providers.openai_provider import OpenAIProvider

class TestOpenAIProviderJSONMode(unittest.TestCase):

    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key-123",
            "OPENAI_MODEL": "gpt-4-turbo-preview"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("orchestrator.providers.openai_provider.urllib.request.urlopen")
    def test_json_mode_basic(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": '{"success": true}'}}]
        }).encode("utf-8")
        
        # Mock context manager
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_response
        mock_ctx.__exit__.return_value = None
        
        mock_urlopen.return_value = mock_ctx

        provider = OpenAIProvider()
        result = provider.run("Test prompt")

        # Verify call arguments
        self.assertTrue(mock_urlopen.called)
        request_obj = mock_urlopen.call_args[0][0]
        data = request_obj.data
        if isinstance(data, bytes):
            payload = json.loads(data.decode("utf-8"))
        else:
            payload = json.loads(data)
        
        # 1. Check response_format
        self.assertEqual(payload.get("response_format"), {"type": "json_object"})
        
        # 2. Check system message
        system_msgs = [m for m in payload["messages"] if m["role"] == "system"]
        self.assertTrue(len(system_msgs) > 0)
        self.assertIn("Return ONLY valid JSON", system_msgs[0]["content"])
        
        # 3. Check temperature (default 0.2)
        # Note: We need to implement this in the provider code
        self.assertEqual(payload.get("temperature"), 0.2)
        
        self.assertEqual(result, '{"success": true}')

    @patch.dict(os.environ, {"OPENAI_TEMPERATURE": "0.5"})
    @patch("orchestrator.providers.openai_provider.urllib.request.urlopen")
    def test_temperature_configuration(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "{}"}}]
        }).encode("utf-8")
        
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_response
        mock_ctx.__exit__.return_value = None
        
        mock_urlopen.return_value = mock_ctx

        provider = OpenAIProvider()
        provider.run("test")

        request_obj = mock_urlopen.call_args[0][0]
        payload = json.loads(request_obj.data.decode("utf-8"))
        self.assertEqual(payload.get("temperature"), 0.5)

    @patch("orchestrator.providers.openai_provider.urllib.request.urlopen")
    def test_fallback_retry_logic(self, mock_urlopen):
        # 1. Setup the HTTPError for the first call
        error_json = json.dumps({"error": {"message": "Invalid response_format parameter", "type": "invalid_request_error"}})
        
        # We need a file-like object for error body
        class MockErrorStream(BytesIO):
             pass
        
        error_fp = MockErrorStream(error_json.encode("utf-8"))
        
        http_error = urllib.error.HTTPError(
            url="http://api.openai.com/v1/chat/completions",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=error_fp
        )
        
        # 2. Setup success for the second call
        success_response = MagicMock()
        success_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": '{"retry": "success"}'}}]
        }).encode("utf-8")
        
        mock_ctx_success = MagicMock()
        mock_ctx_success.__enter__.return_value = success_response
        mock_ctx_success.__exit__.return_value = None

        # Configure side_effect: first call raises, second returns success context
        mock_urlopen.side_effect = [http_error, mock_ctx_success]

        provider = OpenAIProvider()
        result = provider.run("Test prompt")

        self.assertEqual(result, '{"retry": "success"}')
        self.assertEqual(mock_urlopen.call_count, 2)
        
        # Validate First Call (failed one)
        req1 = mock_urlopen.call_args_list[0][0][0]
        payload1 = json.loads(req1.data.decode("utf-8"))
        self.assertEqual(payload1.get("response_format"), {"type": "json_object"})
        
        # Validate Second Call (retry)
        req2 = mock_urlopen.call_args_list[1][0][0]
        payload2 = json.loads(req2.data.decode("utf-8"))
        self.assertIsNone(payload2.get("response_format"))
        
        # Verify stronger system instruction
        system_msg_retry = next(m for m in payload2["messages"] if m["role"] == "system")
        self.assertIn("JSON ONLY", system_msg_retry["content"])


    @patch("orchestrator.providers.openai_provider.urllib.request.urlopen")
    def test_json_parse_retry(self, mock_urlopen):
        # 1. Setup invalid JSON response for first call
        invalid_response = MagicMock()
        invalid_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": 'Here is your JSON:\n```json\n{"foo": "bar"}\n```'}}]
        }).encode("utf-8")
        
        ctx_invalid = MagicMock()
        ctx_invalid.__enter__.return_value = invalid_response
        ctx_invalid.__exit__.return_value = None

        # 2. Setup valid JSON response for second call
        valid_response = MagicMock()
        valid_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": '{"foo": "bar"}'}}]
        }).encode("utf-8")
        
        ctx_valid = MagicMock()
        ctx_valid.__enter__.return_value = valid_response
        ctx_valid.__exit__.return_value = None

        mock_urlopen.side_effect = [ctx_invalid, ctx_valid]

        provider = OpenAIProvider()
        result = provider.run("Test prompt")

        # 3. Verify success
        self.assertEqual(result, '{"foo": "bar"}')
        
        # 4. Verify 2 calls
        self.assertEqual(mock_urlopen.call_count, 2)
        
        # 5. Verify retry payload contains repair instructions
        req2 = mock_urlopen.call_args_list[1][0][0]
        payload2 = json.loads(req2.data.decode("utf-8"))
        
        # Check that we appended the error context to the user message or system message
        # Implementation detail: we'll likely append to the last user message
        messages = payload2["messages"]
        last_message = messages[-1]["content"]
        self.assertIn("Previous response object failed to parse", last_message)
        self.assertIn("Here is your JSON", last_message) # The bad content

if __name__ == '__main__':
    unittest.main()
