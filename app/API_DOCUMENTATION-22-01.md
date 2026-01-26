# ZestalAI API Documentation

## Overview

This document provides a comprehensive reference for the ZestalAI API. It details all available endpoints, their required authentication, request parameters, and response structures.

**Base URL:**
- Production: `https://app.zestal.pro`
- Development: `http://localhost:5000`

## Authentication

Most endpoints require JWT (JSON Web Token) authentication. You must include the token in the `Authorization` header of your requests.

**Header Format:**
```
Authorization: Bearer <your_jwt_token>
```

---

## 1. Authentication Module (`/api/auth`)

### Login
**POST** `/api/auth/login`

Authenticates a user using email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_verified": true
    // ... potentially other user fields
  },
  "message": "Login successful"
}
```

### Signup
**POST** `/api/auth/signup`

Registers a new user account.

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "user@example.com",
  "password": "password123",
  "code": "optional_verification_code"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    // ...
  }
}
```

### Facebook Login
**POST** `/api/auth/facebook/login`

Authenticates a user using a Facebook access token.

**Request Body:**
```json
{
  "access_token": "EAACEdEose0cBA..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "facebook_id": "1234567890"
    // ...
  },
  "message": "Facebook login successful"
}
```

### Verify Token
**GET** `/api/auth/verify`

Verifies if the current JWT token is valid.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "valid": true,
  "user_id": "1",
  "user": {
    "id": 1,
    "email": "user@example.com"
    // ...
  }
}
```

### Check Email
**POST** `/api/auth/check-email`

Checks if an email address is already registered.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "exists": true,
  "is_verified": true
}
```

### Refresh Facebook Token
**POST** `/api/auth/facebook/refresh-token`

Refreshes the user's Facebook access token.

**Headers:** `Authorization: Bearer <token>`
**Request Body (Optional):**
```json
{
  "access_token": "short_lived_token"
}
```

### Check Facebook Token
**GET** `/api/auth/facebook/check-token`

Checks the status of the user's Facebook token and refreshes it if needed.

**Headers:** `Authorization: Bearer <token>`

---

## 2. Main Application Module (`/api`)

### Get User Profile
**GET** `/api/profiles/<userId>`

Retrieves profile information for a specific user.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "1234567890",
  // ... other user fields
}
```

### Get Social Posts
**GET** `/api/social/posts`

Retrieves all social media posts with nested comments and AI replies for the authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
[
  {
    "id": "1",
    "facebook_post_id": "123456789",
    "name": "Post Title",
    "content": "Post content...",
    "timestamp": "2023-10-27T10:00:00Z",
    "likes": 10,
    "shares": 2,
    "engagements": 15,
    "comments": [
      {
        "id": "c1",
        "author": "Jane Doe",
        "content": "Great post!",
        "timestamp": "2023-10-27T10:05:00Z",
        "likes": 1,
        "isNew": false,
        "ai_reply": "Thanks Jane!",
        "self_comment": false,
        "replies": []
      }
    ]
  }
]
```

### Trigger Scrape (Background)
**GET** `/api/scrape`

Triggers a background task to scrape comments for all verified users.

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Comment scraping started in background. Check logs for progress."
}
```

### Log Lead
**POST** `/api/zestal/loglead`

Logs lead information from the landing page.

**Request Body:**
```json
{
  "firstName": "John",
  "email": "john@example.com",
  "phone": "1234567890",
  "emailConsent": true,
  "smsConsent": true
}
```

---

## 3. Facebook Sync Module (`/api/facebook`)

These endpoints allow manual control over Facebook data synchronization.

### Manual Sync Posts
**POST** `/api/facebook/sync/posts`

Triggers a background job to sync Facebook posts.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": 123,
  "message": "Post synchronization job started",
  "job": {
    "id": 123,
    "type": "sync_posts",
    "status": "pending",
    "created_at": "..."
  }
}
```

### Manual Sync Comments
**POST** `/api/facebook/sync/comments`

Triggers a background job to sync comments for all posts.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": 124,
  "message": "Comment synchronization job started"
}
```

### Manual Full Sync
**POST** `/api/facebook/sync/all`

Triggers a full synchronization (posts + comments).

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "job_id": 125,
  "message": "Full synchronization job started"
}
```

### Get Facebook Stats
**GET** `/api/facebook/stats`

Gets synchronization statistics for the user.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "stats": {
    "total_posts": 50,
    "total_comments": 200,
    "active_jobs": 1,
    "last_sync": {
        "id": 120,
        "status": "completed",
        "completed_at": "..."
    },
    "token_status": {
        "valid": true,
        "expires_at": "..."
    }
  }
}
```

### Get Jobs
**GET** `/api/facebook/jobs`

Lists background jobs for the user.
**Query Params:** `limit` (default 20), `status` (optional)

---

## 4. GoHighLevel (GHL) Module (`/api/ghl`)

Endpoints for interacting with GoHighLevel integration.

### List Contacts
**GET** `/api/ghl/contacts`

**Headers:** `Authorization: Bearer <token>`
**Query Params:** `limit`, `page`, `query`, `sortBy`, `tags`, `dateCreated`

### Create Contact
**POST** `/api/ghl/contacts`

**Headers:** `Authorization: Bearer <token>`
**Request Body:** Contact object (GHL format)

### List Tasks
**GET** `/api/ghl/tasks`

**Headers:** `Authorization: Bearer <token>`
**Query Params:** `limit`, `page`, `status`, `dueDate`

### List Calendars
**GET** `/api/ghl/calendars`

**Headers:** `Authorization: Bearer <token>`

### List Campaigns
**GET** `/api/ghl/campaigns`

**Headers:** `Authorization: Bearer <token>`

---

## 5. Scheduler Module (`/api/scheduler`)

### Get Scheduled Jobs
**GET** `/api/scheduler/jobs`

Returns runtime status of internal scheduler jobs.

**Headers:** `Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "success": true,
  "jobs": [
    {
      "id": "fetch_facebook_posts",
      "name": "Fetch Facebook Posts",
      "next_run_time": "2026-01-24T03:00:00+00:00",
      "trigger": "cron[hour='3', minute='0']"
    }
  ],
  "scheduler_running": true
}
```

**Available Job IDs:**
| Job ID | Description | Schedule |
|--------|-------------|----------|
| `fetch_facebook_posts` | Fetch posts for all users | Daily at 3 AM UTC |
| `fetch_facebook_post_comments` | Scrape comments for all posts | Daily at 5 AM UTC |
| `generate_comments_replies` | Generate AI replies | Every 2 hours |
| `cleanup_expired_tokens` | Clean up expired tokens | Daily at 2 AM UTC |
| `scheduler_health_check` | Health check | Every 30 minutes |

### Trigger Job
**POST** `/api/scheduler/jobs/<job_id>/trigger`

Manually triggers a specific scheduler job. Use one of the job IDs from the table above.

**Example:** `/api/scheduler/jobs/fetch_facebook_posts/trigger`

### Pause/Resume Job
**POST** `/api/scheduler/jobs/<job_id>/pause`
**POST** `/api/scheduler/jobs/<job_id>/resume`
