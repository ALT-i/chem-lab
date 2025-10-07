# Moodle Integration Documentation

## Overview

This document describes the integration between the CHM Lab virtual chemistry application and Moodle LMS, enabling automatic grade submission and student profile synchronization.

## Features

### 1. User Profile Synchronization
- Fetches student profile from Moodle on login
- Displays Moodle name and profile picture in the application
- Automatic fallback to initials if profile image unavailable

### 2. Automatic Grade Submission
- Students can submit completed experiments to Moodle
- Grades are posted to specific Moodle assignments
- Per-experiment assignment mapping supported
- Completion validation ensures students finish all steps before submission

### 3. Course Enrollment Verification
- Checks if student is enrolled in CHM 191 course
- Provides meaningful error messages for unenrolled students
- Validates assignment configuration before submission

## Architecture

### Backend Components

#### 1. Moodle Client (`src/common/moodle_client.py`)
Core client for interacting with Moodle REST API:

```python
class MoodleClient:
    def get_users_by_email(emails: List[str]) -> List[Dict]
    def get_enrolled_users(course_id: int) -> List[Dict]
    def save_assignment_grade(assignment_id: int, user_id: int, grade: float, feedback: str)
```

**Functions:**
- `get_users_by_email()` - Lookup Moodle users by email address
- `get_enrolled_users()` - Get all students enrolled in a course
- `save_assignment_grade()` - Submit grade for an assignment

#### 2. API Endpoints (`src/workspace/views.py`)

**GET `/api/v1/moodle/students/?course_id=<id>`**
- Lists all students enrolled in a course
- Requires: JWT authentication + Instructor/Admin role
- Response: List of Moodle user objects

**GET `/api/v1/moodle/user/profile/?email=<email>`**
- Fetches Moodle profile for a user by email
- Requires: JWT authentication
- Response: Moodle user profile with name, email, profile image

**POST `/api/v1/moodle/grades/assignment/`**
- Submits grades for an assignment
- Requires: JWT authentication
- Request body:
```json
{
  "course_id": 9,
  "assignment_id": 1,
  "grades": [
    {
      "email": "student@example.com",
      "grade": 85.5,
      "feedback": "Great work!"
    }
  ]
}
```
- Response: Results array with success/error status per student

#### 3. Database Schema

**Lesson Model** (`src/workspace/models.py`)
```python
class Lesson(models.Model):
    # ... existing fields ...
    moodle_assignment_id = models.IntegerField(
        blank=True, 
        null=True, 
        help_text="Moodle assignment ID for grade submission"
    )
```

**Migration:** `src/workspace/migrations/0016_lesson_moodle_assignment_id.py`

### Frontend Components

#### 1. Login Integration (`src/renderer/components/sections/SectionLogin.tsx`)
- Fetches Moodle profile after successful Django login
- Stores profile data in localStorage:
  - `user_data` - User's full name (from Moodle)
  - `user_email` - User's email
  - `user_avatar` - Profile image URL
  - `moodle_profile` - Full Moodle profile object

#### 2. Sidebar Profile Display (`src/renderer/components/sections/SectionSidePanel.tsx`)
- Displays Moodle profile image or initials
- Shows full name from Moodle profile
- Graceful fallback for missing/failed images

#### 3. Experiment Completion (`src/renderer/components/IndexPage.tsx`)
- Tracks experiment completion via `AnimationBox` callback
- Disables "Submit to Moodle" button until all steps completed
- Visual indicators:
  - ⚠️ Yellow badge: "Complete all steps to submit"
  - ✅ Green badge: "Experiment Complete"
- Validates before submission:
  1. User email exists
  2. Experiment is completed
  3. Assignment ID is configured
  4. User is enrolled in course

#### 4. Quiz Results (`src/renderer/components/sections/SectionQuizBox.tsx`)
- "Submit to Moodle" button on quiz results
- Converts score to percentage (0-100)
- Includes quiz score in feedback

## Configuration

### Backend Environment Variables

Required in `.env` or environment:

```bash
# Moodle Base URL (without trailing slash)
MOODLE_BASE_URL=https://your-site.moodlecloud.com

# Moodle Web Service Token
MOODLE_TOKEN=your_token_here

# CHM 191 Course ID
MOODLE_COURSE_ID=9

# Default Assignment ID (can be overridden per experiment)
MOODLE_DEFAULT_ASSIGNMENT_ID=1
```

### Frontend Configuration

In `src/renderer/utils.js` and `src/renderer/utils/index.js`:

