

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import escape
from ctirs.models import STIPUser

@python_2_unicode_compatible
class Activity(models.Model):
    FAVORITE = 'F'
    LIKE = 'L'
    UP_VOTE = 'U'
    DOWN_VOTE = 'D'
    ACTIVITY_TYPES = (
        (FAVORITE, 'Favorite'),
        (LIKE, 'Like'),
        )

    user = models.ForeignKey(STIPUser)
    activity_type = models.CharField(max_length=1, choices=ACTIVITY_TYPES)
    date = models.DateTimeField(auto_now_add=True)
    feed = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        db_table = 'stip_sns_activity'

    def __str__(self):
        return self.activity_type


@python_2_unicode_compatible
class Notification(models.Model):
    LIKED = 'L'
    COMMENTED = 'C'
    ALSO_COMMENTED = 'S'
    NOTIFICATION_TYPES = (
        (LIKED, 'Liked'),
        (COMMENTED, 'Commented'),
        (ALSO_COMMENTED, 'Also Commented'),
        )

    _LIKED_TEMPLATE = '<a href="/{0}/">{1}</a> liked your post: <a href="/feeds/{2}/">{3}</a>'  # noqa: E501
    _COMMENTED_TEMPLATE = '<a href="/{0}/">{1}</a> commented on your post: <a href="/feeds/{2}/">{3}</a>'  # noqa: E501
    _ALSO_COMMENTED_TEMPLATE = '<a href="/{0}/">{1}</a> also commentend on the post: <a href="/feeds/{2}/">{3}</a>'  # noqa: E501

    from_user = models.ForeignKey(STIPUser, related_name='+')
    to_user = models.ForeignKey(STIPUser, related_name='+')
    date = models.DateTimeField(auto_now_add=True)
    package_id = models.CharField(max_length=256, null=True, blank=True)
    notification_type = models.CharField(max_length=1,
                                         choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        db_table = 'stip_sns_notification'
        ordering = ('-date',)

    def __str__(self):
        if self.notification_type == self.LIKED:
            return self._LIKED_TEMPLATE.format(
                escape(self.from_user.username),
                escape(self.from_user.get_screen_name()),
                self.package_id,
                escape(self.get_summary(''))
                )
        elif self.notification_type == self.COMMENTED:
            return self._COMMENTED_TEMPLATE.format(
                escape(self.from_user.username),
                escape(self.from_user.get_screen_name()),
                self.package_id,
                escape(self.get_summary(''))
                )
        elif self.notification_type == self.ALSO_COMMENTED:
            return self._ALSO_COMMENTED_TEMPLATE.format(
                escape(self.from_user.username),
                escape(self.from_user.get_screen_name()),
                self.package_id,
                escape(self.get_summary(''))
                )
        else:
            return 'Ooops! Something went wrong.'

    def get_summary(self, value):
        summary_size = 50
        if len(value) > summary_size:
            return '{0}...'.format(value[:summary_size])

        else:
            return value
