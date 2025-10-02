# Facebook Scheduler Service

This document explains how the new scheduler service works and how to use it.

## Overview

The Facebook Background Service now runs using APScheduler instead of cron jobs. This provides better integration with your Flask application and more control over scheduled tasks.

## Features

### Scheduled Jobs

1. **Fetch Facebook Posts** - Runs every hour
   - Fetches recent posts for all users with valid Facebook tokens
   - Updates engagement metrics (likes, comments, shares)
   - Fetches comments for posts

2. **Cleanup Expired Tokens** - Runs daily at 2:00 AM
   - Removes expired Facebook access tokens from the database
   - Cleans up user records with invalid tokens

3. **Health Check** - Runs every 30 minutes
   - Monitors scheduler status
   - Logs scheduler health information

### API Endpoints

The scheduler provides REST API endpoints for management:

- `GET /api/scheduler/jobs` - List all scheduled jobs
- `POST /api/scheduler/jobs/{job_id}/trigger` - Manually trigger a job
- `POST /api/scheduler/jobs/{job_id}/pause` - Pause a job
- `POST /api/scheduler/jobs/{job_id}/resume` - Resume a job

### Example Usage

```bash
# List all jobs
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/scheduler/jobs

# Manually trigger Facebook posts fetch
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/scheduler/jobs/fetch_facebook_posts/trigger

# Pause a job
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/scheduler/jobs/fetch_facebook_posts/pause

# Resume a job
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/scheduler/jobs/fetch_facebook_posts/resume
```

## Benefits Over Cron

1. **Better Integration**: Runs within Flask application context
2. **Web Management**: API endpoints for job management
3. **Error Handling**: Built-in error handling and logging
4. **Flexibility**: Easy to modify schedules without server restarts
5. **Monitoring**: Built-in job monitoring and status tracking
6. **Manual Triggers**: Can trigger jobs manually for testing

## Installation

The scheduler is automatically installed and started when you run your Flask application. No additional setup is required.

## Logging

Scheduler logs are written to the application log. You can monitor the logs to see:
- Job execution status
- Error messages
- Performance metrics
- User activity

## Migration from Cron

If you were previously using the cron script (`facebook_cron.sh`), you can now:
1. Remove the cron job entry
2. The scheduler will automatically handle all Facebook data fetching
3. Use the API endpoints for manual control when needed

## Troubleshooting

### Scheduler Not Starting
- Check application logs for initialization errors
- Ensure APScheduler is installed: `pip install APScheduler==3.10.4`
- Verify database connection is working

### Jobs Not Running
- Check if scheduler is running: `GET /api/scheduler/jobs`
- Review logs for error messages
- Manually trigger jobs to test functionality

### Performance Issues
- Monitor job execution times in logs
- Consider adjusting job intervals if needed
- Check database performance during scheduled runs

## Configuration

Job schedules can be modified in `/app/services/scheduler_service.py`:

```python
# Change Facebook posts fetch interval
IntervalTrigger(hours=1)  # Change to hours=2 for every 2 hours

# Change cleanup time
CronTrigger(hour=2, minute=0)  # Change to hour=3 for 3 AM
```
