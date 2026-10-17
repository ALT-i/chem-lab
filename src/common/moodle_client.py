import requests
from typing import Any, Dict, List, Optional

from src.config.common import (
    MOODLE_BASE_URL,
    MOODLE_TOKEN,
    MOODLE_COURSE_ID,
    MOODLE_DEFAULT_ASSIGNMENT_ID,
)


class MoodleNotConfigured(Exception):
    """Raised when no usable Moodle site/token is available.

    Distinct from MoodleError so callers can return 'not set up yet'
    (an administrator action) rather than 'the call failed'.
    """


class MoodleError(Exception):
    """Raised when Moodle is configured but the request did not succeed."""


def get_moodle_settings():
    """Resolve Moodle settings: database configuration first, env as fallback.

    Imported lazily so this module stays importable before migrations run.
    """
    base_url, token = MOODLE_BASE_URL, MOODLE_TOKEN
    course_id, assignment_id = MOODLE_COURSE_ID, MOODLE_DEFAULT_ASSIGNMENT_ID
    try:
        from src.common.models import MoodleConfiguration

        config = MoodleConfiguration.objects.filter(pk=MoodleConfiguration.SINGLETON_PK).first()
    except Exception:  # table not migrated yet, or db unavailable
        config = None

    if config is not None:
        if not config.is_active:
            return {'base_url': '', 'token': '', 'course_id': course_id, 'default_assignment_id': assignment_id}
        base_url = config.base_url or base_url
        token = config.token or token
        if config.course_id is not None:
            course_id = config.course_id
        if config.default_assignment_id is not None:
            assignment_id = config.default_assignment_id

    return {
        'base_url': (base_url or '').rstrip('/'),
        'token': token or '',
        'course_id': course_id,
        'default_assignment_id': assignment_id,
    }


class MoodleClient:
    """Lightweight client for Moodle REST web services (JSON).

    Reads its connection details from the MoodleConfiguration row so an
    administrator can repoint the lab at a different Moodle site without a
    redeploy, falling back to MOODLE_BASE_URL / MOODLE_TOKEN settings.
    """

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None) -> None:
        resolved = get_moodle_settings()
        self.base_url = (base_url or resolved['base_url']).rstrip('/')
        self.token = token or resolved['token']
        self.course_id = resolved['course_id']
        self.default_assignment_id = resolved['default_assignment_id']
        if not self.base_url or not self.token:
            raise MoodleNotConfigured(
                "Moodle has not been set up yet. An administrator needs to add the Moodle "
                "site address and web service token in the admin dashboard."
            )

    def _endpoint(self) -> str:
        return f"{self.base_url}/webservice/rest/server.php"

    def _post(self, wsfunction: str, params: Dict[str, Any]) -> Any:
        data = {
            'wstoken': self.token,
            'wsfunction': wsfunction,
            'moodlewsrestformat': 'json',
        }
        data.update(params)
        try:
            # allow_redirects=False: the destination was validated, but a
            # redirect could hop somewhere internal and would carry the token.
            resp = requests.post(
                self._endpoint(), data=data, timeout=20, allow_redirects=False
            )
        except requests.RequestException as exc:
            raise MoodleError(f"Could not reach the Moodle site at {self.base_url}: {exc}") from exc

        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            raise MoodleError(
                f"The Moodle site at {self.base_url} redirected the request instead of "
                "answering it. A decommissioned MoodleCloud site does this. Check that "
                "the site address is correct and the site is still active."
            )

        if resp.status_code >= 400:
            # A decommissioned MoodleCloud site answers with a redirect to a
            # "not found" page rather than a Moodle API error, so say so plainly.
            raise MoodleError(
                f"The Moodle site at {self.base_url} returned HTTP {resp.status_code}. "
                "Check that the site address is correct and the site is still active."
            )

        try:
            payload = resp.json()
        except ValueError:
            raise MoodleError(
                f"The Moodle site at {self.base_url} did not return a valid API response. "
                "Check that the site address points at a live Moodle installation."
            )

        # Moodle errors often come as {"exception": ..., "message": ...}
        if isinstance(payload, dict) and payload.get('exception'):
            raise MoodleError(f"Moodle API error: {payload.get('message')} ({payload.get('exception')})")
        return payload

    def check_connection(self) -> Dict[str, Any]:
        """Validate the configured site/token. Raises MoodleError on failure."""
        return self._post('core_webservice_get_site_info', {})

    def get_users_by_email(self, emails: List[str]) -> List[Dict[str, Any]]:
        # core_user_get_users_by_field requires field and values[]
        params: Dict[str, Any] = {'field': 'email'}
        for idx, email in enumerate(emails):
            params[f"values[{idx}]"] = email
        result = self._post('core_user_get_users_by_field', params)
        return result

    def get_enrolled_users(self, course_id: int) -> List[Dict[str, Any]]:
        return self._post('core_enrol_get_enrolled_users', {'courseid': course_id})

    def get_assignment_by_course_module(self, course_module_id: int) -> Dict[str, Any]:
        """Get assignment details using course module ID (the ID in the URL)"""
        result = self._post('core_course_get_course_module', {'cmid': course_module_id})
        return result

    def save_assignment_grade(
        self,
        assignment_id: int,
        user_id: int,
        grade: float,
        feedback: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            'assignmentid': assignment_id,
            'userid': user_id,
            'grade': grade,
            'attemptnumber': -1,
            'addattempt': 0,
            'workflowstate': '',
            'applytoall': 0,
        }
        if feedback:
            params['plugindata[assignfeedbackcomments_editor][text]'] = feedback
            params['plugindata[assignfeedbackcomments_editor][format]'] = 1
        return self._post('mod_assign_save_grade', params)
