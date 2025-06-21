"""Tests for response transformation functionality."""

from src.automatic.response_transformer import ResponseTransformer


class TestResponseTransformer:
    def setup_method(self):
        self.transformer = ResponseTransformer()

    def test_string_error_transforms_to_rfc9457(self):
        """Test that string errors are transformed to RFC 9457 format."""
        result = self.transformer.transform_error("User not found", 404)

        expected = {"type": "about:blank", "title": "User not found", "status": 404}
        assert result == expected

    def test_dict_error_passed_through_if_rfc9457_compliant(self):
        """Test that RFC 9457 compliant dict errors are passed through."""
        error_dict = {
            "type": "https://api.example.com/errors/user-not-found",
            "title": "User Not Found",
            "detail": "User with ID 123 does not exist",
            "status": 404,
        }

        result = self.transformer.transform_error(error_dict, 404)
        assert result == error_dict

    def test_dict_error_enhanced_to_rfc9457_if_missing_fields(self):
        """Test that dict errors missing RFC 9457 fields are enhanced."""
        error_dict = {"message": "User not found"}

        result = self.transformer.transform_error(error_dict, 404)

        expected = {
            "type": "about:blank",
            "title": "User not found",
            "status": 404,
            "message": "User not found",  # Original field preserved
        }
        assert result == expected

    def test_success_responses_not_transformed(self):
        """Test that success responses (2xx) are not transformed."""
        data = {"user_id": 1, "name": "Alice"}

        result = self.transformer.transform_response(data, 200)
        assert result == data

    def test_is_error_status_detection(self):
        """Test error status code detection."""
        assert self.transformer.is_error_status(400) is True
        assert self.transformer.is_error_status(404) is True
        assert self.transformer.is_error_status(500) is True
        assert self.transformer.is_error_status(200) is False
        assert self.transformer.is_error_status(201) is False
        assert self.transformer.is_error_status(299) is False

    def test_transform_response_calls_transform_error_for_errors(self):
        """Test that transform_response delegates to transform_error for error statuses."""
        result = self.transformer.transform_response("Bad request", 400)

        expected = {"type": "about:blank", "title": "Bad request", "status": 400}
        assert result == expected
