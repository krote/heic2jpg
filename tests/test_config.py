"""
Tests for Configuration class
"""

import os
import pytest
from heic2jpg import Config

class TestConfig:
    def test_default_values(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.credentials_file == 'credentials.json'
        assert config.token_file == 'token.json'
        assert config.default_quality == 85
        assert config.default_max_width == 1920
        assert config.default_max_height == 1080
        assert config.default_output_dir == 'converted'
    
    def test_environment_variables(self, env_vars):
        """Test configuration from environment variables"""
        config = Config()
        
        assert config.credentials_file == 'test_credentials.json'
        assert config.token_file == 'test_token.json'
        assert config.default_quality == 90
        assert config.default_max_width == 1600
        assert config.default_max_height == 900
        assert config.default_output_dir == 'test_output'
    
    def test_get_str_method(self):
        """Test get_str static method"""
        os.environ['TEST_STRING'] = 'test_value'
        
        result = Config.get_str('TEST_STRING', 'default')
        assert result == 'test_value'
        
        result = Config.get_str('NON_EXISTENT', 'default')
        assert result == 'default'
        
        if 'TEST_STRING' in os.environ:
            del os.environ['TEST_STRING']
    
    def test_get_int_method(self):
        """Test get_int static method"""
        os.environ['TEST_INT'] = '123'
        
        result = Config.get_int('TEST_INT', 0)
        assert result == 123
        
        result = Config.get_int('NON_EXISTENT', 456)
        assert result == 456
        
        # Test invalid integer
        os.environ['TEST_INVALID_INT'] = 'not_a_number'
        result = Config.get_int('TEST_INVALID_INT', 789)
        assert result == 789
        
        if 'TEST_INT' in os.environ:
            del os.environ['TEST_INT']
        if 'TEST_INVALID_INT' in os.environ:
            del os.environ['TEST_INVALID_INT']