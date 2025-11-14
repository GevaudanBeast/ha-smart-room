#!/usr/bin/env python3
"""Script to cleanup Smart Room Manager config entries."""
import json
import os
import shutil
from pathlib import Path

# Paths (adjust if needed)
CONFIG_DIR = Path.home() / "config"
STORAGE_DIR = CONFIG_DIR / ".storage"
CONFIG_ENTRIES_FILE = STORAGE_DIR / "core.config_entries"
BACKUP_FILE = CONFIG_ENTRIES_FILE.with_suffix('.backup')

print("🔍 Smart Room Manager Configuration Cleanup Script")
print("=" * 60)

# Check if file exists
if not CONFIG_ENTRIES_FILE.exists():
    print(f"❌ Config entries file not found: {CONFIG_ENTRIES_FILE}")
    print(f"   Expected location: {CONFIG_DIR}")
    print("\n💡 Please adjust CONFIG_DIR in the script to match your HA config directory")
    exit(1)

print(f"✓ Found config entries file: {CONFIG_ENTRIES_FILE}")

# Load config entries
try:
    with open(CONFIG_ENTRIES_FILE, 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"❌ Error reading config file: {e}")
    exit(1)

# Find Smart Room Manager entries
srm_entries = []
for i, entry in enumerate(data.get('data', {}).get('entries', [])):
    if entry.get('domain') == 'smart_room_manager':
        srm_entries.append((i, entry))

print(f"\n📊 Found {len(srm_entries)} Smart Room Manager entry(ies)")

if not srm_entries:
    print("✓ No Smart Room Manager entries found - nothing to clean")
    exit(0)

# Display entries
for i, (idx, entry) in enumerate(srm_entries, 1):
    print(f"\n📄 Entry #{i}:")
    print(f"   - Index: {idx}")
    print(f"   - Entry ID: {entry.get('entry_id')}")
    print(f"   - Title: {entry.get('title')}")
    print(f"   - Version: {entry.get('version')}")
    print(f"   - State: {entry.get('state', 'N/A')}")
    print(f"   - Rooms: {len(entry.get('options', {}).get('rooms', []))}")

# Ask user
print("\n" + "=" * 60)
response = input("\n❓ Do you want to DELETE all Smart Room Manager entries? (yes/no): ")

if response.lower() != 'yes':
    print("❌ Aborted - no changes made")
    exit(0)

# Backup
print(f"\n💾 Creating backup: {BACKUP_FILE}")
shutil.copy2(CONFIG_ENTRIES_FILE, BACKUP_FILE)
print("✓ Backup created")

# Remove entries
print("\n🗑️  Removing Smart Room Manager entries...")
entries = data['data']['entries']
for idx, _ in reversed(srm_entries):  # Remove from end to preserve indices
    del entries[idx]
    print(f"   ✓ Removed entry at index {idx}")

# Save
try:
    with open(CONFIG_ENTRIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print("\n✅ Config entries file updated successfully!")
except Exception as e:
    print(f"\n❌ Error writing config file: {e}")
    print(f"   Restoring backup...")
    shutil.copy2(BACKUP_FILE, CONFIG_ENTRIES_FILE)
    print("   ✓ Backup restored")
    exit(1)

print("\n" + "=" * 60)
print("✅ DONE!")
print("\n📋 Next steps:")
print("   1. Restart Home Assistant")
print("   2. Add Smart Room Manager integration again")
print(f"\n💡 If something goes wrong, restore backup:")
print(f"   cp {BACKUP_FILE} {CONFIG_ENTRIES_FILE}")
print("=" * 60)
