#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta

def test_easy_date_selection():
    """Test the easy date/time selection functionality"""
    
    now = datetime.now()
    
    print("🔄 Testing Easy Date/Time Selection\n")
    
    # Test date calculations
    today = now
    tomorrow = now + timedelta(days=1)
    next_week = now + timedelta(days=7)
    
    print("📅 Date Options:")
    print(f"✅ Today: {today.strftime('%Y-%m-%d %A')}")
    print(f"✅ Tomorrow: {tomorrow.strftime('%Y-%m-%d %A')}")
    print(f"✅ Next Week: {next_week.strftime('%Y-%m-%d %A')}")
    
    print("\n⏰ Time Options:")
    time_options = [
        ("9:00 AM", 9, 0),
        ("10:00 AM", 10, 0),
        ("2:00 PM", 14, 0),
        ("5:00 PM", 17, 0),
        ("8:00 PM", 20, 0)
    ]
    
    for label, hour, minute in time_options:
        test_time = datetime.combine(tomorrow.date(), datetime.min.time().replace(hour=hour, minute=minute))
        print(f"✅ {label}: {test_time.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n🎯 Example User Flow:")
    print("1. User clicks 'Set Reminder'")
    print("2. User selects contact 'John Smith'")
    print("3. User clicks 'Tomorrow' button")
    print("4. User clicks '10:00 AM' button") 
    print("5. User types reminder note")
    print("6. ✅ Reminder set for tomorrow at 10:00 AM!")
    
    print(f"\n📅 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

def test_custom_time_parsing():
    """Test custom time parsing"""
    
    print("\n🔧 Testing Custom Time Parsing:")
    
    test_times = [
        "10AM",
        "2:30 PM", 
        "14:30",
        "9am",
        "11:45 PM",
        "23:59"
    ]
    
    for time_str in test_times:
        try:
            time_lower = time_str.lower()
            
            if 'am' in time_lower or 'pm' in time_lower:
                # Handle 12-hour format
                time_part = time_lower.replace('am', '').replace('pm', '').strip()
                
                if ':' in time_part:
                    hour_str, minute_str = time_part.split(':')
                    hour = int(hour_str)
                    minute = int(minute_str)
                else:
                    hour = int(time_part)
                    minute = 0
                
                # Convert to 24-hour format
                if 'pm' in time_lower:
                    if hour != 12:
                        hour += 12
                elif 'am' in time_lower and hour == 12:
                    hour = 0
                    
            else:
                # Handle 24-hour format
                if ':' in time_str:
                    hour_str, minute_str = time_str.split(':')
                    hour = int(hour_str)
                    minute = int(minute_str)
                else:
                    hour = int(time_str)
                    minute = 0
            
            print(f"✅ '{time_str}' -> {hour:02d}:{minute:02d}")
            
        except Exception as e:
            print(f"❌ '{time_str}' -> Error: {e}")

if __name__ == "__main__":
    test_easy_date_selection()
    test_custom_time_parsing()
