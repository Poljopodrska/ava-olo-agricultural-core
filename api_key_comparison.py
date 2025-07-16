#!/usr/bin/env python3
"""Compare API keys to identify issues"""

# Two different API keys seen in the codebase
working_key = "AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo"  # From test files
current_key = "AIzaSyDyFXDciVwW1ciV3jNM7SguGx2P8lK-BTo"   # From deployment

print("=== API Key Comparison ===")
print(f"Working key:  {working_key}")
print(f"Current key:  {current_key}")
print(f"Are they same: {working_key == current_key}")

print("\n=== Working Key Analysis ===")
print(f"Length: {len(working_key)}")
print(f"First 10: {working_key[:10]}")
print(f"Last 10: {working_key[-10:]}")

print("\n=== Current Key Analysis ===")
print(f"Length: {len(current_key)}")
print(f"First 10: {current_key[:10]}")
print(f"Last 10: {current_key[-10:]}")

print("\n=== Differences ===")
if len(working_key) != len(current_key):
    print(f"Different lengths: {len(working_key)} vs {len(current_key)}")

# Character by character comparison
differences = []
for i, (c1, c2) in enumerate(zip(working_key, current_key)):
    if c1 != c2:
        differences.append(f"Position {i}: '{c1}' vs '{c2}'")

if differences:
    print(f"Character differences found: {len(differences)}")
    for diff in differences[:10]:  # Show first 10 differences
        print(f"  {diff}")
else:
    print("No character differences found")

print("\n=== Recommendation ===")
if working_key != current_key:
    print("⚠️  Keys are different!")
    print("✅ Try using the working key in AWS App Runner environment:")
    print(f"   GOOGLE_MAPS_API_KEY={working_key}")
else:
    print("✅ Keys are identical - issue might be elsewhere")