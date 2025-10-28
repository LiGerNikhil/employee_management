# Support Ticket System - Implementation Guide

## Overview
Implemented a comprehensive support ticket system where employees can raise issues and admins can track, update, and resolve them with a colorful, intuitive UI.

## Features Implemented

### 1. **Ticket Model**
Complete ticket management with:
- ✅ Auto-generated ticket numbers (TKT-YYYYMMDD-XXXX)
- ✅ Subject and description
- ✅ Category (Attendance, Leave, Payroll, Technical, HR, Facility, Other)
- ✅ Priority (Low, Medium, High, Urgent)
- ✅ Status (Open, In Progress, Resolved, Closed, Reopened)
- ✅ File attachments
- ✅ Timestamps (created, updated, resolved)
- ✅ Resolved by (admin tracking)
- ✅ Admin notes (internal)

### 2. **Comment System**
- ✅ Multiple comments per ticket
- ✅ Employee and admin can comment
- ✅ Internal notes (admin only)
- ✅ Timestamps

### 3. **Color-Coded UI**

**Status Colors:**
- 🔵 **Blue (Primary)** - Open
- 🟡 **Yellow (Warning)** - In Progress
- 🟢 **Green (Success)** - Resolved
- ⚪ **Gray (Secondary)** - Closed
- 🔴 **Red (Danger)** - Reopened

**Priority Colors:**
- 🔵 **Cyan (Info)** - Low
- 🔵 **Blue (Primary)** - Medium
- 🟡 **Yellow (Warning)** - High
- 🔴 **Red (Danger)** - Urgent

**Category Icons:**
- ⏰ `bx-time-five` - Attendance
- 📅 `bx-calendar-x` - Leave
- 💰 `bx-money` - Payroll
- 🔧 `bx-wrench` - Technical
- 👤 `bx-user-voice` - HR
- 🏢 `bx-building` - Facility
- ❓ `bx-help-circle` - Other

## Files Created/Modified

### 1. **Models** (`employees/models.py`)
```python
class Ticket(models.Model):
    ticket_number = CharField(unique=True)
    employee = ForeignKey(Employee)
    subject = CharField(max_length=200)
    description = TextField()
    category = CharField(choices=CATEGORY_CHOICES)
    priority = CharField(choices=PRIORITY_CHOICES)
    status = CharField(choices=STATUS_CHOICES)
    attachment = FileField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    resolved_at = DateTimeField()
    resolved_by = ForeignKey(User)
    admin_notes = TextField()

class TicketComment(models.Model):
    ticket = ForeignKey(Ticket)
    user = ForeignKey(User)
    comment = TextField()
    is_internal = BooleanField()
    created_at = DateTimeField()
```

### 2. **URLs** (`employees/urls.py`)
```python
# Employee URLs
path('tickets/', views.employee_tickets, name='employee_tickets')
path('tickets/create/', views.create_ticket, name='create_ticket')
path('tickets/<int:pk>/', views.ticket_detail, name='ticket_detail')
path('tickets/<int:pk>/comment/', views.add_ticket_comment, name='add_ticket_comment')

# Admin URLs
path('admin/tickets/', views.admin_tickets, name='admin_tickets')
path('admin/tickets/<int:pk>/update/', views.admin_update_ticket, name='admin_update_ticket')
```

### 3. **Sidebar Menu**
**Employee Menu:**
- Support Tickets (with icon)

**Admin Menu:**
- Support Tickets (with icon)

### 4. **Admin Panel** (`employees/admin.py`)
- Registered Ticket and TicketComment models
- Inline comments in ticket admin
- Searchable and filterable

## Views to Implement

### Employee Views:
1. **employee_tickets** - List all my tickets
2. **create_ticket** - Create new ticket
3. **ticket_detail** - View ticket details and comments
4. **add_ticket_comment** - Add comment to ticket

### Admin Views:
1. **admin_tickets** - View all tickets with filters
2. **admin_update_ticket** - Update ticket status, priority, add notes

## Templates to Create

### Employee Templates:
1. **employee_tickets.html** - My tickets list
2. **create_ticket.html** - Create ticket form
3. **ticket_detail.html** - Ticket details with comments

### Admin Templates:
1. **admin_tickets.html** - All tickets dashboard
2. **admin_ticket_detail.html** - Admin ticket management

## Features

### For Employees:
- ✅ Create tickets with attachments
- ✅ View all my tickets
- ✅ Filter by status/priority
- ✅ Add comments
- ✅ Track ticket progress
- ✅ See admin responses

### For Admins:
- ✅ View all tickets
- ✅ Filter by employee/status/priority/category
- ✅ Update ticket status
- ✅ Change priority
- ✅ Add internal notes
- ✅ Resolve tickets
- ✅ Reply to employees
- ✅ Track resolution time
- ✅ See overdue tickets

## Ticket Number Format
```
TKT-20251029-0001
TKT-20251029-0002
...
```
Format: `TKT-[YYYYMMDD]-[Sequential Number]`

## Status Workflow
```
Open → In Progress → Resolved → Closed
         ↓
      Reopened (if issue persists)
```

## Priority Levels
1. **Low** - Minor issues, no urgency
2. **Medium** - Normal issues, standard timeline
3. **High** - Important issues, needs attention
4. **Urgent** - Critical issues, immediate action required

## Categories
1. **Attendance Issue** - Check-in/out problems
2. **Leave Request** - Leave applications
3. **Payroll Issue** - Salary/payment issues
4. **Technical Support** - System/app issues
5. **HR Related** - HR queries
6. **Facility/Infrastructure** - Office facilities
7. **Other** - Miscellaneous

## Database Indexes
```python
indexes = [
    models.Index(fields=['-created_at']),
    models.Index(fields=['employee', '-created_at']),
    models.Index(fields=['status', '-created_at']),
]
```

## Properties & Methods

### Ticket Properties:
- `status_color` - Returns Bootstrap color class
- `priority_color` - Returns Bootstrap color class
- `category_icon` - Returns Boxicon class
- `is_overdue` - True if open for >3 days

### TicketComment Properties:
- `is_admin` - True if comment from admin

## Next Steps

1. ✅ Models created
2. ✅ Migrations run
3. ✅ Admin registered
4. ✅ URLs added
5. ✅ Sidebar updated
6. ⏳ Views to implement
7. ⏳ Templates to create
8. ⏳ Forms to create

## Status

🟡 **IN PROGRESS** - Models and structure complete, views and templates pending

**Date:** October 29, 2025
**Feature:** Support Ticket System
**Next:** Implement views and create templates
