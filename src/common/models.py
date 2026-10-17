from django.db import models

from src.users.models import User


class MoodleConfiguration(models.Model):
    """The institution's own Moodle connection details.

    Stored in the database rather than environment variables so the NOUN
    team can point the lab at their own Moodle site -- and rotate the web
    service token -- without a redeploy. A single row (pk=1) is used.

    Settings values (MOODLE_BASE_URL / MOODLE_TOKEN / ...) remain as a
    fallback so existing deployments keep working until a row is saved.
    """

    SINGLETON_PK = 1

    base_url = models.URLField(
        blank=True,
        default='',
        help_text="Moodle site root, e.g. https://your-site.moodlecloud.com (no trailing /webservice path)",
    )
    token = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Web service token generated in Moodle under Site administration > Server > Web services > Manage tokens",
    )
    course_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Moodle course ID that the lab's experiments belong to",
    )
    default_assignment_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Fallback assignment ID used only when a lesson has none of its own",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to disable the Moodle integration without deleting the credentials",
    )

    last_verified_at = models.DateTimeField(null=True, blank=True)
    last_verification_error = models.TextField(blank=True, default='')

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        verbose_name = 'Moodle configuration'
        verbose_name_plural = 'Moodle configuration'

    def __str__(self):
        if not self.is_configured:
            return 'Moodle configuration (not set up)'
        return f'Moodle configuration ({self.base_url})'

    def save(self, *args, **kwargs):
        # Enforce the singleton: there is only ever one configuration row.
        self.pk = self.SINGLETON_PK
        if self.base_url:
            self.base_url = self.base_url.rstrip('/')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - guarded in admin too
        raise RuntimeError('The Moodle configuration row cannot be deleted; clear the fields instead.')

    @property
    def is_configured(self):
        return bool(self.is_active and self.base_url and self.token)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return obj
