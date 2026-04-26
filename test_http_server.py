#!/usr/bin/env python3
"""Test cases for HttpServer.py - HTTP/1.0 request parsing and response handling."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from HttpServer import parse_http_request


class TestParseHttpRequest(unittest.TestCase):
    """Test HTTP request parsing functionality."""

    def test_valid_get_request_no_params(self):
        """Test parsing a valid GET request without query parameters."""
        raw = "GET /hello HTTP/1.0\r\nHost: localhost\r\nUser-Agent: test\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['path'], '/hello')
        self.assertEqual(result['headers'].get('host'), 'localhost')

    def test_valid_get_request_with_params(self):
        """Test parsing a valid GET request with query parameters."""
        raw = "GET /users?id=10&name=john HTTP/1.0\r\nHost: localhost\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['method'], 'GET')
        self.assertEqual(result['path'], '/users')
        self.assertEqual(result['params'].get('id'), '10')
        self.assertEqual(result['params'].get('name'), 'john')

    def test_valid_post_request_with_body(self):
        """Test parsing a valid POST request with form data."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Type: application/x-www-form-urlencoded\r\n"
               "Content-Length: 34\r\n"
               "\r\n"
               "username=yousef&password=secret123")
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['method'], 'POST')
        self.assertEqual(result['path'], '/submit')
        self.assertEqual(result['body'], 'username=yousef&password=secret123')
        self.assertEqual(result['post_data'].get('username'), 'yousef')

    def test_case_insensitive_headers(self):
        """Test that header keys are normalized to lowercase."""
        raw = "GET /hello HTTP/1.0\r\nHost: localhost\r\nUser-Agent: test\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIn('host', result['headers'])
        self.assertIn('user-agent', result['headers'])

    def test_content_length_mismatch(self):
        """Test that mismatched Content-Length returns None."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Length: 100\r\n"
               "\r\n"
               "short")
        result = parse_http_request(raw)
        self.assertIsNone(result)

    def test_content_length_correct(self):
        """Test that correct Content-Length passes validation."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Length: 5\r\n"
               "\r\n"
               "hello")
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['body'], 'hello')

    def test_post_with_wrong_content_type(self):
        """Test POST with wrong Content-Type doesn't parse body."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Type: application/json\r\n"
               "Content-Length: 5\r\n"
               "\r\n"
               "hello")
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['body'], 'hello')
        self.assertEqual(result['post_data'], {})

    def test_post_without_content_type(self):
        """Test POST without proper Content-Type doesn't parse body."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Length: 5\r\n"
               "\r\n"
               "hello")
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['post_data'], {})

    def test_invalid_request_line(self):
        """Test parsing a request with invalid request line."""
        raw = "INVALID\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNone(result)


class TestServerResponseLogic(unittest.TestCase):
    """Test the server's response logic for different endpoints."""

    @patch('HttpServer.ReliableUDP')
    def test_server_get_valid_user_id_in_range(self, mock_udp_class):
        """Test /users?id=X where 10<=X<=100."""
        raw = "GET /users?id=50 HTTP/1.0\r\nHost: localhost\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['path'], '/users')
        self.assertEqual(result['params'].get('id'), '50')

    @patch('HttpServer.ReliableUDP')
    def test_server_response_to_post_submit(self, mock_udp_class):
        """Test server handles POST /submit correctly."""
        raw = ("POST /submit HTTP/1.0\r\n"
               "Host: localhost\r\n"
               "Content-Type: application/x-www-form-urlencoded\r\n"
               "Content-Length: 34\r\n"
               "\r\n"
               "username=yousef&password=secret123")
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['method'], 'POST')
        self.assertEqual(result['path'], '/submit')

    @patch('HttpServer.ReliableUDP')
    def test_server_response_to_hello_with_params(self, mock_udp_class):
        """Test server handles GET /hello with query params."""
        raw = "GET /hello?name=alice&age=25 HTTP/1.0\r\nHost: localhost\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['path'], '/hello')
        self.assertEqual(result['params'].get('name'), 'alice')

    @patch('HttpServer.ReliableUDP')
    def test_server_rejects_out_of_range_user_id(self, mock_udp_class):
        """Test /users?id=101 (above range) should be rejected."""
        raw = "GET /users?id=101 HTTP/1.0\r\nHost: localhost\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['params'].get('id'), '101')

    @patch('HttpServer.ReliableUDP')
    def test_server_rejects_invalid_path(self, mock_udp_class):
        """Test server rejects request to invalid path."""
        raw = "GET /invalid HTTP/1.0\r\nHost: localhost\r\n\r\n"
        result = parse_http_request(raw)
        self.assertIsNotNone(result)
        self.assertEqual(result['path'], '/invalid')


if __name__ == '__main__':
    unittest.main(verbosity=2)
