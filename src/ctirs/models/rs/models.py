import os
import hmac
import uuid
import hashlib
import pytz
from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from ctirs.models.gv.authentication.models import GVAuthUser
from ctirs.models.sns.authentication.models import Profile
from ctirs.models.sns.core.models import Region
import stip.common.const as const


COUNTRY_CODE_LIST = list(set([country_code_list['country_code'] for country_code_list in Region.objects.values('country_code')]))
LANGUAGE_LIST = [language_info[0] for language_info in const.LANGUAGES]


#####################
class STIPUserManager(BaseUserManager):
    def create_user(self, username, screen_name, password, is_admin=False):
        if not username:
            raise ValueError('Users must have an username')
        user = self.model(username=username, password=password)
        user.is_active = True
        user.set_password(password)
        user.is_admin = is_admin
        user.screen_name = screen_name
        if is_admin:
            user.gv_auth_user = GVAuthUser.objects.create_superuser()
            user.role = 'admin'
            user.is_superuser = True
        else:
            user.gv_auth_user = GVAuthUser.objects.create_user()
            user.role = 'user'
            user.is_superuser = False
        user.sns_profile = Profile.create_first_login()
        if os.name == 'posix':
            os_language, os_country_code, os_timezone = get_os_info()
            if os_country_code in COUNTRY_CODE_LIST:
                user.country_code = os_country_code
            if os_language in LANGUAGE_LIST:
                user.language = os_language
            if os_timezone in pytz.all_timezones:
                user.timezone = os_timezone
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(username=username, screen_name=username, password=password, is_admin=True)
        return user

def get_os_info():
    os_language = None
    os_country_code = None
    os_timezone = None
    try:
        with open('/etc/default/locale', 'r') as f:
            for i in  f.read().replace('"', '').split('\n'):
                if 'LANG=' in i:
                    locale_info = i[i.find('LANG=') + 5:i.find('.')].split('_')
                    if len(locale_info) == 2:
                        os_language = locale_info[0]
                        os_country_code = locale_info[1]
                    break
    except FileNotFoundError:
        pass
    try:
        with open('/etc/timezone', 'r') as f:
            os_timezone = f.read().split('\n')[0]
    except FileNotFoundError:
        pass
    return (os_language, os_country_code,  os_timezone)

class STIPUser(AbstractBaseUser, PermissionsMixin):
    # get_full_name/get_short_nameは必須メソッド
    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    @classmethod
    def make_api_key(self):
        return hmac.new(uuid.uuid4().bytes, digestmod=hashlib.sha1).hexdigest()

    def change_api_key(self):
        self.api_key = self.make_api_key()
        self.save()

    def create_gv_auth_user(self):
        self.gv_auth_user = GVAuthUser.objects.create_user()
        self.save()

    username = models.CharField(unique=True, max_length=30)
    screen_name = models.CharField(max_length=30, default='')
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=128, default='')
    timezone = models.CharField(max_length=128, default='UTC')
    is_modified_password = models.BooleanField(default=False)
    is_buildin = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, default=None, null=True)

    # RS/StipUser から移動
    location = models.CharField(max_length=50, null=True, blank=True)
    url = models.CharField(max_length=1024, null=True, blank=True)
    affiliation = models.CharField(max_length=50, null=True, blank=True)
    job_title = models.CharField(max_length=50, null=True, blank=True)
    evaluation = models.IntegerField(default=0)
    description = models.CharField(max_length=1024, null=True, blank=True)
    tlp = models.CharField(max_length=10, choices=const.TLP_CHOICES, default="AMBER")
    region = models.ForeignKey(Region, null=True)
    country_code = models.TextField(max_length=8, default='US', null=True)
    administrative_code = models.TextField(max_length=8, default=None, null=True)
    administrative_area = models.TextField(max_length=128, default=None, null=True)
    sector = models.CharField(max_length=128, choices=const.SECTOR_GROUP_CHOICES, null=True)
    ci = models.CharField(max_length=128, choices=const.CRITICAL_INFRASTRUCTURE_CHOICES, null=True)
    language = models.CharField(max_length=16, choices=const.LANGUAGES, default='en')
    role = models.CharField(max_length=10, choices=const.ROLE_CHOICES, default="user")
    gv_auth_user = models.ForeignKey(GVAuthUser, on_delete=models.CASCADE, default=1)
    sns_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=1)

    USERNAME_FIELD = 'username'
    ANONYMOUS_USER_ACCOUNT_NAME = 'anonymous'
    objects = STIPUserManager()

    class Meta:
        db_table = 'stip_common_user'

    @staticmethod
    def get_anonymous_user():
        return STIPUser.objects.get(username=STIPUser.ANONYMOUS_USER_ACCOUNT_NAME)

    @staticmethod
    def change_build_password(new_password):
        for build_in_account in STIPUser.objects.filter(is_buildin=True):
            build_in_account.set_password(new_password)
            build_in_account.is_modified_password = True
            build_in_account.save()
        return

    # sns の authentication.models.Profile から移動
    def get_screen_name(self):
        v = self.username
        if self.screen_name is not None:
            if len(self.screen_name) != 0:
                v = self.screen_name
        if isinstance(v, str):
            return v
        return v

    def get_url(self):
        if self.url is None:
            return ''
        url = self.url.encode()
        if "http://" not in self.url and "https://" not in self.url and len(self.url) > 0:  # noqa: E501
            # url = "http://" + str(self.url)
            url = "http://" + self.url
        return url

    def get_picture_location(self, prefix):
        s = prefix + '/profile_pictures/' + self.username + '.jpg'
        return s.encode()

    def get_picture(self):
        no_picture_url = '/static/img/user.png'
        try:
            filename = self.get_picture_location(const.MEDIA_ROOT)
            picture_url = self.get_picture_location(const.MEDIA_URL)
            if os.path.isfile(filename):
                return picture_url
            else:
                return no_picture_url
        except Exception:
            return no_picture_url

    def get_affiliation(self):
        return self.affiliation

    def get_evaluation(self):
        return self.evaluation

    def get_tlp(self):
        return self.tlp

    def get_description(self):
        return self.description

    def notify_liked(self, package_id, feed_user):
        from ctirs.models.sns.activities.models import Notification
        if self != feed_user:
            Notification(notification_type=Notification.LIKED,
                         from_user=self, to_user=feed_user,
                         package_id=package_id).save()

    def unotify_liked(self, package_id, feed_user):
        from ctirs.models.sns.activities.models import Notification
        if self != feed_user:
            Notification.objects.filter(notification_type=Notification.LIKED,
                                        from_user=self, to_user=feed_user,
                                        package_id=package_id).delete()

    def notify_commented(self, package_id, feed_user):
        from ctirs.models.sns.activities.models import Notification
        if self != feed_user:
            Notification(notification_type=Notification.COMMENTED,
                         from_user=self, to_user=feed_user,
                         package_id=package_id).save()


