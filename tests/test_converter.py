"""
Tests for HeicToJpgConverter class
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PIL import Image
import io

from heic2jpg import HeicToJpgConverter

class TestHeicToJpgConverter:
    
    def test_init(self):
        """Test converter initialization"""
        converter = HeicToJpgConverter()
        
        assert converter.credentials_file == 'credentials.json'
        assert converter.token_file == 'token.json'
        assert converter.service is None
        assert converter.logger is not None
    
    def test_init_custom_files(self):
        """Test converter initialization with custom files"""
        converter = HeicToJpgConverter(
            credentials_file='custom_creds.json',
            token_file='custom_token.json'
        )
        
        assert converter.credentials_file == 'custom_creds.json'
        assert converter.token_file == 'custom_token.json'
    
    @patch('heic2jpg.build')
    @patch('heic2jpg.Credentials')
    def test_authenticate_with_existing_valid_token(self, mock_credentials, mock_build):
        """Test authentication with existing valid token"""
        converter = HeicToJpgConverter()
        
        # Mock existing valid credentials
        mock_creds = Mock()
        mock_creds.valid = True
        mock_credentials.from_authorized_user_file.return_value = mock_creds
        
        # Mock service
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        with patch('os.path.exists', return_value=True):
            converter.authenticate()
        
        assert converter.service == mock_service
        mock_credentials.from_authorized_user_file.assert_called_once_with(
            converter.token_file, ['https://www.googleapis.com/auth/drive.readonly']
        )
    
    @patch('heic2jpg.build')
    @patch('heic2jpg.InstalledAppFlow')
    @patch('heic2jpg.Credentials')
    def test_authenticate_new_credentials(self, mock_credentials, mock_flow, mock_build):
        """Test authentication with new credentials"""
        converter = HeicToJpgConverter()
        
        # Mock no existing token
        mock_credentials.from_authorized_user_file.return_value = None
        
        # Mock flow
        mock_flow_instance = Mock()
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        mock_creds = Mock()
        mock_creds.to_json.return_value = '{"token": "test"}'
        mock_flow_instance.run_local_server.return_value = mock_creds
        
        # Mock service
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = lambda path: path == converter.credentials_file
            with patch('builtins.open', create=True) as mock_open:
                converter.authenticate()
        
        assert converter.service == mock_service
        mock_flow.from_client_secrets_file.assert_called_once()
    
    def test_authenticate_no_credentials_file(self):
        """Test authentication failure when credentials file doesn't exist"""
        converter = HeicToJpgConverter()
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Credentials file"):
                converter.authenticate()
    
    def test_list_heic_files(self, mock_google_service):
        """Test listing HEIC files"""
        converter = HeicToJpgConverter()
        converter.service = mock_google_service
        
        files = converter.list_heic_files()
        
        assert len(files) == 2
        assert files[0]['name'] == 'photo1.heic'
        assert files[1]['name'] == 'photo2.HEIC'
        
        mock_google_service.files().list.assert_called_once()
    
    def test_list_heic_files_with_folder_id(self, mock_google_service):
        """Test listing HEIC files in specific folder"""
        converter = HeicToJpgConverter()
        converter.service = mock_google_service
        
        folder_id = 'test_folder_id'
        files = converter.list_heic_files(folder_id)
        
        # Check that folder ID was included in query
        call_args = mock_google_service.files().list.call_args
        query = call_args[1]['q']
        assert folder_id in query
    
    def test_list_heic_files_not_authenticated(self):
        """Test listing files without authentication"""
        converter = HeicToJpgConverter()
        
        with pytest.raises(RuntimeError, match="Not authenticated"):
            converter.list_heic_files()
    
    @patch('heic2jpg.MediaIoBaseDownload')
    def test_download_file(self, mock_download, mock_google_service):
        """Test file download"""
        converter = HeicToJpgConverter()
        converter.service = mock_google_service
        
        # Mock download
        mock_downloader = Mock()
        mock_downloader.next_chunk.side_effect = [
            (Mock(progress=lambda: 0.5), False),
            (Mock(progress=lambda: 1.0), True)
        ]
        mock_download.return_value = mock_downloader
        
        # Mock file data
        test_data = b'test_file_data'
        with patch('io.BytesIO') as mock_bytesio:
            mock_file_io = Mock()
            mock_file_io.getvalue.return_value = test_data
            mock_bytesio.return_value = mock_file_io
            
            result = converter.download_file('file123', 'test.heic')
        
        assert result == test_data
        mock_google_service.files().get_media.assert_called_once_with(fileId='file123')
    
    def test_download_file_not_authenticated(self):
        """Test file download without authentication"""
        converter = HeicToJpgConverter()
        
        with pytest.raises(RuntimeError, match="Not authenticated"):
            converter.download_file('file123', 'test.heic')
    
    def test_convert_heic_to_jpg(self, sample_image_data):
        """Test HEIC to JPG conversion"""
        converter = HeicToJpgConverter()
        
        with patch('PIL.Image.open') as mock_open:
            # Mock image
            mock_image = Mock()
            mock_image.mode = 'RGB'
            mock_image.size = (100, 100)
            mock_image.thumbnail = Mock()
            
            # Mock save
            def mock_save(file_obj, format=None, quality=None, optimize=None):
                file_obj.write(sample_image_data)
            
            mock_image.save = mock_save
            mock_open.return_value = mock_image
            
            result = converter.convert_heic_to_jpg(b'mock_heic_data')
        
        assert isinstance(result, bytes)
        assert len(result) > 0
        mock_image.thumbnail.assert_called_once_with((1920, 1080), Image.Resampling.LANCZOS)
    
    def test_convert_heic_to_jpg_with_resize(self, sample_image_data):
        """Test HEIC to JPG conversion with resizing"""
        converter = HeicToJpgConverter()
        
        with patch('PIL.Image.open') as mock_open:
            # Mock large image
            mock_image = Mock()
            mock_image.mode = 'RGB'
            mock_image.size = (3000, 2000)  # Larger than max_size
            mock_image.thumbnail = Mock()
            
            def mock_save(file_obj, format=None, quality=None, optimize=None):
                file_obj.write(sample_image_data)
            
            mock_image.save = mock_save
            mock_open.return_value = mock_image
            
            result = converter.convert_heic_to_jpg(
                b'mock_heic_data',
                quality=90,
                max_size=(1600, 900)
            )
        
        assert isinstance(result, bytes)
        mock_image.thumbnail.assert_called_once_with((1600, 900), Image.Resampling.LANCZOS)
    
    def test_convert_heic_to_jpg_convert_mode(self, sample_image_data):
        """Test HEIC to JPG conversion with mode conversion"""
        converter = HeicToJpgConverter()
        
        with patch('PIL.Image.open') as mock_open:
            # Mock image with non-RGB mode
            mock_image = Mock()
            mock_image.mode = 'RGBA'
            mock_image.size = (100, 100)
            
            mock_rgb_image = Mock()
            mock_rgb_image.mode = 'RGB'
            mock_rgb_image.size = (100, 100)
            mock_rgb_image.thumbnail = Mock()
            
            def mock_save(file_obj, format=None, quality=None, optimize=None):
                file_obj.write(sample_image_data)
            
            mock_rgb_image.save = mock_save
            mock_image.convert.return_value = mock_rgb_image
            mock_open.return_value = mock_image
            
            result = converter.convert_heic_to_jpg(b'mock_heic_data')
        
        assert isinstance(result, bytes)
        mock_image.convert.assert_called_once_with('RGB')
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_process_files(self, mock_exists, mock_mkdir, temp_dir, sample_image_data, mock_google_service):
        """Test processing files"""
        converter = HeicToJpgConverter()
        converter.service = mock_google_service
        
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        with patch.object(converter, 'download_file') as mock_download:
            mock_download.return_value = b'mock_heic_data'
            
            with patch.object(converter, 'convert_heic_to_jpg') as mock_convert:
                mock_convert.return_value = sample_image_data
                
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = Mock()
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    converter.process_files(output_dir=temp_dir)
        
        # Verify calls
        assert mock_download.call_count == 2  # Two files in mock service
        assert mock_convert.call_count == 2
        assert mock_file.write.call_count == 2