#!/usr/bin/env python3
"""
Simple test to verify Cache-Control headers are properly set.
This can be run without pytest to validate the implementation.
"""

import sys
sys.path.insert(0, '/home/ruby/Projects/courses/flask_helloworld_miniproject')

from app.app import app

def test_cache_control_headers():
    """Test that Cache-Control headers are properly set."""
    with app.test_client() as client:
        response = client.get('/health')
        
        print("Testing /health endpoint Cache-Control headers...")
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON: {response.get_json()}")
        print(f"\nHeaders:")
        
        # Check Cache-Control
        cache_control = response.headers.get('Cache-Control', '')
        print(f"  Cache-Control: {cache_control}")
        assert 'no-cache' in cache_control, "Missing 'no-cache' directive"
        assert 'no-store' in cache_control, "Missing 'no-store' directive"
        assert 'must-revalidate' in cache_control, "Missing 'must-revalidate' directive"
        print("    ✓ Contains no-cache")
        print("    ✓ Contains no-store")
        print("    ✓ Contains must-revalidate")
        
        # Check Pragma
        pragma = response.headers.get('Pragma', '')
        print(f"  Pragma: {pragma}")
        assert pragma == 'no-cache', f"Expected 'no-cache', got '{pragma}'"
        print("    ✓ Correct value")
        
        # Check Expires
        expires = response.headers.get('Expires', '')
        print(f"  Expires: {expires}")
        assert expires == '0', f"Expected '0', got '{expires}'"
        print("    ✓ Correct value")
        
        # Check response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.get_json() == {"status": "healthy"}, "Incorrect JSON response"
        
        print("\n✅ All Cache-Control tests passed!")
        return True

if __name__ == "__main__":
    try:
        test_cache_control_headers()
        print("\n🎉 Cache-Control implementation is correct!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
