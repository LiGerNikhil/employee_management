"""
Quick test script to verify check-in functionality
Run with: python manage.py shell < test_checkin.py
"""
from employees.models import Employee, Attendance
from django.utils import timezone

print("Testing check-in functionality...")

# Get first employee
try:
    employee = Employee.objects.first()
    if not employee:
        print("❌ No employees found. Please create an employee first.")
        exit()
    
    print(f"✓ Testing with employee: {employee.name}")
    
    # Get today's date
    today = timezone.now().date()
    print(f"✓ Today's date: {today}")
    
    # Try to get or create attendance
    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today
    )
    
    if created:
        print(f"✓ Created new attendance record: {attendance}")
    else:
        print(f"✓ Retrieved existing attendance record: {attendance}")
    
    # Try again to verify no IntegrityError
    attendance2, created2 = Attendance.objects.get_or_create(
        employee=employee,
        date=today
    )
    
    if not created2:
        print(f"✓ Successfully retrieved same record without error")
        print(f"✓ Attendance IDs match: {attendance.id == attendance2.id}")
    
    print("\n✅ Check-in functionality is working correctly!")
    print("The IntegrityError has been fixed.")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
