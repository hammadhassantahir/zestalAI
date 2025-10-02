# Facebook App Review Documentation for user_posts Permission

## Overview
This document explains how our ZestalAI application uses the `user_posts` permission and complies with Facebook's platform policies.

## How We Use user_posts Permission

### 1. Purpose
We use the `user_posts` permission to help users analyze their social media engagement and content performance. Our application provides:
- Content analytics and insights
- Engagement tracking (likes, comments, shares)
- Content optimization recommendations
- Social media performance metrics

### 2. Data Collection
Our application collects the following data from user posts:
- **Post Content**: Message text and story content for content analysis
- **Post Metadata**: Creation time, update time, post type (status, photo, video, etc.)
- **Engagement Metrics**: Number of likes, comments, and shares
- **Comments**: Comment text and metadata for engagement analysis
- **Permalink URLs**: For reference back to original posts

### 3. Data Storage and Security
- All Facebook data is securely stored in our database with proper encryption
- Access tokens are stored securely and automatically cleaned up when expired
- User data is only accessible by the authenticated user who owns it
- We comply with data retention policies and allow users to delete their data

### 4. User Consent and Control
- Users explicitly grant permission during the OAuth flow
- Users can revoke access at any time through Facebook settings
- Users can delete their stored data through our application
- Clear privacy policy explains data usage

## Technical Implementation

### API Endpoints
1. **POST /api/auth/facebook/fetch-posts**
   - Fetches user's recent posts from Facebook API
   - Requires user authentication
   - Stores posts and engagement data in our database

2. **GET /api/auth/facebook/posts**
   - Returns user's stored posts with analytics
   - Paginated results for performance
   - Includes engagement metrics and trends

3. **POST /api/auth/facebook/posts/{id}/fetch-comments**
   - Fetches comments for a specific post
   - Analyzes comment sentiment and engagement
   - Stores comment data for comprehensive analytics

### Background Processing
- Automated service runs hourly to update post data
- Respects Facebook API rate limits
- Automatically handles expired tokens
- Provides fresh analytics data

### Database Schema
- **Users Table**: Stores Facebook access tokens and expiration
- **FacebookPosts Table**: Stores post content and engagement metrics
- **FacebookComments Table**: Stores comment data for engagement analysis

## Data Usage Compliance

### What We Do
✅ Analyze user's own posts for content insights
✅ Track engagement metrics for performance analysis
✅ Provide content optimization recommendations
✅ Store data securely with proper access controls
✅ Respect user privacy and data ownership
✅ Automatically clean up expired tokens

### What We Don't Do
❌ Share user data with third parties
❌ Access posts from other users
❌ Use data for advertising purposes
❌ Store data longer than necessary
❌ Provide data to unauthorized parties

## User Experience Flow
1. User logs in with Facebook OAuth
2. User grants `user_posts` permission
3. Application fetches user's posts with their consent
4. User receives analytics dashboard with their content insights
5. Background service keeps data updated (with user's continued consent)
6. User can revoke access or delete data at any time

## Privacy and Security
- All API calls use HTTPS encryption
- Access tokens stored with database encryption
- User data isolated per account
- Regular security audits and updates
- Compliance with GDPR and data protection regulations

## Support and Contact
For questions about data usage or privacy:
- Email: privacy@zestal.pro
- Privacy Policy: [Your Privacy Policy URL]
- Terms of Service: [Your Terms URL]

---

This implementation ensures full compliance with Facebook's platform policies while providing valuable analytics features to our users.
