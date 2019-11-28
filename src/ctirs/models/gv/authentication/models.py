from django.db import models

####################


class GVAuthUserManager(models.Manager):
    def create_user(self, is_l1_view=False, is_l2_view=False, is_sharing_view=False):
        user = GVAuthUser()
        user.is_l1_view = is_l1_view
        user.is_l2_view = is_l2_view
        user.is_sharing_view = is_sharing_view
        user.save(using=self._db)
        return user

    def create_superuser(self):
        user = self.create_user(is_l1_view=True, is_l2_view=True, is_sharing_view=True)
        user.save(using=self._db)
        return user


class GVAuthUser(models.Model):
    is_l1_view = models.BooleanField(default=True)
    is_l2_view = models.BooleanField(default=True)
    is_sharing_view = models.BooleanField(default=False)
    css_thema = models.CharField(max_length=30, default='default')
    objects = GVAuthUserManager()

    class Meta:
        db_table = 'stip_gv_user'
