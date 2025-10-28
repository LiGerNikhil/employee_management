# Quick Reference Guide - Check-In & Check-Out

## 🚀 Quick Start

### For Employees

**Morning Check-In:**
1. Go to: `http://your-domain.com/check-in/`
2. Camera starts automatically
3. Position your face in frame
4. Click "Capture Photo"
5. Click "Check In with Photo"
6. Done! ✅

**Evening Check-Out:**
1. Go to: `http://your-domain.com/check-in/` (same page)
2. Scroll to "Ready to Check Out?" section
3. Click "Start Camera for Check-out"
4. Position your face in frame
5. Click "Capture Photo"
6. Click "Complete Check-out"
7. Done! ✅

---

## 📋 Key URLs

| Feature | URL | Method | Access |
|---------|-----|--------|--------|
| Check-In Page | `/check-in/` | GET, POST | Employees only |
| Check-Out | `/check-out/` | POST only | Employees only |
| Dashboard | `/employee-dashboard/` | GET | Employees only |
| Admin Dashboard | `/admin-dashboard/` | GET | Superadmin only |

---

## ✅ Validation Checklist

### Check-In Requirements
- [ ] User is logged in
- [ ] User is an employee
- [ ] Not already checked in today
- [ ] Photo is captured/uploaded
- [ ] Face is registered in system
- [ ] Exactly 1 face detected in photo
- [ ] Face matches registered face

### Check-Out Requirements
- [ ] User is logged in
- [ ] User is an employee
- [ ] Already checked in today
- [ ] Not already checked out today
- [ ] Photo is captured/uploaded
- [ ] Face is registered in system
- [ ] Exactly 1 face detected in photo
- [ ] Face matches registered face

---

## 🎯 Common Issues & Solutions

### Issue: Camera not working
**Solutions:**
1. Grant camera permission in browser
2. Use HTTPS (required by most browsers)
3. Try different browser (Chrome recommended)
4. Use fallback file upload option

### Issue: Face not detected
**Solutions:**
1. Ensure good lighting
2. Face the camera directly
3. Remove glasses/hat if possible
4. Move closer to camera
5. Try retaking photo

### Issue: Face verification failed
**Solutions:**
1. Ensure it's the same person as registered
2. Check lighting conditions
3. Capture clearer photo
4. Contact admin to re-register face

### Issue: Already checked in/out
**Solution:**
- This is expected behavior
- You can only check in/out once per day
- Check dashboard for today's status

---

## 🔧 Admin Tasks

### Register Employee Face
1. Create employee with profile picture
2. System automatically extracts face encoding
3. Face registered ✅

### Check Attendance
1. Go to `/attendance/`
2. Filter by date/employee
3. View check-in/out times and photos

### View Employee Details
1. Go to `/employees/<id>/`
2. See attendance history
3. Check face registration status

---

## 📊 Status Indicators

### Dashboard Indicators

**Check-In Status:**
- 🟢 "Checked In" - Successfully checked in today
- 🟡 "Not Checked In" - Haven't checked in yet
- ⏰ Time displayed when checked in

**Check-Out Status:**
- 🔴 "Ready to Check Out" - Can check out now
- 🟢 "Checked Out" - Already checked out
- ⏰ Time displayed when checked out

---

## 💡 Tips & Best Practices

### For Employees
✅ **DO:**
- Check in as soon as you arrive
- Ensure good lighting for photos
- Face the camera directly
- Check out before leaving
- Keep face clear (no masks/sunglasses)

❌ **DON'T:**
- Try to check in/out multiple times
- Use someone else's photo
- Cover your face during capture
- Skip the photo requirement

### For Admins
✅ **DO:**
- Ensure all employees have registered faces
- Monitor attendance regularly
- Check for failed verifications
- Keep face recognition library updated

❌ **DON'T:**
- Delete attendance records without backup
- Change tolerance without testing
- Disable face verification
- Share employee photos

---

## 🔐 Security Notes

### Password Security
- Minimum 8 characters required
- Change regularly
- Don't share with others

### Face Recognition
- Photos are encrypted
- Face encodings are secure
- Cannot be reverse-engineered
- Biometric data protected

### Data Privacy
- Photos stored securely
- Access controlled by role
- Audit trail maintained
- GDPR compliant

---

## 📱 Browser Compatibility

| Browser | Check-In | Check-Out | Camera | Notes |
|---------|----------|-----------|--------|-------|
| Chrome | ✅ | ✅ | ✅ | Recommended |
| Firefox | ✅ | ✅ | ✅ | Full support |
| Safari | ✅ | ✅ | ⚠️ | HTTPS required |
| Edge | ✅ | ✅ | ✅ | Full support |
| Mobile Chrome | ✅ | ✅ | ✅ | Works well |
| Mobile Safari | ✅ | ✅ | ⚠️ | HTTPS required |

---

## 🎨 UI Elements

### Buttons

**Check-In:**
- 🟢 Green "Check In with Photo" button
- Success color indicates positive action

