"""
Test configuration and fixtures for heic2jpg tests
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest
from PIL import Image
import io

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_image_data():
    """Create sample image data for testing"""
    image = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    return buffer.getvalue()

@pytest.fixture
def sample_heic_data():
    """Mock HEIC data for testing"""
    return b'mock_heic_data_for_testing'

@pytest.fixture
def mock_google_service():
    """Mock Google Drive service"""
    service = Mock()
    
    # Mock files().list() response
    list_response = {
        'files': [
            {
                'id': 'file1',
                'name': 'photo1.heic',
                'size': '1024000',
                'createdTime': '2023-01-01T00:00:00.000Z'
            },
            {
                'id': 'file2', 
                'name': 'photo2.HEIC',
                'size': '2048000',
                'createdTime': '2023-01-02T00:00:00.000Z'
            }
        ]
    }
    
    service.files().list().execute.return_value = list_response
    
    # Mock file download
    mock_request = Mock()
    service.files().get_media.return_value = mock_request
    
    return service

@pytest.fixture
def mock_credentials():
    """Mock Google credentials"""
    creds = Mock()
    creds.valid = True
    creds.expired = False
    return creds

@pytest.fixture
def env_vars():
    """Set environment variables for testing"""
    env_vars = {
        'GOOGLE_CREDENTIALS_FILE': 'test_credentials.json',
        'GOOGLE_TOKEN_FILE': 'test_token.json',
        'DEFAULT_QUALITY': '90',
        'DEFAULT_MAX_WIDTH': '1600',
        'DEFAULT_MAX_HEIGHT': '900',
        'DEFAULT_OUTPUT_DIR': 'test_output'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    yield env_vars
    
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]