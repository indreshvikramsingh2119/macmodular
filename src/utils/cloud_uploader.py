"""
Cloud Uploader Module for ECG Reports
Supports multiple cloud storage services for automatic report backup
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
# 1) Load from current working directory (if running from project root)
load_dotenv()
# 2) Also attempt to load from project root explicitly (works when app starts from elsewhere)
try:
    this_file = Path(__file__).resolve()
    project_root = this_file.parents[2] if len(this_file.parents) >= 3 else this_file.parent
    root_env = project_root / '.env'
    if root_env.exists():
        load_dotenv(dotenv_path=str(root_env), override=False)
    else:
        # Fallback: also try one directory up (in case of unusual packaging)
        alt_env = project_root.parent / '.env'
        if alt_env.exists():
            load_dotenv(dotenv_path=str(alt_env), override=False)
except Exception:
    # Best-effort; silently continue if path resolution fails
    pass

# Final fallback: manually parse .env if python-dotenv misses it (rare edge cases)
def _manual_env_load(env_path: Path):
    try:
        if env_path.exists():
            with env_path.open('r', encoding='utf-8', errors='ignore') as f:
                for raw in f:
                    line = raw.replace('\ufeff', '')  # strip BOM if present
                    line = line.replace('＝', '=')      # normalize unicode equals
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        # Force override to ensure latest values are used
                        if k:
                            os.environ[k] = v
    except Exception:
        pass

try:
    _manual_env_load(root_env)
except Exception:
    pass


class CloudUploader:
    """Handle uploading ECG reports to cloud storage"""
    
    def __init__(self):
        self.cloud_service = os.getenv('CLOUD_SERVICE', 'none').lower()
        self.upload_enabled = os.getenv('CLOUD_UPLOAD_ENABLED', 'false').lower() == 'true'
        
        # AWS S3 Configuration
        self.s3_bucket = os.getenv('AWS_S3_BUCKET')
        self.s3_region = os.getenv('AWS_S3_REGION', 'us-east-1')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Azure Blob Storage Configuration
        self.azure_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.azure_container = os.getenv('AZURE_CONTAINER_NAME', 'ecg-reports')
        
        # Google Cloud Storage Configuration
        self.gcs_bucket = os.getenv('GCS_BUCKET_NAME')
        self.gcs_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Custom API Endpoint Configuration
        self.api_endpoint = os.getenv('CLOUD_API_ENDPOINT')
        self.api_key = os.getenv('CLOUD_API_KEY')
        
        # FTP/SFTP Configuration
        self.ftp_host = os.getenv('FTP_HOST')
        self.ftp_port = int(os.getenv('FTP_PORT', '21'))
        self.ftp_username = os.getenv('FTP_USERNAME')
        self.ftp_password = os.getenv('FTP_PASSWORD')
        self.ftp_remote_path = os.getenv('FTP_REMOTE_PATH', '/ecg-reports')
        
        # Dropbox Configuration
        self.dropbox_token = os.getenv('DROPBOX_ACCESS_TOKEN')
        
        # Log file for upload tracking
        self.upload_log_path = "reports/upload_log.json"

    def reload_config(self):
        """Re-read .env from CWD and project root and refresh fields."""
        try:
            load_dotenv(override=True)
            this_file = Path(__file__).resolve()
            project_root = this_file.parents[2] if len(this_file.parents) >= 3 else this_file.parent
            root_env = project_root / '.env'
            if root_env.exists():
                load_dotenv(dotenv_path=str(root_env), override=True)
            # Manual fallback parse as well
            try:
                _manual_env_load(root_env)
            except Exception:
                pass
            # Also try CWD .env
            try:
                cwd_env = Path(os.getcwd()) / '.env'
                _manual_env_load(cwd_env)
            except Exception:
                pass
        except Exception:
            pass
        self.cloud_service = os.getenv('CLOUD_SERVICE', 'none').lower()
        self.upload_enabled = os.getenv('CLOUD_UPLOAD_ENABLED', 'false').lower() == 'true'
        self.s3_bucket = os.getenv('AWS_S3_BUCKET')
        self.s3_region = os.getenv('AWS_S3_REGION', 'us-east-1')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

    def get_config_snapshot(self):
        return {
            'cloud_service': self.cloud_service,
            'upload_enabled': self.upload_enabled,
            's3_bucket': self.s3_bucket,
            's3_region': self.s3_region,
            'aws_access_key_set': bool(self.aws_access_key),
            'aws_secret_key_set': bool(self.aws_secret_key),
        }
        
    def is_configured(self):
        """Check if cloud upload is properly configured"""
        if not self.upload_enabled:
            return False
            
        if self.cloud_service == 's3':
            return bool(self.s3_bucket and self.aws_access_key and self.aws_secret_key)
        elif self.cloud_service == 'azure':
            return bool(self.azure_connection_string)
        elif self.cloud_service == 'gcs':
            return bool(self.gcs_bucket and self.gcs_credentials_path)
        elif self.cloud_service == 'api':
            return bool(self.api_endpoint)
        elif self.cloud_service == 'ftp' or self.cloud_service == 'sftp':
            return bool(self.ftp_host and self.ftp_username)
        elif self.cloud_service == 'dropbox':
            return bool(self.dropbox_token)
        
        return False
    
    def upload_report(self, file_path, metadata=None):
        """
        Upload ONLY reports, metrics, and report files to AWS S3
        Does NOT upload: session logs, debug data, crash logs, temp files
        
        Args:
            file_path (str): Path to the report file (PDF, JSON, etc.)
            metadata (dict): Optional metadata about the report
            
        Returns:
            dict: Upload result with status, url, and error if any
        """
        if not self.upload_enabled:
            return {"status": "disabled", "message": "Cloud upload is disabled"}
            
        if not self.is_configured():
            return {"status": "error", "message": f"Cloud service '{self.cloud_service}' is not properly configured"}
        
        try:
            # Check if this is a report file (PDF or JSON report)
            file_ext = Path(file_path).suffix.lower()
            file_basename = os.path.basename(file_path).lower()
            
            # ONLY upload reports and metrics - filter out everything else
            allowed_extensions = ['.pdf', '.json']
            is_report = file_ext in allowed_extensions and 'report' in file_basename
            is_metric = file_ext == '.json' and 'metric' in file_basename
            
            if not (is_report or is_metric):
                return {
                    "status": "skipped",
                    "message": f"File {file_basename} is not a report or metric file - not uploaded"
                }
            
            # Prepare metadata - ONLY include essential report information
            upload_metadata = {
                "filename": os.path.basename(file_path),
                "uploaded_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
                "file_type": Path(file_path).suffix,
            }
            
            # Only add specific metadata fields if provided
            if metadata:
                # Filter metadata to only include report-related fields
                allowed_keys = [
                    'patient_name', 'patient_age', 'report_date', 'machine_serial',
                    'heart_rate', 'pr_interval', 'qrs_duration', 'qtc_interval',
                    'st_segment', 'qrs_axis'
                ]
                filtered_metadata = {k: v for k, v in metadata.items() if k in allowed_keys}
                upload_metadata.update(filtered_metadata)
            
            # Upload based on configured service
            if self.cloud_service == 's3':
                result = self._upload_to_s3(file_path, upload_metadata)
            elif self.cloud_service == 'azure':
                result = self._upload_to_azure(file_path, upload_metadata)
            elif self.cloud_service == 'gcs':
                result = self._upload_to_gcs(file_path, upload_metadata)
            elif self.cloud_service == 'api':
                result = self._upload_to_api(file_path, upload_metadata)
            elif self.cloud_service == 'ftp':
                result = self._upload_to_ftp(file_path, upload_metadata, use_sftp=False)
            elif self.cloud_service == 'sftp':
                result = self._upload_to_ftp(file_path, upload_metadata, use_sftp=True)
            elif self.cloud_service == 'dropbox':
                result = self._upload_to_dropbox(file_path, upload_metadata)
            else:
                result = {"status": "error", "message": f"Unknown cloud service: {self.cloud_service}"}
            
            # Log the upload
            if result.get("status") == "success":
                self._log_upload(file_path, result, upload_metadata)
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def upload_user_signup(self, user_data):
        """
        Upload user signup details to cloud storage
        
        Args:
            user_data (dict): Dictionary containing user signup information
                             {username, full_name, age, gender, phone, address, serial_number, registered_at}
        
        Returns:
            dict: Upload result with status and details
        """
        print(f"🔵 upload_user_signup called with data: {user_data}")
        
        if not self.upload_enabled:
            msg = "Cloud upload is disabled"
            print(f"❌ {msg}")
            return {"status": "disabled", "message": msg}
        
        if not self.is_configured():
            msg = f"Cloud service '{self.cloud_service}' is not properly configured"
            print(f"❌ {msg}")
            return {"status": "error", "message": msg}
        
        if not user_data or not isinstance(user_data, dict):
            msg = "Invalid user data"
            print(f"❌ {msg}")
            return {"status": "error", "message": msg}
        
        try:
            # Create a JSON file with user signup details
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            username = user_data.get('username', 'unknown')
            filename = f"user_signup_{username}_{timestamp}.json"
            
            # Create temp directory if it doesn't exist
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, filename)
            
            print(f"📝 Creating user signup file: {file_path}")
            
            # Add timestamp to user data
            upload_data = user_data.copy()
            upload_data['uploaded_at'] = datetime.now().isoformat()
            
            # Write user data to JSON file
            with open(file_path, 'w') as f:
                json.dump(upload_data, f, indent=2)
            
            print(f"✅ User signup file created successfully")
            
            # Upload to cloud
            metadata = {
                'type': 'user_signup',
                'username': username,
                'uploaded_at': datetime.now().isoformat()
            }
            
            print(f"☁️ Uploading to {self.cloud_service}...")
            
            result = None
            if self.cloud_service == 's3':
                result = self._upload_to_s3(file_path, metadata)
            elif self.cloud_service == 'azure':
                result = self._upload_to_azure(file_path, metadata)
            elif self.cloud_service == 'gcs':
                result = self._upload_to_gcs(file_path, metadata)
            elif self.cloud_service == 'api':
                result = self._upload_to_api(file_path, metadata)
            elif self.cloud_service == 'ftp':
                result = self._upload_to_ftp(file_path, metadata)
            elif self.cloud_service == 'sftp':
                result = self._upload_to_ftp(file_path, metadata, use_sftp=True)
            elif self.cloud_service == 'dropbox':
                result = self._upload_to_dropbox(file_path, metadata)
            else:
                result = {"status": "error", "message": f"Unknown cloud service: {self.cloud_service}"}
            
            print(f"📤 Upload result: {result}")
            
            # Clean up temp file
            try:
                os.remove(file_path)
                print(f"🗑️ Temp file removed: {file_path}")
            except Exception as cleanup_err:
                print(f"⚠️ Could not remove temp file: {cleanup_err}")
            
            # Log upload
            if result and result.get("status") == "success":
                self._log_upload(filename, result, metadata)
                print(f"✅ User signup uploaded to {self.cloud_service}: {username}")
            else:
                print(f"❌ Upload failed: {result}")
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to upload user signup: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"Stack trace: {traceback.format_exc()}")
            return {"status": "error", "message": error_msg}
    
    def _upload_to_s3(self, file_path, metadata):
        """Upload to AWS S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.s3_region
            )
            
            # Generate S3 key
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"ecg-reports/{timestamp}/{filename}"
            
            # Upload file
            s3_client.upload_file(
                file_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={'Metadata': {k: str(v) for k, v in metadata.items()}}
            )
            
            # Generate presigned URL (optional)
            url = f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{s3_key}"
            
            return {
                "status": "success",
                "service": "s3",
                "url": url,
                "key": s3_key,
                "bucket": self.s3_bucket
            }
            
        except ImportError:
            return {"status": "error", "message": "boto3 not installed. Run: pip install boto3"}
        except ClientError as e:
            return {"status": "error", "message": f"S3 upload failed: {str(e)}"}

    def list_reports(self, prefix: str = "ecg-reports/"):
        """List report objects in S3 (PDF and JSON under prefix)."""
        if not (self.upload_enabled and self.cloud_service == 's3' and self.s3_bucket):
            return {"status": "error", "message": "S3 not configured"}
        try:
            import boto3
            s3 = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.s3_region
            )
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
            items = []
            for page in pages:
                for obj in page.get('Contents', []) or []:
                    key = obj['Key']
                    if not key.lower().endswith(('.pdf', '.json')):
                        continue
                    items.append({
                        'key': key,
                        'size': obj.get('Size', 0),
                        'last_modified': obj.get('LastModified').isoformat() if obj.get('LastModified') else '',
                        'url': f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{key}"
                    })
            return {"status": "success", "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def generate_presigned_url(self, key: str, expires_in: int = 3600):
        """Generate a presigned URL for a given S3 object key."""
        try:
            import boto3
            s3 = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.s3_region
            )
            url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return {"status": "success", "url": url}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _upload_to_azure(self, file_path, metadata):
        """Upload to Azure Blob Storage"""
        try:
            from azure.storage.blob import BlobServiceClient
            
            blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
            container_client = blob_service_client.get_container_client(self.azure_container)
            
            # Ensure container exists
            try:
                container_client.create_container()
            except Exception:
                pass  # Container already exists
            
            # Generate blob name
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y/%m/%d")
            blob_name = f"ecg-reports/{timestamp}/{filename}"
            
            # Upload file
            blob_client = container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True, metadata=metadata)
            
            url = blob_client.url
            
            return {
                "status": "success",
                "service": "azure",
                "url": url,
                "blob_name": blob_name,
                "container": self.azure_container
            }
            
        except ImportError:
            return {"status": "error", "message": "azure-storage-blob not installed. Run: pip install azure-storage-blob"}
        except Exception as e:
            return {"status": "error", "message": f"Azure upload failed: {str(e)}"}
    
    def _upload_to_gcs(self, file_path, metadata):
        """Upload to Google Cloud Storage"""
        try:
            from google.cloud import storage
            
            storage_client = storage.Client.from_service_account_json(self.gcs_credentials_path)
            bucket = storage_client.bucket(self.gcs_bucket)
            
            # Generate blob name
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y/%m/%d")
            blob_name = f"ecg-reports/{timestamp}/{filename}"
            
            # Upload file
            blob = bucket.blob(blob_name)
            blob.metadata = metadata
            blob.upload_from_filename(file_path)
            
            url = blob.public_url
            
            return {
                "status": "success",
                "service": "gcs",
                "url": url,
                "blob_name": blob_name,
                "bucket": self.gcs_bucket
            }
            
        except ImportError:
            return {"status": "error", "message": "google-cloud-storage not installed. Run: pip install google-cloud-storage"}
        except Exception as e:
            return {"status": "error", "message": f"GCS upload failed: {str(e)}"}
    
    def _upload_to_api(self, file_path, metadata):
        """Upload to custom API endpoint"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                headers = {}
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'
                
                data = {'metadata': json.dumps(metadata)}
                
                response = requests.post(
                    self.api_endpoint,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json() if response.content else {}
                    return {
                        "status": "success",
                        "service": "api",
                        "response": result,
                        "url": result.get('url', self.api_endpoint)
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API returned status {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            return {"status": "error", "message": f"API upload failed: {str(e)}"}
    
    def _upload_to_ftp(self, file_path, metadata, use_sftp=False):
        """Upload to FTP/SFTP server"""
        try:
            if use_sftp:
                import paramiko
                
                transport = paramiko.Transport((self.ftp_host, self.ftp_port))
                transport.connect(username=self.ftp_username, password=self.ftp_password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                
                # Create remote directory if needed
                remote_file = f"{self.ftp_remote_path}/{os.path.basename(file_path)}"
                sftp.put(file_path, remote_file)
                sftp.close()
                transport.close()
                
            else:
                from ftplib import FTP
                
                ftp = FTP()
                ftp.connect(self.ftp_host, self.ftp_port)
                ftp.login(self.ftp_username, self.ftp_password)
                
                # Upload file
                with open(file_path, 'rb') as f:
                    remote_file = f"{self.ftp_remote_path}/{os.path.basename(file_path)}"
                    ftp.storbinary(f'STOR {remote_file}', f)
                
                ftp.quit()
            
            return {
                "status": "success",
                "service": "sftp" if use_sftp else "ftp",
                "remote_path": remote_file
            }
            
        except ImportError:
            return {"status": "error", "message": "paramiko not installed for SFTP. Run: pip install paramiko"}
        except Exception as e:
            return {"status": "error", "message": f"FTP upload failed: {str(e)}"}
    
    def _upload_to_dropbox(self, file_path, metadata):
        """Upload to Dropbox"""
        try:
            import dropbox
            
            dbx = dropbox.Dropbox(self.dropbox_token)
            
            # Generate Dropbox path
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y/%m/%d")
            dropbox_path = f"/ECG-Reports/{timestamp}/{filename}"
            
            # Upload file
            with open(file_path, 'rb') as f:
                dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            
            # Get shareable link
            try:
                link = dbx.sharing_create_shared_link(dropbox_path)
                url = link.url
            except:
                url = dropbox_path
            
            return {
                "status": "success",
                "service": "dropbox",
                "url": url,
                "path": dropbox_path
            }
            
        except ImportError:
            return {"status": "error", "message": "dropbox not installed. Run: pip install dropbox"}
        except Exception as e:
            return {"status": "error", "message": f"Dropbox upload failed: {str(e)}"}
    
    def _log_upload(self, file_path, result, metadata):
        """Log successful upload to tracking file"""
        try:
            # Load existing log
            log_data = []
            if os.path.exists(self.upload_log_path):
                with open(self.upload_log_path, 'r') as f:
                    log_data = json.load(f)
            
            # Add new entry
            log_entry = {
                "local_path": file_path,
                "uploaded_at": datetime.now().isoformat(),
                "service": self.cloud_service,
                "result": result,
                "metadata": metadata
            }
            log_data.append(log_entry)
            
            # Save log
            os.makedirs(os.path.dirname(self.upload_log_path), exist_ok=True)
            with open(self.upload_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not log upload: {e}")
    
    def get_upload_history(self, limit=50):
        """Get recent upload history"""
        try:
            if os.path.exists(self.upload_log_path):
                with open(self.upload_log_path, 'r') as f:
                    log_data = json.load(f)
                return log_data[-limit:]
            return []
        except Exception:
            return []


# Global instance
_cloud_uploader = None

def get_cloud_uploader():
    """Get or create global cloud uploader instance"""
    global _cloud_uploader
    if _cloud_uploader is None:
        _cloud_uploader = CloudUploader()
    return _cloud_uploader

