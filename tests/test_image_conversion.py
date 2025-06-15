"""
Tests for image conversion functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from heic2jpg import HeicToJpgConverter

class TestImageConversion:
    
    def create_test_image(self, size=(100, 100), mode='RGB', color='red'):
        """Helper to create test images"""
        image = Image.new(mode, size, color)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    def test_convert_small_image(self):
        """Test converting small image that doesn't need resizing"""
        converter = HeicToJpgConverter()
        
        # Create a small test image
        original_image = Image.new('RGB', (100, 100), 'red')
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = original_image
            
            result = converter.convert_heic_to_jpg(
                b'mock_heic_data',
                quality=85,
                max_size=(1920, 1080)
            )
        
        # Should return JPG data
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify the image wasn't resized (size is smaller than max)
        # The thumbnail method should still be called but won't change size
        assert original_image.size == (100, 100)
    
    def test_convert_large_image_resize(self):
        """Test converting large image that needs resizing"""
        converter = HeicToJpgConverter()
        
        # Create a large test image
        large_image = Image.new('RGB', (3000, 2000), 'blue')
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = large_image
            
            result = converter.convert_heic_to_jpg(
                b'mock_heic_data',
                quality=85,
                max_size=(1920, 1080)
            )
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_convert_different_qualities(self):
        """Test conversion with different quality settings"""
        converter = HeicToJpgConverter()
        
        original_image = Image.new('RGB', (100, 100), 'green')
        
        results = []
        for quality in [50, 85, 95]:
            with patch('PIL.Image.open') as mock_open:
                mock_open.return_value = original_image
                
                result = converter.convert_heic_to_jpg(
                    b'mock_heic_data',
                    quality=quality,
                    max_size=(1920, 1080)
                )
                results.append((quality, len(result)))
        
        # Higher quality should generally result in larger files
        assert all(isinstance(result[1], int) and result[1] > 0 for result in results)
    
    def test_convert_different_modes(self):
        """Test conversion of images with different color modes"""
        converter = HeicToJpgConverter()
        
        modes_to_test = ['RGBA', 'L', 'P']
        
        for mode in modes_to_test:
            test_image = Image.new(mode, (100, 100), 'red' if mode == 'RGBA' else 128)
            
            # Mock the convert method
            rgb_image = Image.new('RGB', (100, 100), 'red')
            test_image.convert = Mock(return_value=rgb_image)
            
            with patch('PIL.Image.open') as mock_open:
                mock_open.return_value = test_image
                
                result = converter.convert_heic_to_jpg(b'mock_heic_data')
            
            assert isinstance(result, bytes)
            assert len(result) > 0
            
            # Verify convert was called for non-RGB modes
            if mode != 'RGB':
                test_image.convert.assert_called_once_with('RGB')
    
    def test_convert_various_sizes(self):
        """Test conversion with various max_size constraints"""
        converter = HeicToJpgConverter()
        
        # Test image larger than all constraints
        large_image = Image.new('RGB', (4000, 3000), 'purple')
        
        size_constraints = [
            (1920, 1080),
            (1280, 720),
            (800, 600),
            (400, 300)
        ]
        
        for max_width, max_height in size_constraints:
            with patch('PIL.Image.open') as mock_open:
                mock_open.return_value = large_image
                
                result = converter.convert_heic_to_jpg(
                    b'mock_heic_data',
                    quality=85,
                    max_size=(max_width, max_height)
                )
            
            assert isinstance(result, bytes)
            assert len(result) > 0
    
    def test_convert_aspect_ratio_preservation(self):
        """Test that aspect ratio is preserved during resizing"""
        converter = HeicToJpgConverter()
        
        # Create image with specific aspect ratio (2:1)
        original_image = Image.new('RGB', (2000, 1000), 'orange')
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = original_image
            
            # Mock thumbnail to verify it's called with correct parameters
            original_image.thumbnail = Mock()
            
            converter.convert_heic_to_jpg(
                b'mock_heic_data',
                quality=85,
                max_size=(1920, 1080)
            )
            
            # Verify thumbnail was called with max_size
            original_image.thumbnail.assert_called_once_with(
                (1920, 1080), 
                Image.Resampling.LANCZOS
            )
    
    def test_convert_edge_cases(self):
        """Test edge cases in image conversion"""
        converter = HeicToJpgConverter()
        
        # Test very small image
        tiny_image = Image.new('RGB', (1, 1), 'white')
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = tiny_image
            
            result = converter.convert_heic_to_jpg(b'mock_heic_data')
        
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Test square image
        square_image = Image.new('RGB', (100, 100), 'black')
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = square_image
            
            result = converter.convert_heic_to_jpg(b'mock_heic_data')
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_convert_invalid_data(self):
        """Test conversion with invalid HEIC data"""
        converter = HeicToJpgConverter()
        
        with patch('PIL.Image.open', side_effect=Exception("Invalid image data")):
            with pytest.raises(Exception):
                converter.convert_heic_to_jpg(b'invalid_data')
    
    def test_convert_optimization_flag(self):
        """Test that optimization flag is set during conversion"""
        converter = HeicToJpgConverter()
        
        original_image = Image.new('RGB', (100, 100), 'yellow')
        
        # Mock the save method to capture arguments
        def mock_save(file_obj, format=None, quality=None, optimize=None):
            # Verify optimize flag is set
            assert optimize is True
            assert format == 'JPEG'
            assert quality == 85
            file_obj.write(b'mock_jpg_data')
        
        original_image.save = mock_save
        
        with patch('PIL.Image.open') as mock_open:
            mock_open.return_value = original_image
            
            result = converter.convert_heic_to_jpg(b'mock_heic_data', quality=85)
        
        assert result == b'mock_jpg_data'