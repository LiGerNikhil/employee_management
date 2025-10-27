# Installing Face Recognition Library

## Current Status
⚠ **Face recognition library is not installed.** The system will work without it, but face verification will be skipped during check-in.

## Error Encountered
```
ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device
```

## Solution Options

### Option 1: Free Up Disk Space (Recommended)
The face_recognition library requires approximately **100MB** of disk space for the models.

1. **Check available disk space:**
   ```bash
   # On Windows
   wmic logicaldisk get size,freespace,caption
   ```

2. **Free up space by:**
   - Deleting temporary files
   - Cleaning up old downloads
   - Removing unused applications
   - Emptying recycle bin

3. **Install face_recognition:**
   ```bash
   pip install face_recognition
   ```

### Option 2: Install on Different Drive
If C: drive is full, install Python packages on a different drive:

```bash
pip install --target=D:\python_packages face_recognition
```

Then add to your Python path in settings.py or environment variables.

### Option 3: Use Lightweight Alternative (Advanced)
If disk space is severely limited, consider using opencv-python for basic face detection:

```bash
pip install opencv-python
```

Note: This won't provide face recognition, only face detection.

### Option 4: Work Without Face Recognition
The system is designed to work without face_recognition:

**What works:**
- ✅ Employee creation
- ✅ Employee check-in with photos
- ✅ Photo storage for audit trail
- ✅ All admin functions

**What doesn't work:**
- ❌ Automatic face verification during check-in
- ❌ Confidence scoring
- ❌ Face encoding storage

**Workaround:**
- Manual verification of check-in photos by admin
- Photos are still saved for review

## Installation Steps (When Space Available)

### Windows:

1. **Install Visual Studio Build Tools** (required for dlib):
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"

2. **Install CMake:**
   ```bash
   pip install cmake
   ```

3. **Install face_recognition:**
   ```bash
   pip install face_recognition
   ```

### Linux/Mac:

```bash
# Install dependencies
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev

# Install face_recognition
pip install face_recognition
```

## Verification

After installation, verify it works:

```python
python -c "import face_recognition; print('✓ Face recognition installed successfully!')"
```

## Troubleshooting

### Issue: "No module named 'dlib'"
**Solution:** Install dlib separately:
```bash
pip install dlib
```

### Issue: "Microsoft Visual C++ 14.0 is required"
**Solution:** Install Visual Studio Build Tools (see above)

### Issue: Still getting disk space errors
**Solution:** 
1. Check pip cache: `pip cache dir`
2. Clear pip cache: `pip cache purge`
3. Try again: `pip install face_recognition`

### Issue: Import errors after installation
**Solution:** Restart your Django development server

## Testing After Installation

1. **Test import:**
   ```bash
   python manage.py shell
   >>> import face_recognition
   >>> print("Success!")
   ```

2. **Create a test employee with photo:**
   - Go to admin panel
   - Create employee with clear profile picture
   - Check for success message with face registration

3. **Test check-in:**
   - Login as employee
   - Go to check-in page
   - Upload selfie
   - Should see face verification result

## Current System Behavior (Without face_recognition)

### Employee Creation:
- ✅ Employee is created successfully
- ⚠ Warning message: "Face recognition library is not installed"
- ℹ Face encoding fields remain empty
- ℹ `face_registered` flag stays `False`

### Employee Check-in:
- ✅ Check-in is recorded
- ✅ Photo is saved
- ℹ Message: "Face recognition library is not installed, so verification was skipped"
- ℹ No confidence score displayed

### Admin Features:
- ✅ All admin functions work normally
- ✅ Can view/edit employees
- ✅ Can view attendance records
- ℹ Face registration status shows "Not Registered"

## Re-enabling Face Recognition

Once you install face_recognition:

1. **No code changes needed** - system auto-detects the library

2. **Register existing employees:**
   - Go to each employee's edit page
   - Re-upload their profile picture
   - Face will be automatically registered

3. **New employees:**
   - Face will be automatically registered during creation

4. **Verify:**
   - Check employee detail page
   - Should show "Face Registered" badge
   - Check-in should show verification results

## Support

If you continue to have issues:
1. Check Python version (3.7+ required)
2. Check pip version: `pip --version`
3. Update pip: `pip install --upgrade pip`
4. Try installing in virtual environment
5. Contact system administrator

## Alternative: Cloud-Based Face Recognition

If local installation continues to fail, consider:
- AWS Rekognition
- Azure Face API
- Google Cloud Vision API

These require API keys but don't need local installation.
