# Facebook App Setup Guide for Test Users

## Issue
When testing with new user accounts, you get this error:
```
(#100) You must provide an app access token, or a user access token that is an owner or developer of the app
```

## Solutions

### Option 1: Add Test Users to Facebook App (Recommended)

1. **Go to Facebook Developers Console:**
   - Visit: https://developers.facebook.com/
   - Select your "Zestal Consumer APP"

2. **Add Test Users:**
   - Go to "Roles" → "Test Users"
   - Click "Add Test Users"
   - Enter the email of your test account
   - Assign them "Developer" or "Tester" role

3. **Verify Test User:**
   - The test user will receive an email invitation
   - They need to accept the invitation to use the app

### Option 2: Make App Public (For Production)

1. **Go to App Review:**
   - In Facebook Developers Console
   - Go to "App Review" → "Permissions and Features"

2. **Submit for Review:**
   - Submit the required permissions for review
   - Once approved, the app will be available to all users

### Option 3: Add Users as App Developers

1. **Go to Roles:**
   - In Facebook Developers Console
   - Go to "Roles" → "Roles"

2. **Add Developers:**
   - Click "Add People"
   - Enter the Facebook email of your test users
   - Assign them "Developer" role

### Option 4: Use Facebook Test Users (Development Only)

1. **Create Test Users:**
   - Go to "Roles" → "Test Users"
   - Click "Create Test Users"
   - Facebook will create fake users for testing

2. **Use Test User Credentials:**
   - These users can be used for testing without real Facebook accounts

## Current App Configuration

Your Facebook App ID: `1157082506284931`
App Name: `Zestal Consumer APP`

## Testing Steps

1. **Add your test user to the app** (using one of the options above)
2. **Have the test user log in with Facebook**
3. **Verify the login works** without permission errors
4. **Test Facebook posts fetching**

## Error Handling

The app now provides better error messages:
- If permission error: "Please ensure you are authorized to use this app"
- If token invalid: "Invalid Facebook access token"

## Notes

- **Development Mode**: Only app owners/developers can use the app
- **Live Mode**: All users can use the app (requires Facebook review)
- **Test Users**: Can be used in development mode without review

## Quick Fix for Testing

If you need immediate testing, you can:
1. Add your test account as a "Developer" in the Facebook app
2. Or use the main account (infinity.devz.team@gmail.com) for testing
3. Or create Facebook test users for development
