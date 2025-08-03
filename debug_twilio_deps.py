#!/usr/bin/env python3
"""Debug Twilio dependencies"""

# Check what dependencies Twilio needs
twilio_deps = """
twilio==8.10.0
    - requests>=2.0.0
    - PyJWT[crypto]>=2.0.0,<3.0.0
    - pytz
    - aiohttp>=3.8.4
    - aiohttp-retry>=2.8.3
"""

print("Twilio 8.10.0 typically requires:")
print(twilio_deps)

# These are the key dependencies that might be missing
print("\nKey dependencies to check:")
print("1. requests - for HTTP calls")
print("2. PyJWT[crypto] - for JWT token handling (needs cryptography)")
print("3. pytz - for timezone handling")
print("4. aiohttp - for async HTTP")
print("5. aiohttp-retry - for retrying failed requests")
print("\nThe [crypto] extra in PyJWT requires the 'cryptography' package")
print("which needs system libraries like libffi-dev and python3-dev")