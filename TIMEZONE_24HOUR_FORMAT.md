# 24-Hour Time Format with IST Timezone

## Overview
All timestamps now display in **24-hour format (00:00 to 24:00)** using **Indian Standard Time (IST)**.

## Changes Made

### 1. Timezone Configuration
**File:** `config/settings.py`

```python
TIME_ZONE = "Asia/Kolkata"  # Indian Standard Time (IST - UTC+5:30)
USE_TZ = True
```

- Times stored in database: UTC
- Times displayed to users: IST in 24-hour format
- Automatic conversion between UTC and IST

### 2. Time Format Standards

#### 24-Hour Format Used:
- **Time with seconds:** `14:30:45` (HH:MM:SS)
- **Time without seconds:** `14:30` (HH:MM)
- **Date format:** `28 Oct 2025, Monday`

#### Django Template Format Codes:
- `H:i:s` = 14:30:45 (24-hour with seconds)
- `H:i` = 14:30 (24-hour without seconds)
- `d M Y` = 28 Oct 2025

### 3. Templates Updated

All templates now use `|date:"H:i"` or `|date:"H:i:s"` for 24-hour format:

#### Attendance List
```django
{{ record.check_in_time|date:"H:i:s" }}  → 14:30:45
```

#### Check-in Page
```django
{{ today_attendance.check_in_time|date:"H:i:s" }}  → 14:30:45
```

#### Employee Dashboard
```django
{{ today_attendance.check_in_time|date:"H:i" }}  → 14:30
```

#### Admin Dashboard
```django
{{ attendance.check_in_time|date:"H:i" }}  → 14:30
```

#### Employee Detail
```django
{{ attendance.check_in_time|date:"H:i:s" }}  → 14:30:45
```

## Time Display Examples

### Before (12-hour format, UTC):
```
Check-in: 09:00:00 AM (UTC)
Actual PC time: 02:30:00 PM (IST)
```

### After (24-hour format, IST):
```
Check-in: 14:30:00
Matches PC time: 14:30:00
```

## How It Works

### 1. Time Storage (Database)
```
Database stores: 2025-10-28 09:00:00 UTC
```

### 2. Time Conversion (Django)
```
Django converts: UTC → IST (adds 5 hours 30 minutes)
Result: 2025-10-28 14:30:00 IST
```

### 3. Time Display (Template)
```
Template formats: 14:30:00 (24-hour format)
User sees: 14:30:00
```

## Format Breakdown

### Time Formats:
| Format | Example | Usage |
|--------|---------|-------|
| `H:i:s` | 14:30:45 | Full time with seconds |
| `H:i` | 14:30 | Time without seconds |
| `h:i A` | 02:30 PM | 12-hour format (NOT used) |

### Date Formats:
| Format | Example | Usage |
|--------|---------|-------|
| `d M Y` | 28 Oct 2025 | Short date |
| `d M Y, l` | 28 Oct 2025, Monday | Date with day |
| `l, M d, Y` | Monday, Oct 28, 2025 | Full format |

## Benefits

1. **Matches PC Time:** Shows exact time from your computer
2. **24-Hour Format:** Professional standard (00:00 to 24:00)
3. **IST Timezone:** Indian Standard Time (UTC+5:30)
4. **No Confusion:** No AM/PM needed
5. **Consistent:** Same format everywhere

## Testing

### Verify 24-Hour Format:

1. **Check Current Time:**
   - Look at your PC clock: e.g., 14:30
   - Check-in as employee
   - Verify displayed time matches: 14:30

2. **Check Attendance List:**
   - Go to attendance records
   - Times should show as: 14:30:45 (not 02:30 PM)

3. **Check Dashboards:**
   - Employee dashboard: "Today at 14:30"
   - Admin dashboard: Times in 24-hour format

### Expected Display:

**Morning (before noon):**
- 00:00 to 11:59 (not 12:00 AM to 11:59 AM)

**Afternoon/Evening:**
- 12:00 to 23:59 (not 12:00 PM to 11:59 PM)

## IST Details

- **Full Name:** Indian Standard Time
- **Timezone:** Asia/Kolkata
- **UTC Offset:** +05:30 (5 hours 30 minutes ahead)
- **DST:** No daylight saving time
- **Covers:** All of India

## Time Conversion Examples

| UTC Time | IST Time | Display |
|----------|----------|---------|
| 00:00:00 | 05:30:00 | 05:30:00 |
| 06:00:00 | 11:30:00 | 11:30:00 |
| 09:00:00 | 14:30:00 | 14:30:00 |
| 12:00:00 | 17:30:00 | 17:30:00 |
| 18:30:00 | 00:00:00 | 00:00:00 (next day) |

## Troubleshooting

### Issue: Time doesn't match PC
**Solution:**
1. Verify PC timezone is set to IST
2. Check `TIME_ZONE = "Asia/Kolkata"` in settings.py
3. Restart Django server

### Issue: Still showing 12-hour format
**Solution:**
1. Check templates use `|date:"H:i"` not `|time:"h:i A"`
2. Clear browser cache
3. Restart server

### Issue: Wrong time displayed
**Solution:**
1. Verify `USE_TZ = True` in settings.py
2. Check database has timezone-aware datetimes
3. Ensure pytz is installed (optional but recommended)

## Code Examples

### In Templates:

```django
<!-- 24-hour time with seconds -->
{{ attendance.check_in_time|date:"H:i:s" }}
Output: 14:30:45

<!-- 24-hour time without seconds -->
{{ attendance.check_in_time|date:"H:i" }}
Output: 14:30

<!-- Full datetime -->
{{ attendance.check_in_time|date:"d M Y, H:i:s" }}
Output: 28 Oct 2025, 14:30:45
```

### In Views (if needed):

```python
from django.utils import timezone

# Get current IST time
current_time = timezone.now()  # Automatically in IST

# Format in 24-hour
time_str = current_time.strftime("%H:%M:%S")  # 14:30:45
```

## Files Modified

1. `config/settings.py` - Timezone set to Asia/Kolkata
2. `templates/employees/attendance_list.html` - 24-hour format
3. `templates/employees/check_in.html` - 24-hour format
4. `templates/employees/dashboard/employee_dashboard.html` - 24-hour format
5. `templates/employees/dashboard/admin_dashboard.html` - 24-hour format
6. `templates/employees/employee_detail.html` - 24-hour format

## Summary

✅ **Timezone:** Indian Standard Time (IST)
✅ **Format:** 24-hour (00:00 to 24:00)
✅ **Display:** Matches your PC time exactly
✅ **Consistent:** Same format across all pages

**All times now display in 24-hour format using IST timezone!**
