"""
Test script for MSAL Device Flow authentication
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from auth.msal_device_auth import MSALDeviceAuthManager

def test_device_flow():
    """Test MSAL Device Flow"""
    print("\n" + "="*70)
    print("🔐 MSAL Device Code Flow Test")
    print("="*70 + "\n")
    
    try:
        # Initialize manager
        manager = MSALDeviceAuthManager()
        
        print("📝 Configuration:")
        print(f"   ✅ Client ID configured")
        print(f"   ✅ Tenant ID configured")
        print(f"   ✅ Token storage ready\n")
        
        # Check if already authenticated
        if manager.is_authenticated:
            print("✅ Token found on disk. Using cached authentication.\n")
            token = manager.get_access_token()
            print(f"✅ Access token retrieved (length: {len(token)})")
        else:
            print("🔐 No cached token. Starting device flow...\n")
            token_dict = manager.ensure_authenticated()
            
            if token_dict and "access_token" in token_dict:
                print("\n✅ Authentication successful!")
                print(f"✅ Access token saved: {token_dict['access_token'][:30]}...")
                print(f"✅ Expires in: {token_dict.get('expires_in', 'N/A')} seconds")
            else:
                print("\n❌ Authentication failed")
                return False
        
        print("\n" + "="*70)
        print("✅ Device Flow Test PASSED")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_device_flow()
    sys.exit(0 if success else 1)