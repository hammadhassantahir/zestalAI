# ZestalAI API Routes Documentation

This document provides a complete list of all API endpoints in the ZestalAI application.

**Base URL:** `https://app.zestal.pro` or `http://localhost:5000` (development)

---

## Table of Contents
- [Authentication Routes](#authentication-routes)
- [Facebook Routes](#facebook-routes)
- [GoHighLevel Routes](#gohighlevel-routes)
- [Main Routes](#main-routes)
- [Scheduler Routes](#scheduler-routes)

---

## Authentication Routes (`/api/auth`)

### User Authentication

**POST `/api/auth/login`** - Login with email and password
- Request: `{ "email": "user@example.com", "password": "password123" }`
- Response: `{ "access_token": "jwt_token", "user": {...}, "message": "Login successful" }`

**POST `/api/auth/signup`** - Register a new user
- Request: `{ "first_name": "John", "last_name": "Doe", "email": "user@example.com", "password": "password123" }`
- Response: `{ "message": "User registered successfully", "access_token": "jwt_token", "user": {...} }`

### Facebook Authentication

**POST `/api/auth/facebook/login`** - Login with Facebook access token
- Request: `{ "access_token": "facebook_access_token" }`
- Response: `{ "access_token": "jwt_token", "user": {...}, "message": "Facebook login successful" }`

**GET `/api/auth/facebook/callback`** - Handle Facebook OAuth callback
- Query Params: `code`, `state`

**GET `/api/auth/facebook/redirect`** - Handle Facebook OAuth redirect
- Query Params: `code`, `state`

**GET/POST `/api/auth/facebook/webhook`** - Handle Facebook webhook (verification & events)
- GET Query Params: `hub.mode`, `hub.verify_token`, `hub.challenge`

### Token Verification

**GET `/api/auth/verify`** - Verify JWT token validity
- Headers: `Authorization: Bearer <token>`
- Response: `{ "valid": true, "user_id": "id", "user": {...} }`

**POST `/api/auth/check-email`** - Check if email exists
- Request: `{ "email": "user@example.com" }`
- Response: `{ "exists": true, "is_verified": true }`

### Facebook Posts Management

**POST `/api/auth/facebook/fetch-posts`** - Fetch user's Facebook posts from API
- Headers: `Authorization: Bearer <token>`
- Request (optional): `{ "limit": 50 }`

**GET `/api/auth/facebook/posts`** - Get user's Facebook posts from database
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit` (default: 20), `offset` (default: 0)

**POST `/api/auth/facebook/refresh-token`** - Refresh Facebook access token
- Headers: `Authorization: Bearer <token>`
- Request (optional): `{ "access_token": "short_lived_token" }`

**GET `/api/auth/facebook/check-token`** - Check Facebook token status
- Headers: `Authorization: Bearer <token>`

**POST `/api/auth/facebook/posts/<post_id>/fetch-comments`** - Fetch comments for a post
- Headers: `Authorization: Bearer <token>`
- Request (optional): `{ "limit": 25 }`

---

## Facebook Routes (`/api/facebook`)

### Manual Sync Operations

**POST `/api/facebook/sync/posts`** - Manually trigger Facebook post synchronization
- Headers: `Authorization: Bearer <token>`
- Response: `{ "success": true, "job_id": 123, "message": "...", "job": {...} }`

**POST `/api/facebook/sync/comments`** - Manually trigger comment synchronization
- Headers: `Authorization: Bearer <token>`

**POST `/api/facebook/sync/all`** - Trigger full synchronization
- Headers: `Authorization: Bearer <token>`

### Job Management

**GET `/api/facebook/jobs/<job_id>`** - Get status of a specific job
- Headers: `Authorization: Bearer <token>`

**GET `/api/facebook/jobs`** - Get all jobs for current user
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit` (default: 20), `status` (optional)

**GET `/api/facebook/stats`** - Get Facebook synchronization statistics
- Headers: `Authorization: Bearer <token>`
- Response: `{ "success": true, "stats": { "total_posts": 100, "total_comments": 500, ... } }`

---

## GoHighLevel Routes (`/api/ghl`)

### Contact Management

**GET `/api/ghl/contacts`** - List contacts with optional filters
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit`, `page`, `query`, `sortBy`, `tags`, `dateCreated`

**GET `/api/ghl/contacts/<contact_id>`** - Get a specific contact
- Headers: `Authorization: Bearer <token>`

**POST `/api/ghl/contacts`** - Create a new contact
- Headers: `Authorization: Bearer <token>`
- Request: `{ "firstName": "John", "lastName": "Doe", "email": "john@example.com", ... }`

**PUT `/api/ghl/contacts/<contact_id>`** - Update a contact
- Headers: `Authorization: Bearer <token>`

**DELETE `/api/ghl/contacts/<contact_id>`** - Delete a contact
- Headers: `Authorization: Bearer <token>`

### Location Management

**GET `/api/ghl/locations/<location_id>`** - Get location details
- Headers: `Authorization: Bearer <token>`

### Campaign Management

**GET `/api/ghl/campaigns`** - List campaigns with optional filters
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit`, `page`, `status`

### Task Management

**GET `/api/ghl/tasks`** - List tasks with optional filters
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit`, `page`, `status`, `dueDate`

**POST `/api/ghl/tasks`** - Create a new task
- Headers: `Authorization: Bearer <token>`

**PUT `/api/ghl/tasks/<task_id>`** - Update a task
- Headers: `Authorization: Bearer <token>`

**DELETE `/api/ghl/tasks/<task_id>`** - Delete a task
- Headers: `Authorization: Bearer <token>`

### Calendar Management

**GET `/api/ghl/calendars`** - List calendars
- Headers: `Authorization: Bearer <token>`
- Query Params: `limit`, `page`

**GET `/api/ghl/calendars/<calendar_id>`** - Get a specific calendar
- Headers: `Authorization: Bearer <token>`

**POST `/api/ghl/calendars`** - Create a calendar
- Headers: `Authorization: Bearer <token>`

**PUT `/api/ghl/calendars/<calendar_id>`** - Update a calendar
- Headers: `Authorization: Bearer <token>`

**DELETE `/api/ghl/calendars/<calendar_id>`** - Delete a calendar
- Headers: `Authorization: Bearer <token>`

---

## Main Routes (`/api`)

### General Routes

**GET `/api/`** - Welcome message

### GoHighLevel OAuth

**GET `/api/ghl/auth`** - Get authorization URL for GoHighLevel OAuth

**GET `/api/ghlcallback`** - Handle OAuth callback from GoHighLevel
- Query Params: `code`, `error`, `error_description`

### GoHighLevel Data (Legacy)

**GET `/api/ghlRedirects`** - Handle GoHighLevel redirects

**GET `/api/ghl/contacts`** - Get contacts from GoHighLevel V2 API
- Headers: `Authorization: Bearer <token>`
- Query Params: `page` (default: 1), `limit` (default: 100)

**GET `/api/ghl/appointments`** - Get appointments from GoHighLevel
- Headers: `Authorization: Bearer <token>`

**GET `/api/ghl/conversations`** - Get conversations from GoHighLevel
- Headers: `Authorization: Bearer <token>`

**GET `/api/ghl/dashboard`** - Get overview of GoHighLevel data
- Headers: `Authorization: Bearer <token>`

### User Management

**POST `/api/setcode`** - Set user verification code
- Headers: `Authorization: Bearer <token>`
- Request: `{ "email": "user@example.com", "code": "verification_code" }`

### Webhooks

**POST `/api/zestal/webhook`** - Zestal webhook endpoint

**POST `/api/zestal/loglead`** - Log lead information
- Request: `{ "firstName": "John", "email": "john@example.com", ... }`

### Facebook Integration

**GET `/api/facebook-login`** - Render Facebook login page

### Background Tasks

**POST `/api/scrape`** - Trigger comment scraping in background

### Testing

**GET `/api/test`** - Test endpoint for AI comment generation

### Utility Routes

**GET `/api/favicon.ico`** - Handle favicon requests
**GET `/api/socket.io/`** - Handle socket.io requests
**GET `/api/robots.txt`** - Handle robots.txt requests
**GET `/api/sitemap.xml`** - Handle sitemap.xml requests

---

## Scheduler Routes (`/api/scheduler`)

### Job Management

**GET `/api/scheduler/jobs`** - Get list of scheduled jobs
- Headers: `Authorization: Bearer <token>`
- Response: `{ "success": true, "jobs": [...], "scheduler_running": true }`

**POST `/api/scheduler/jobs/<job_id>/trigger`** - Manually trigger a job
- Headers: `Authorization: Bearer <token>`

**POST `/api/scheduler/jobs/<job_id>/pause`** - Pause a job
- Headers: `Authorization: Bearer <token>`

**POST `/api/scheduler/jobs/<job_id>/resume`** - Resume a job
- Headers: `Authorization: Bearer <token>`

---

## Response Codes

- **200 OK** - Request successful
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request parameters
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error

---

## Authentication

Most endpoints require JWT authentication. Include token in Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Notes

- All endpoints support CORS for configured origins
- API uses JSON for request/response bodies
- Timestamps in ISO 8601 format
- Pagination available for list endpoints
- Error responses: `{"error": "error message"}`

---

## Last Updated
2024-01-15
