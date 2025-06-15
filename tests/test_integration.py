"""
Integration tests for Google Drive API functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from heic2jpg import HeicToJpgConverter

class TestGoogleDriveIntegration:
    """Integration tests for Google Drive functionality"""
    
    @pytest.mark.integration
    def test_full_authentication_flow(self):
        """Test complete authentication flow (mocked)"""
        converter = HeicToJpgConverter()
        
        with patch('heic2jpg.os.path.exists') as mock_exists:
            with patch('heic2jpg.Credentials') as mock_credentials:
                with patch('heic2jpg.InstalledAppFlow') as mock_flow:
                    with patch('heic2jpg.build') as mock_build:
                        with patch('builtins.open', create=True):
                            
                            # Mock no existing token
                            mock_exists.return_value = True
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
                            
                            converter.authenticate()
                            
                            assert converter.service == mock_service
                            mock_flow.from_client_secrets_file.assert_called_once()
                            mock_flow_instance.run_local_server.assert_called_once()
    
    @pytest.mark.integration
    def test_list_files_with_pagination(self):
        """Test listing files with pagination (mocked)"""
        converter = HeicToJpgConverter()
        
        # Mock service with paginated response
        mock_service = Mock()
        
        # First call returns nextPageToken
        first_response = {
            'files': [
                {'id': 'file1', 'name': 'photo1.heic', 'size': '1024', 'createdTime': '2023-01-01T00:00:00.000Z'}
            ],
            'nextPageToken': 'next_token_123'
        }
        
        # Second call returns remaining files
        second_response = {
            'files': [
                {'id': 'file2', 'name': 'photo2.heic', 'size': '2048', 'createdTime': '2023-01-02T00:00:00.000Z'}
            ]
        }
        
        mock_service.files().list().execute.side_effect = [first_response, second_response]
        converter.service = mock_service
        
        files = converter.list_heic_files()
        
        # Should return files from first call only (our implementation doesn't handle pagination yet)
        assert len(files) == 1
        assert files[0]['name'] == 'photo1.heic'
    
    @pytest.mark.integration
    def test_download_large_file_chunks(self):
        """Test downloading large file in chunks"""
        converter = HeicToJpgConverter()
        
        mock_service = Mock()
        converter.service = mock_service
        
        # Mock chunked download
        with patch('heic2jpg.MediaIoBaseDownload') as mock_download:
            mock_downloader = Mock()
            
            # Mock multiple chunks
            mock_status_1 = Mock()
            mock_status_1.progress.return_value = 0.3
            mock_status_2 = Mock()
            mock_status_2.progress.return_value = 0.7
            mock_status_3 = Mock()
            mock_status_3.progress.return_value = 1.0
            
            mock_downloader.next_chunk.side_effect = [
                (mock_status_1, False),
                (mock_status_2, False),
                (mock_status_3, True)
            ]
            
            mock_download.return_value = mock_downloader
            
            # Mock file data
            test_data = b'large_file_data_chunk_by_chunk'
            with patch('io.BytesIO') as mock_bytesio:
                mock_file_io = Mock()
                mock_file_io.getvalue.return_value = test_data
                mock_bytesio.return_value = mock_file_io
                
                result = converter.download_file('large_file_id', 'large_file.heic')
            
            assert result == test_data
            assert mock_downloader.next_chunk.call_count == 3
    
    @pytest.mark.integration
    def test_process_files_end_to_end(self, temp_dir):
        """Test complete file processing workflow"""
        converter = HeicToJpgConverter()
        
        # Mock authenticated service
        mock_service = Mock()
        converter.service = mock_service
        
        # Mock file list response
        mock_files = [
            {'id': 'file1', 'name': 'photo1.heic', 'size': '1024000', 'createdTime': '2023-01-01T00:00:00.000Z'},
            {'id': 'file2', 'name': 'photo2.HEIC', 'size': '2048000', 'createdTime': '2023-01-02T00:00:00.000Z'}
        ]
        mock_service.files().list().execute.return_value = {'files': mock_files}
        
        # Mock download
        with patch.object(converter, 'download_file') as mock_download:
            mock_download.return_value = b'mock_heic_data'
            
            # Mock conversion
            with patch.object(converter, 'convert_heic_to_jpg') as mock_convert:
                mock_convert.return_value = b'mock_jpg_data'
                
                # Run process_files
                converter.process_files(output_dir=temp_dir)
                
                # Verify files were processed
                assert mock_download.call_count == 2
                assert mock_convert.call_count == 2
                
                # Check output files exist
                output_path_1 = Path(temp_dir) / 'photo1.jpg'
                output_path_2 = Path(temp_dir) / 'photo2.jpg'
                
                assert output_path_1.exists()
                assert output_path_2.exists()
    
    @pytest.mark.integration
    def test_error_handling_during_processing(self, temp_dir):
        """Test error handling during file processing"""
        converter = HeicToJpgConverter()
        
        # Mock authenticated service
        mock_service = Mock()
        converter.service = mock_service
        
        # Mock file list with multiple files
        mock_files = [
            {'id': 'file1', 'name': 'good_photo.heic', 'size': '1024000', 'createdTime': '2023-01-01T00:00:00.000Z'},
            {'id': 'file2', 'name': 'bad_photo.heic', 'size': '2048000', 'createdTime': '2023-01-02T00:00:00.000Z'},
            {'id': 'file3', 'name': 'another_good.heic', 'size': '1536000', 'createdTime': '2023-01-03T00:00:00.000Z'}
        ]
        mock_service.files().list().execute.return_value = {'files': mock_files}
        
        # Mock download - second file fails
        def mock_download_side_effect(file_id, file_name):
            if file_id == 'file2':
                raise Exception("Download failed")
            return b'mock_heic_data'
        
        with patch.object(converter, 'download_file') as mock_download:
            mock_download.side_effect = mock_download_side_effect
            
            # Mock conversion
            with patch.object(converter, 'convert_heic_to_jpg') as mock_convert:
                mock_convert.return_value = b'mock_jpg_data'
                
                # Run process_files - should handle error gracefully
                converter.process_files(output_dir=temp_dir)
                
                # Verify only successful files were processed
                assert mock_download.call_count == 3  # All attempted
                assert mock_convert.call_count == 2   # Only successful ones
                
                # Check output files
                good_file_1 = Path(temp_dir) / 'good_photo.jpg'
                bad_file = Path(temp_dir) / 'bad_photo.jpg'
                good_file_2 = Path(temp_dir) / 'another_good.jpg'
                
                assert good_file_1.exists()
                assert not bad_file.exists()  # Failed download
                assert good_file_2.exists()
    
    @pytest.mark.integration
    def test_skip_existing_files(self, temp_dir):
        """Test skipping files that already exist"""
        converter = HeicToJpgConverter()
        
        # Create existing output file
        existing_file = Path(temp_dir) / 'existing.jpg'
        existing_file.write_bytes(b'existing_content')
        
        # Mock authenticated service
        mock_service = Mock()
        converter.service = mock_service
        
        # Mock file list
        mock_files = [
            {'id': 'file1', 'name': 'existing.heic', 'size': '1024000', 'createdTime': '2023-01-01T00:00:00.000Z'},
            {'id': 'file2', 'name': 'new_file.heic', 'size': '2048000', 'createdTime': '2023-01-02T00:00:00.000Z'}
        ]
        mock_service.files().list().execute.return_value = {'files': mock_files}
        
        with patch.object(converter, 'download_file') as mock_download:
            mock_download.return_value = b'mock_heic_data'
            
            with patch.object(converter, 'convert_heic_to_jpg') as mock_convert:
                mock_convert.return_value = b'mock_jpg_data'
                
                converter.process_files(output_dir=temp_dir)
                
                # Should only process the new file
                assert mock_download.call_count == 1
                assert mock_convert.call_count == 1
                
                # Verify existing file wasn't overwritten
                assert existing_file.read_bytes() == b'existing_content'
    
    @pytest.mark.integration
    def test_folder_specific_processing(self):
        """Test processing files from specific folder"""
        converter = HeicToJpgConverter()
        
        # Mock authenticated service
        mock_service = Mock()
        converter.service = mock_service
        
        folder_id = 'specific_folder_123'
        
        # Should include folder ID in query
        mock_service.files().list().execute.return_value = {'files': []}
        
        converter.process_files(folder_id=folder_id)
        
        # Verify folder ID was used in query
        call_args = mock_service.files().list.call_args
        query = call_args[1]['q']
        assert folder_id in query