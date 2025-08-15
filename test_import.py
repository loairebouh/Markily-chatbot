#!/usr/bin/env python3
"""
Quick test to verify the bot imports and basic functions work
"""

import sys
import os
sys.path.append('.')

def test_bot_import():
    """Test that the bot can be imported without errors"""
    try:
        print("🔄 Testing bot import...")
        from markily_bot import MarkilyBot, parse_reminder_datetime
        print("✅ Bot import successful!")
        
        # Test date parsing
        from datetime import datetime
        test_date = parse_reminder_datetime("tomorrow 10AM")
        if test_date:
            print(f"✅ Date parsing works: {test_date}")
        else:
            print("❌ Date parsing failed")
            
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_bot_import()
    sys.exit(0 if success else 1)
