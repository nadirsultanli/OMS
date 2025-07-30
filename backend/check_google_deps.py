#!/usr/bin/env python3
"""
Script to check if Google OAuth dependencies are installed
"""

def check_google_dependencies():
    """Check if Google OAuth dependencies are available"""
    try:
        import google.auth
        import google.oauth2.id_token
        import google_auth_oauthlib.flow
        print("✅ All Google OAuth dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Google OAuth dependencies: {e}")
        print("To install: pip install google-auth google-auth-oauthlib google-auth-httplib2")
        return False

if __name__ == "__main__":
    check_google_dependencies()