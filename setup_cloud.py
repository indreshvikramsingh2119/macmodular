#!/usr/bin/env python3
"""
Interactive Cloud Setup Script
Automatically configures AWS credentials for teammates
No manual .env editing required!
"""

import os
import sys
from pathlib import Path
import getpass

def print_header():
    """Print welcome header"""
    print("\n" + "=" * 70)
    print("🔐 ECG MONITOR - AUTOMATIC CLOUD SETUP")
    print("=" * 70)
    print("\nThis script will help you set up cloud sync in 2 minutes.")
    print("You'll need 4 credentials from Divyansh.\n")

def print_separator():
    """Print separator line"""
    print("-" * 70)

def get_input_secure(prompt, is_secret=False):
    """Get input from user, optionally hide for secrets"""
    if is_secret:
        return getpass.getpass(prompt)
    else:
        return input(prompt).strip()

def validate_aws_access_key(key):
    """Validate AWS access key format"""
    if not key:
        return False, "Access key cannot be empty"
    if not key.startswith("AKIA"):
        return False, "Access key should start with 'AKIA'"
    if len(key) != 20:
        return False, f"Access key should be 20 characters (you entered {len(key)})"
    return True, "Valid"

def validate_aws_secret_key(key):
    """Validate AWS secret key format"""
    if not key:
        return False, "Secret key cannot be empty"
    if len(key) != 40:
        return False, f"Secret key should be 40 characters (you entered {len(key)})"
    return True, "Valid"

def validate_bucket_name(bucket):
    """Validate S3 bucket name"""
    if not bucket:
        return False, "Bucket name cannot be empty"
    if len(bucket) < 3:
        return False, "Bucket name too short"
    return True, "Valid"

def test_cloud_connection(env_path):
    """Test if cloud connection works"""
    print("\n🧪 Testing cloud connection...")
    
    try:
        # Load the .env file we just created
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        # Try to connect
        import boto3
        
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_S3_REGION')
        )
        
        # Try to list bucket
        bucket_name = os.getenv('AWS_S3_BUCKET')
        s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        
        print("✅ Connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def create_env_file():
    """Interactive setup to create .env file"""
    
    print_header()
    
    # Check if .env already exists
    env_path = Path(".env")
    if env_path.exists():
        print("⚠️  WARNING: .env file already exists!")
        response = input("Do you want to overwrite it? (yes/no): ").lower()
        if response not in ['yes', 'y']:
            print("\n❌ Setup cancelled. Existing .env file kept.")
            return False
        print("\n📝 Overwriting existing .env file...")
    
    print("\n📋 Please enter your AWS credentials:")
    print("(Contact Divyansh if you don't have these)")
    print()
    
    # Collect credentials
    credentials = {}
    
    # 1. AWS Access Key
    print_separator()
    print("1️⃣  AWS Access Key ID")
    print("   Format: AKIA... (20 characters)")
    while True:
        access_key = get_input_secure("   Enter AWS_ACCESS_KEY_ID: ")
        valid, message = validate_aws_access_key(access_key)
        if valid:
            credentials['AWS_ACCESS_KEY_ID'] = access_key
            print(f"   ✅ {message}")
            break
        else:
            print(f"   ❌ {message}. Try again.")
    
    # 2. AWS Secret Key
    print_separator()
    print("2️⃣  AWS Secret Access Key")
    print("   Format: 40 characters (will be hidden)")
    while True:
        secret_key = get_input_secure("   Enter AWS_SECRET_ACCESS_KEY: ", is_secret=True)
        valid, message = validate_aws_secret_key(secret_key)
        if valid:
            credentials['AWS_SECRET_ACCESS_KEY'] = secret_key
            print(f"   ✅ {message}")
            break
        else:
            print(f"   ❌ {message}. Try again.")
    
    # 3. S3 Bucket Name
    print_separator()
    print("3️⃣  S3 Bucket Name")
    print("   Example: ecg-reports-bucket")
    while True:
        bucket = get_input_secure("   Enter AWS_S3_BUCKET: ")
        valid, message = validate_bucket_name(bucket)
        if valid:
            credentials['AWS_S3_BUCKET'] = bucket
            print(f"   ✅ {message}")
            break
        else:
            print(f"   ❌ {message}. Try again.")
    
    # 4. AWS Region
    print_separator()
    print("4️⃣  AWS Region")
    print("   Common options:")
    print("     • us-east-1 (N. Virginia) - DEFAULT")
    print("     • us-west-2 (Oregon)")
    print("     • ap-south-1 (Mumbai)")
    print("     • eu-west-1 (Ireland)")
    region = get_input_secure("   Enter AWS_S3_REGION [us-east-1]: ")
    credentials['AWS_S3_REGION'] = region if region else "us-east-1"
    print(f"   ✅ Using region: {credentials['AWS_S3_REGION']}")
    
    # 5. Confirm
    print_separator()
    print("\n📝 Review your configuration:")
    print(f"   • Cloud Service: S3")
    print(f"   • Access Key: {credentials['AWS_ACCESS_KEY_ID'][:8]}...{credentials['AWS_ACCESS_KEY_ID'][-4:]}")
    print(f"   • Secret Key: {'*' * 36}{credentials['AWS_SECRET_ACCESS_KEY'][-4:]}")
    print(f"   • Bucket: {credentials['AWS_S3_BUCKET']}")
    print(f"   • Region: {credentials['AWS_S3_REGION']}")
    print()
    
    confirm = input("Is this correct? (yes/no): ").lower()
    if confirm not in ['yes', 'y']:
        print("\n❌ Setup cancelled. Please run the script again.")
        return False
    
    # Write .env file
    print("\n💾 Creating .env file...")
    try:
        with open(env_path, 'w') as f:
            f.write("# ========================================\n")
            f.write("# ECG Monitor - Cloud Configuration\n")
            f.write("# Auto-generated by setup_cloud.py\n")
            f.write("# ========================================\n\n")
            f.write("CLOUD_SERVICE=s3\n\n")
            f.write(f"AWS_ACCESS_KEY_ID={credentials['AWS_ACCESS_KEY_ID']}\n")
            f.write(f"AWS_SECRET_ACCESS_KEY={credentials['AWS_SECRET_ACCESS_KEY']}\n")
            f.write(f"AWS_S3_BUCKET={credentials['AWS_S3_BUCKET']}\n")
            f.write(f"AWS_S3_REGION={credentials['AWS_S3_REGION']}\n")
        
        print("✅ .env file created successfully!")
        
        # Test connection
        if test_cloud_connection(env_path):
            print("\n" + "=" * 70)
            print("🎉 SUCCESS! Cloud sync is now configured!")
            print("=" * 70)
            print("\n✅ Next steps:")
            print("   1. Run the app: python src/main.py")
            print("   2. Create a user or generate a report")
            print("   3. Data will auto-upload to cloud every 5 seconds")
            print("   4. View in Admin panel")
            print("\n💡 Your credentials are saved in .env (never commit this file!)")
            print()
            return True
        else:
            print("\n⚠️  .env file created, but connection test failed.")
            print("Please verify your credentials with Divyansh.")
            return False
            
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    try:
        import boto3
    except ImportError:
        missing.append("boto3")
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        missing.append("python-dotenv")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nPlease install them first:")
        print(f"   pip install {' '.join(missing)}")
        print("\nOr install all dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True

def main():
    """Main setup function"""
    try:
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Run interactive setup
        success = create_env_file()
        
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