def pre_save_stipuser(sender, instance, **kwargs):
    try:
        if instance.gv_auth_user == 0:
            # Profile がない
            instance.gv_auth_user = GVAuthUser.objects.create_user()
            instance.save()
    except BaseException:
        # Profile がない
        instance.gv_auth_user = GVAuthUser.objects.create_user()
        instance.save()


pre_save.connect(pre_save_stipuser, sender=STIPUser)


#####################
class SystemManager(models.Manager):
    def modify(self, community_root_dir, suffix_list_file_path, http_proxy=None, https_proxy=None):
        config = self.get()
        config.community_root_dir = community_root_dir
        config.public_suffix_list_file_path = suffix_list_file_path
        if http_proxy is not None:
            config.http_proxy = http_proxy
        if https_proxy is not None:
            config.https_proxy = https_proxy
        config.save()
        return

    def get_community_root_dir(self):
        return self.get().community_root_dir

    def get_public_suffix_list_file_path(self):
        return self.get().public_suffix_list_file_path


class System(models.Model):
    community_root_dir = models.FilePathField(max_length=100)
    public_suffix_list_file_path = models.FilePathField(max_length=1024, default='')
    http_proxy = models.CharField(max_length=1024, default='')
    https_proxy = models.CharField(max_length=1024, default='')
    objects = SystemManager()

    class Meta:
        db_table = 'stip_rs_system'

    @staticmethod
    def get_request_proxies():
        return System.get_requets_proxies()

    @staticmethod
    def get_requets_proxies():
        try:
            config = System.objects.get()
        except BaseException:
            # 未定義
            return None
        if len(config.http_proxy) == 0 and len(config.https_proxy) == 0:
            # 未定義
            return None
        proxies = {}
        if len(config.http_proxy) != 0:
            proxies['http'] = config.http_proxy
        if len(config.https_proxy) != 0:
            proxies['https'] = config.https_proxy
        return proxies


#####################
class MongoConfigManager(models.Manager):
    def modify(self, host, port, db):
        c = self.get()
        c.host = host
        c.port = port
        c.db = db
        c.save()
        return


class MongoConfig(models.Model):
    host = models.CharField(max_length=100, default='')
    port = models.IntegerField(default=27017)
    db = models.CharField(max_length=100, default='ctirs')
    objects = MongoConfigManager()

    class Meta:
        db_table = 'stip_rs_mongo'
