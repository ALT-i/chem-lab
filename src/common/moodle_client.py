import requests
from typing import Any, Dict, List, Optional

from src.config.common import MOODLE_BASE_URL, MOODLE_TOKEN


class MoodleClient:
    """Lightweight client for Moodle REST web services (JSON).

    Requires MOODLE_BASE_URL and MOODLE_TOKEN to be configured.
    """

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None) -> None:
        self.base_url = (base_url or MOODLE_BASE_URL).rstrip('/')
        self.token = token or MOODLE_TOKEN
        if not self.base_url or not self.token:
            raise ValueError("Moodle configuration missing: set MOODLE_BASE_URL and MOODLE_TOKEN")

    def _endpoint(self) -> str:
        return f"{self.base_url}/webservice/rest/server.php"

    def _post(self, wsfunction: str, params: Dict[str, Any]) -> Any:
        data = {
            'wstoken': self.token,
            'wsfunction': wsfunction,
            'moodlewsrestformat': 'json',
        }
        data.update(params)
        resp = requests.post(self._endpoint(), data=data, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
        # Moodle errors often come as {"exception": ..., "message": ...}
        if isinstance(payload, dict) and payload.get('exception'):
            raise RuntimeError(f"Moodle API error: {payload.get('message')} ({payload.get('exception')})")
        return payload

    def get_users_by_email(self, emails: List[str]) -> List[Dict[str, Any]]:
        # core_user_get_users_by_field requires field and values[]
        params: Dict[str, Any] = {'field': 'email'}
        for idx, email in enumerate(emails):
            params[f"values[{idx}]"] = email
        print(f"[Moodle] Searching for users by email: {emails}")
        result = self._post('core_user_get_users_by_field', params)
        print(f"[Moodle] Found {len(result) if result else 0} users")
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
        print(f"[Moodle] Saving grade: assignment_id={assignment_id}, user_id={user_id}, grade={grade}")
        try:
            result = self._post('mod_assign_save_grade', params)
            print(f"[Moodle] Grade saved successfully")
            return result
        except Exception as e:
            print(f"[Moodle] Error saving grade: {e}")
            raise


