#!/usr/bin/env python3
"""
HEIC to JPG Converter with Google Drive Integration
Converts HEIC files from Google Drive to compressed JPG files for blog use.
"""

import os
import io
from pathlib import Path
from typing import List, Optional, Tuple
import argparse
import logging
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from PIL import Image
import pillow_heif

# Load environment variables
load_dotenv()

# Enable HEIF support in Pillow
pillow_heif.register_heif_opener()

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class Config:
    """Configuration class for loading settings from environment variables"""
    
    @staticmethod
    def get_str(key: str, default: str = '') -> str:
        return os.getenv(key, default)
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @property
    def credentials_file(self) -> str:
        return self.get_str('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    @property
    def token_file(self) -> str:
        return self.get_str('GOOGLE_TOKEN_FILE', 'token.json')
    
    @property
    def default_quality(self) -> int:
        return self.get_int('DEFAULT_QUALITY', 85)
    
    @property
    def default_max_width(self) -> int:
        return self.get_int('DEFAULT_MAX_WIDTH', 1920)
    
    @property
    def default_max_height(self) -> int:
        return self.get_int('DEFAULT_MAX_HEIGHT', 1080)
    
    @property
    def default_output_dir(self) -> str:
        return self.get_str('DEFAULT_OUTPUT_DIR', 'converted')

class HeicToJpgConverter:
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def authenticate(self) -> None:
        """Authenticate with Google Drive API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        self.logger.info("Successfully authenticated with Google Drive")
    
    def list_heic_files(self, folder_id: Optional[str] = None) -> List[dict]:
        """List all HEIC files in Google Drive or specific folder"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        query = "mimeType='image/heic' or name contains '.heic' or name contains '.HEIC'"
        if folder_id:
            query = f"'{folder_id}' in parents and ({query})"
        
        results = self.service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, size, createdTime)"
        ).execute()
        
        files = results.get('files', [])
        self.logger.info(f"Found {len(files)} HEIC files")
        return files
    
    def download_file(self, file_id: str, file_name: str) -> bytes:
        """Download file from Google Drive"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        request = self.service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                self.logger.info(f"Downloading {file_name}: {int(status.progress() * 100)}%")
        
        return file_io.getvalue()
    
    def convert_heic_to_jpg(self, heic_data: bytes, quality: int = 85, max_size: Tuple[int, int] = (1920, 1080)) -> bytes:
        """Convert HEIC data to compressed JPG"""
        try:
            # Load HEIC image
            image = Image.open(io.BytesIO(heic_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if image is larger than max_size
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                self.logger.info(f"Resized image to {image.size}")
            
            # Save as JPG
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error converting HEIC to JPG: {e}")
            raise
    
    def delete_drive_file(self, file_id: str, file_name: str) -> bool:
        """Delete file from Google Drive"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info(f"Deleted original HEIC file: {file_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file {file_name}: {e}")
            return False
    
    def confirm_deletion(self, file_count: int) -> bool:
        """Ask user confirmation for deleting original HEIC files"""
        if file_count == 0:
            return False
        
        print(f"\n{file_count} HEIC files have been successfully converted to JPG.")
        response = input("Do you want to delete the original HEIC files from Google Drive? (y/N): ").strip().lower()
        return response in ['y', 'yes']
    
    def process_files(self, output_dir: str = 'converted', quality: int = 85, 
                     max_size: Tuple[int, int] = (1920, 1080), folder_id: Optional[str] = None,
                     auto_delete: bool = False):
        """Process all HEIC files and convert to JPG"""
        if not self.service:
            self.authenticate()
        
        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)
        
        # Get list of HEIC files
        heic_files = self.list_heic_files(folder_id)
        
        if not heic_files:
            self.logger.info("No HEIC files found")
            return
        
        processed_count = 0
        processed_files = []
        
        for file_info in heic_files:
            try:
                file_name = file_info['name']
                file_id = file_info['id']
                
                # Skip if already converted
                jpg_name = Path(file_name).stem + '.jpg'
                output_path = Path(output_dir) / jpg_name
                
                if output_path.exists():
                    self.logger.info(f"Skipping {file_name} (already exists)")
                    continue
                
                self.logger.info(f"Processing {file_name}...")
                
                # Download file
                heic_data = self.download_file(file_id, file_name)
                
                # Convert to JPG
                jpg_data = self.convert_heic_to_jpg(heic_data, quality, max_size)
                
                # Save JPG file
                with open(output_path, 'wb') as f:
                    f.write(jpg_data)
                
                original_size = len(heic_data)
                compressed_size = len(jpg_data)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                self.logger.info(
                    f"Converted {file_name} -> {jpg_name} "
                    f"({original_size//1024}KB -> {compressed_size//1024}KB, "
                    f"{compression_ratio:.1f}% smaller)"
                )
                
                processed_count += 1
                processed_files.append((file_id, file_name))
                
            except Exception as e:
                self.logger.error(f"Error processing {file_name}: {e}")
                continue
        
        self.logger.info(f"Successfully processed {processed_count} files")
        
        # Ask for deletion confirmation
        if processed_files:
            should_delete = auto_delete or self.confirm_deletion(len(processed_files))
            
            if should_delete:
                deleted_count = 0
                for file_id, file_name in processed_files:
                    if self.delete_drive_file(file_id, file_name):
                        deleted_count += 1
                
                self.logger.info(f"Deleted {deleted_count} original HEIC files from Google Drive")

def main():
    config = Config()
    
    parser = argparse.ArgumentParser(description='Convert HEIC files from Google Drive to JPG')
    parser.add_argument('--output', '-o', default=config.default_output_dir, help='Output directory')
    parser.add_argument('--quality', '-q', type=int, default=config.default_quality, help='JPG quality (1-100)')
    parser.add_argument('--max-width', type=int, default=config.default_max_width, help='Maximum width')
    parser.add_argument('--max-height', type=int, default=config.default_max_height, help='Maximum height')
    parser.add_argument('--folder-id', help='Google Drive folder ID to process')
    parser.add_argument('--credentials', default=config.credentials_file, help='Google API credentials file')
    parser.add_argument('--auto-delete', action='store_true', help='Automatically delete original HEIC files without confirmation')
    
    args = parser.parse_args()
    
    converter = HeicToJpgConverter(credentials_file=args.credentials, token_file=config.token_file)
    
    try:
        converter.process_files(
            output_dir=args.output,
            quality=args.quality,
            max_size=(args.max_width, args.max_height),
            folder_id=args.folder_id,
            auto_delete=args.auto_delete
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())