```javascript
const server = {
  absolute_url: 'http://localhost:8001',  // Local testing
  // absolute_url: 'https://chem-lab-backend.onrender.com',  // Production
  // ... other endpoints ...
  moodle_students: 'api/v1/moodle/students/',
  moodle_user_profile: 'api/v1/moodle/user/profile/',
  moodle_assignment_grades: 'api/v1/moodle/grades/assignment/',
}
```

### Moodle Setup

#### 1. Enable Web Services
1. **Site administration** → **Advanced features**
2. Enable "Enable web services"
3. Save changes

#### 2. Enable REST Protocol
1. **Site administration** → **Plugins** → **Web services** → **Manage protocols**
2. Enable "REST protocol"

#### 3. Create External Service
1. **Site administration** → **Plugins** → **Web services** → **External services**
2. Click "Add" to create new service
3. Name: "CHM Lab Integration"
4. Enabled: Yes
5. Authorized users only: No (or add specific users)
6. Add these functions:
   - `core_user_get_users_by_field`
   - `core_enrol_get_enrolled_users`
   - `mod_assign_save_grade`

#### 4. Create Web Service Token
1. **Site administration** → **Plugins** → **Web services** → **Manage tokens**
2. Click "Add"
3. Select user (admin or service account)
4. Select the service created above
5. Copy the generated token → use as `MOODLE_TOKEN`

#### 5. Create Course and Assignment
1. Create course "CHM 191" (note the course ID from URL)
2. Add Assignment activity: "Lab Exercise"
3. Get assignment ID:
```bash
curl -s "https://your-site.moodlecloud.com/webservice/rest/server.php" \
  --data "wstoken=YOUR_TOKEN" \
  --data "wsfunction=mod_assign_get_assignments" \
  --data "moodlewsrestformat=json" \
  --data "courseids[0]=COURSE_ID"
```

#### 6. Confirm Student Emails
- Ensure student accounts have confirmed emails
- Unconfirmed emails get `.invalid` appended
- To confirm: **Site administration** → **Users** → **Browse list of users** → Edit user → Check "Confirmed"

## Usage Workflow

### Student Workflow

1. **Login to CHM Lab**
   - Django authentication with email/password
   - Moodle profile automatically fetched
   - Profile image and name displayed in sidebar

2. **Complete Experiment**
   - Work through all experiment steps
   - System tracks completion automatically
   - "Submit to Moodle" button activates when complete

3. **Submit to Moodle**
   - Click "📤 Submit to Moodle" button
   - Validation checks run automatically
   - Grade (100 points) submitted to Moodle assignment
   - Success confirmation displayed

4. **Complete Quiz (Optional)**
   - Take quiz after experiment
   - View results and score
   - Click "Submit to Moodle" on results page
   - Percentage-based grade submitted

### Instructor Workflow

1. **Configure Experiments**
   - Login to Django admin: `/admin/`
   - Navigate to **Workspace** → **Lessons**
   - Edit each lesson/experiment
   - Set `Moodle assignment id` field
   - Save changes

2. **View Grades in Moodle**
   - Login to Moodle
   - Navigate to CHM 191 course
   - Click **Grades** to view gradebook
   - View individual assignment grades
   - Review student submissions and feedback

3. **Manage Enrollments**
   - Enroll students in CHM 191 course on Moodle
   - Ensure student emails match Django accounts
   - Students auto-verified on first submission

## Error Handling

### User-Facing Messages

| Condition | Message |
|-----------|---------|
| Email missing | "Missing user email. Please log in again." |
| Experiment incomplete | "⚠️ Please complete all experiment steps before submitting to Moodle." |
| No assignment configured | "This experiment is not linked to a Moodle assignment yet. Please contact your instructor." |
| Not enrolled in course | "⚠️ You are not enrolled in the CHM 191 course on Moodle. Please contact your instructor to be added to the course." |
| Moodle API error | "Failed to submit: [error details]" |
| Success | "✅ Successfully submitted to Moodle!" |

### Backend Error Responses

**401 Unauthorized**
- JWT token missing or invalid
- Solution: Re-login to get fresh token

**404 Not Found**
- User not found in Moodle (by email)
- Assignment ID doesn't exist
- Solution: Check email matches, verify assignment ID

**500 Internal Server Error**
- Moodle API connection failure
- Database error
- Solution: Check logs, verify Moodle token and URL

## Testing

### Local Testing Checklist

