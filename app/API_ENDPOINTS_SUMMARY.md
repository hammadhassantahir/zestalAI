# ZestalAI API Endpoints Summary

Quick reference of all API endpoints organized by module.

## Authentication Routes (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | Login with email/password | No |
| POST | `/api/auth/signup` | Register new user | No |
| POST | `/api/auth/facebook/login` | Login with Facebook token | No |
| GET | `/api/auth/facebook/callback` | Facebook OAuth callback | No |
| GET | `/api/auth/facebook/redirect` | Facebook OAuth redirect | No |
| GET/POST | `/api/auth/facebook/webhook` | Facebook webhook | No |
| GET | `/api/auth/verify` | Verify JWT token | Yes |
| POST | `/api/auth/check-email` | Check if email exists | No |
| POST | `/api/auth/facebook/fetch-posts` | Fetch posts from Facebook | Yes |
| GET | `/api/auth/facebook/posts` | Get posts from database | Yes |
| POST | `/api/auth/facebook/refresh-token` | Refresh Facebook token | Yes |
| GET | `/api/auth/facebook/check-token` | Check token status | Yes |
| POST | `/api/auth/facebook/posts/<id>/fetch-comments` | Fetch post comments | Yes |

## Facebook Routes (`/api/facebook`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/facebook/sync/posts` | Sync posts manually | Yes |
| POST | `/api/facebook/sync/comments` | Sync comments manually | Yes |
| POST | `/api/facebook/sync/all` | Full sync (posts+comments) | Yes |
| GET | `/api/facebook/jobs/<id>` | Get job status | Yes |
| GET | `/api/facebook/jobs` | Get user jobs | Yes |
| GET | `/api/facebook/stats` | Get sync statistics | Yes |

## GoHighLevel Routes (`/api/ghl`)

### Contacts
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ghl/contacts` | List contacts | Yes |
| GET | `/api/ghl/contacts/<id>` | Get contact | Yes |
| POST | `/api/ghl/contacts` | Create contact | Yes |
| PUT | `/api/ghl/contacts/<id>` | Update contact | Yes |
| DELETE | `/api/ghl/contacts/<id>` | Delete contact | Yes |

### Locations
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ghl/locations/<id>` | Get location | Yes |

### Campaigns
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ghl/campaigns` | List campaigns | Yes |

### Tasks
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ghl/tasks` | List tasks | Yes |
| POST | `/api/ghl/tasks` | Create task | Yes |
| PUT | `/api/ghl/tasks/<id>` | Update task | Yes |
| DELETE | `/api/ghl/tasks/<id>` | Delete task | Yes |

### Calendars
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/ghl/calendars` | List calendars | Yes |
| GET | `/api/ghl/calendars/<id>` | Get calendar | Yes |
| POST | `/api/ghl/calendars` | Create calendar | Yes |
| PUT | `/api/ghl/calendars/<id>` | Update calendar | Yes |
| DELETE | `/api/ghl/calendars/<id>` | Delete calendar | Yes |

## Main Routes (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/` | Welcome message | No |
| GET | `/api/ghl/auth` | Get GHL auth URL | No |
| GET | `/api/ghlcallback` | GHL OAuth callback | No |
| GET | `/api/ghlRedirects` | Handle GHL redirects | No |
| GET | `/api/ghl/contacts` | Get contacts (V2) | Yes |
| GET | `/api/ghl/appointments` | Get appointments | Yes |
| GET | `/api/ghl/conversations` | Get conversations | Yes |
| GET | `/api/ghl/dashboard` | Get dashboard data | Yes |
| POST | `/api/setcode` | Set verification code | Yes |
| POST | `/api/zestal/webhook` | Webhook endpoint | No |
| POST | `/api/zestal/loglead` | Log lead data | No |
| GET | `/api/facebook-login` | Facebook login page | No |
| POST | `/api/scrape` | Trigger scraping | No |
| GET | `/api/test` | Test endpoint | No |

## Scheduler Routes (`/api/scheduler`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/scheduler/jobs` | Get scheduled jobs | Yes |
| POST | `/api/scheduler/jobs/<id>/trigger` | Trigger job | Yes |
| POST | `/api/scheduler/jobs/<id>/pause` | Pause job | Yes |
| POST | `/api/scheduler/jobs/<id>/resume` | Resume job | Yes |

---

## Total Endpoint Count

- Authentication: 14 endpoints
- Facebook: 6 endpoints
- GoHighLevel: 21 endpoints
- Main: 14 endpoints
- Scheduler: 4 endpoints

**Total: 59 API endpoints**

---

## Authentication

Most endpoints require JWT token in header:
```
Authorization: Bearer <token>
```

## Base URL
- Production: `https://app.zestal.pro`
- Development: `http://localhost:5000`