**Check-Out:**
- 🔴 Red "Complete Check-out" button
- Danger color indicates end of day

### Status Messages

**Colors:**
- 🔵 Blue = Information
- 🟢 Green = Success
- 🟡 Yellow = Warning
- 🔴 Red = Error

**Icons:**
- ✓ Check circle = Success
- ⓘ Info circle = Information
- ⚠ Warning triangle = Warning
- ✗ Error circle = Error
- ⟳ Loader = Processing

---

## 📈 Performance Expectations

### Normal Operation
- Camera init: 1-2 seconds
- Photo capture: Instant
- Face verification: 2-4 seconds
- Total time: 5-7 seconds

### If Slower
- Check internet connection
- Clear browser cache
- Restart browser
- Contact IT support

---

## 🆘 Emergency Procedures

### Camera Completely Broken
1. Use file upload fallback
2. Take photo with phone
3. Upload to system
4. Face verification still applies

### Face Verification Always Failing
1. Contact admin immediately
2. Admin can manually mark attendance
3. Re-register face if needed
4. Check lighting/camera quality

### System Down
1. Note time manually
2. Inform supervisor
3. Admin can add attendance later
4. Keep photo evidence if possible

---

## 📞 Support Contacts

### Technical Issues
- Check browser console (F12)
- Take screenshot of error
- Note exact time of issue
- Contact: IT Support

### Face Registration Issues
- Contact: HR Department
- Bring valid ID
- Schedule re-registration
- Allow 24 hours for update

### Attendance Disputes
- Contact: HR Department
- Provide date and time
- Explain situation
- Check dashboard first

---

## 🔄 Daily Workflow

```
Morning:
08:45 - Arrive at office
08:50 - Open laptop/computer
08:55 - Navigate to /check-in/
09:00 - Complete check-in ✅

During Day:
09:00-18:00 - Work normally
             - System tracks attendance

Evening:
17:55 - Finish work tasks
18:00 - Navigate to /check-in/
18:05 - Complete check-out ✅
18:10 - Leave office
```

---

## 🎓 Training Resources

### For New Employees
1. Read this guide
2. Watch demo video (if available)
3. Practice check-in on first day
4. Ask questions to HR
5. Save this guide for reference

### For Admins
1. Review `CHECKOUT_IMPLEMENTATION.md`
2. Understand validation layers
3. Know troubleshooting steps
4. Test face recognition
5. Monitor system health

---

## ✨ Feature Highlights

### What Makes It Secure
✅ Biometric authentication
✅ Face verification required
✅ Cannot bypass checks
✅ Duplicate prevention
✅ Audit trail maintained

### What Makes It Easy
✅ Simple 3-step process
✅ Clear visual feedback
✅ Helpful error messages
✅ Retake option available
✅ Fallback upload option

### What Makes It Fast
✅ Auto camera start (check-in)
✅ Instant photo capture
✅ Quick face verification
✅ Optimized processing
✅ 5-7 second total time

---

## 📝 Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Capture Photo | Space | When camera active |
| Retake | R | After capture |
| Submit | Enter | When form ready |
| Cancel | Esc | Any time |

---

## 🌟 Success Criteria

### Successful Check-In
✅ Green success message displayed
✅ Confidence score shown (e.g., 95.3%)
✅ Redirected to dashboard
✅ Check-in time recorded
✅ Photo saved

### Successful Check-Out
✅ Green success message displayed
✅ Confidence score shown (e.g., 96.1%)
✅ "Have a great day!" message
✅ Redirected to dashboard
✅ Check-out time recorded
✅ Photo saved

---

## 🎯 Quick Commands

### For Testing
```bash
# Run diagnostic
python manage.py shell < test_checkout.py

# Check today's attendance
python manage.py shell
>>> from employees.models import Attendance
>>> from django.utils import timezone
>>> Attendance.objects.filter(date=timezone.now().date())

# Check employee face registration
>>> from employees.models import Employee
>>> Employee.objects.filter(face_registered=True).count()
```

### For Debugging
```javascript
// Browser console
// Check camera permissions
navigator.permissions.query({name: 'camera'})

// Check if camera available
navigator.mediaDevices.enumerateDevices()

// Test face detection
console.log(document.getElementById('camera'))
```

---

## 📚 Related Documentation

- `CHECKOUT_IMPLEMENTATION.md` - Technical details
- `FEATURE_COMPARISON.md` - Check-in vs check-out
- `IMPLEMENTATION_SUMMARY.md` - Complete overview
- `test_checkout.py` - Diagnostic script

---

## ✅ Final Checklist

Before going live:
- [ ] All employees have registered faces
- [ ] Camera permissions granted
- [ ] HTTPS enabled (if required)
- [ ] Database backups configured
- [ ] Error logging enabled
- [ ] Support contacts updated
- [ ] Training completed
- [ ] Test check-in/out successful
- [ ] Documentation reviewed
- [ ] Emergency procedures known

---

**Last Updated**: October 29, 2025
**Version**: 1.0
**Status**: ✅ Production Ready
