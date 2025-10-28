# Debug Checkout Camera Issue

## Steps to Debug

### 1. Open Browser Console
- Press **F12** on your keyboard
- Click the **Console** tab
- Keep it open while testing

### 2. Navigate to Check-In Page
- Go to: `http://127.0.0.1:8000/check-in/`
- Make sure you're already checked in (so checkout section appears)

### 3. Check Console Messages
Look for these messages when page loads:
```
Checkout elements check: {camera: true/false, startBtn: true/false, ...}
Adding click listener to checkout start button
✓ Click listener added successfully
```

**OR**

```
⚠️ Checkout start button not found!
```

### 4. Click "Start Camera for Check-out" Button
Watch the console for:
```
=== CHECKOUT START BUTTON CLICKED ===
Event: ...
Button element: ...
Calling initCheckoutCamera...
initCheckoutCamera called
checkoutCamera element: ...
Requesting camera access...
```

### 5. Possible Outcomes

#### ✅ Success Path:
```
Camera access granted!
Checkout camera initialized successfully
```
- Camera should appear
- "Capture Photo" button should be visible

#### ❌ Error Path 1 - Button Not Found:
```
⚠️ Checkout start button not found!
```
**Cause**: Button element doesn't exist in DOM
**Solution**: Check if you're actually checked in today

#### ❌ Error Path 2 - Camera Element Not Found:
```
Checkout camera element not found!
```
**Cause**: Video element missing
**Solution**: Template rendering issue

#### ❌ Error Path 3 - Permission Denied:
```
Checkout camera error: NotAllowedError
Error name: NotAllowedError
Error message: Permission denied
```
**Cause**: Browser blocked camera access
**Solution**: 
1. Click the camera icon in address bar
2. Allow camera permission
3. Refresh page and try again

#### ❌ Error Path 4 - No Camera:
```
Checkout camera error: NotFoundError
Error name: NotFoundError  
Error message: Requested device not found
```
**Cause**: No camera detected
**Solution**: 
1. Check if camera is connected
2. Check if another app is using it
3. Use file upload fallback

#### ❌ Error Path 5 - HTTPS Required:
```
Checkout camera error: NotSupportedError
Error message: Only secure origins are allowed
```
**Cause**: Browser requires HTTPS for camera
**Solution**: Access via HTTPS or localhost

## What to Report

Please copy and paste:

1. **All console messages** from when you load the page
2. **All console messages** from when you click the button
3. **Any error messages** in red
4. **Your browser name and version**

Example format:
```
Browser: Chrome 119
URL: http://127.0.0.1:8000/check-in/

Page Load Messages:
[paste here]

Button Click Messages:
[paste here]

Errors:
[paste here]
```

## Quick Fixes to Try

### Fix 1: Refresh Page
1. Press Ctrl+Shift+R (hard refresh)
2. Try clicking button again

### Fix 2: Clear Cache
1. Press Ctrl+Shift+Delete
2. Clear cached images and files
3. Refresh page

### Fix 3: Check Camera Permission
1. Look for camera icon in address bar
2. Click it
3. Set to "Allow"
4. Refresh page

### Fix 4: Try Different Browser
- Chrome (recommended)
- Firefox
- Edge

### Fix 5: Check if Already Checked Out
- Look at the page
- If you see check-out time, you're already checked out
- Can't check out twice in one day

## Visual Indicators

When button is clicked, you should see:
1. Button text changes to "Starting camera..."
2. Button becomes disabled
3. Status message appears: "Requesting camera access..."
4. Browser asks for camera permission (first time)
5. Camera preview appears
6. "Capture Photo" button becomes visible

If ANY of these don't happen, note which step fails.