- [ ] Backend running with Moodle env vars set
- [ ] Frontend pointing to `localhost:8001`
- [ ] Test user exists in both Django and Moodle
- [ ] Emails match between systems
- [ ] Test user enrolled in CHM 191 on Moodle
- [ ] Assignment created and ID configured
- [ ] Login successful, profile loads
- [ ] Complete experiment, button enables
- [ ] Submit to Moodle succeeds
- [ ] Grade appears in Moodle gradebook

### Test Cases

1. **Profile Fetch on Login**
   - Login with valid credentials
   - Check browser console for "Moodle profile fetched"
   - Verify name and avatar display correctly

2. **Experiment Submission**
   - Start experiment, verify button is disabled
   - Complete all steps
   - Verify button becomes enabled with green badge
   - Submit, check for success message
   - Verify grade in Moodle

3. **Error Cases**
   - Try submitting before completion → warning message
   - Try submitting unenrolled user → enrollment message
   - Try experiment without assignment ID → config message

## API Reference

### Moodle Web Service Functions Used

**core_user_get_users_by_field**
```
Parameters:
  - field: "email"
  - values[0]: "user@example.com"
Returns: Array of user objects
```

**core_enrol_get_enrolled_users**
```
Parameters:
  - courseid: 9
Returns: Array of enrolled user objects
```

**mod_assign_save_grade**
```
Parameters:
  - assignmentid: 1
  - userid: 12
  - grade: 85.5
  - attemptnumber: -1
  - addattempt: 0
  - workflowstate: ""
  - applytoall: 0
  - plugindata[assignfeedbackcomments_editor][text]: "feedback"
  - plugindata[assignfeedbackcomments_editor][format]: 1
Returns: Success/error response
```

## Troubleshooting

### Common Issues

**Issue: 404 when fetching user profile**
- **Cause:** Email mismatch between Django and Moodle
- **Solution:** Confirm emails match exactly, including case

**Issue: "dml_missing_record_exception"**
- **Cause:** Wrong assignment ID (using course module ID instead)
- **Solution:** Use `mod_assign_get_assignments` to get correct ID

**Issue: Profile image doesn't load**
- **Cause:** Moodle image URLs require authentication/CORS
- **Solution:** Image gracefully falls back to initials

**Issue: 500 error when loading lessons**
- **Cause:** Migration not applied for `moodle_assignment_id`
- **Solution:** Run `python manage.py migrate workspace`

**Issue: "accessexception" from Moodle**
- **Cause:** Web service function not enabled in service
- **Solution:** Add required functions to external service

### Debug Mode

Enable detailed Moodle client logging (already implemented):
```python
# In moodle_client.py
print(f"[Moodle] Searching for users by email: {emails}")
print(f"[Moodle] Found {len(result)} users")
print(f"[Moodle] Saving grade: assignment_id={assignment_id}, user_id={user_id}, grade={grade}")
```

Check Django logs for Moodle API interactions.

## Security Considerations

1. **Token Security**
   - Store Moodle token in environment variables only
   - Never commit tokens to version control
   - Rotate tokens periodically

2. **Authentication**
   - All endpoints require JWT authentication
   - Grade submission restricted to authenticated users
   - Enrollment verification before grade submission

3. **Data Privacy**
   - Only fetch profiles for authenticated users
   - Grade submission limited to user's own email
   - No bulk data exposure

## Future Enhancements

### Potential Improvements

1. **Multiple Assignment Support**
   - UI for instructor to map assignments in app
   - Assignment selector per experiment type

2. **Grade Caching**
   - Cache submitted grades locally
   - Prevent duplicate submissions
   - Sync status indicator

3. **Gradebook Integration**
   - View Moodle grades within app
   - Progress tracking across experiments
   - Grade history

4. **Batch Operations**
   - Instructor bulk grade upload
   - Class-wide grade reports
   - Export functionality

5. **Enhanced Profile Sync**
   - Profile image proxy to avoid CORS
   - Sync additional profile fields
   - Real-time profile updates

## Support

For issues or questions:
- Check Django logs: `docker-compose logs web`
- Check Moodle logs: **Site administration** → **Reports** → **Logs**
- Review this documentation
- Contact development team

## Changelog

### Version 1.0.0 (Current)
- Initial Moodle integration
- Profile synchronization on login
- Experiment completion tracking
- Grade submission for completed experiments
- Quiz results submission
- Per-experiment assignment mapping
- Enrollment verification
- Comprehensive error handling

---

**Last Updated:** January 2025
**Integration Version:** 1.0.0
**Moodle Version Tested:** 4.x (MoodleCloud)

