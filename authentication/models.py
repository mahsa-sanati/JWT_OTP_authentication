from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver 
from django.db.models.signals import post_save
from django.utils.text import slugify
from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager, 
    PermissionsMixin,
    )
from unidecode import unidecode
import uuid

from authentication.api.regex_validators import (
    mobile_regex,
    )


def get_img_upload_path(instance, filename):
    return f'media/{str(instance.user.mobile)}/{filename}'


class UserManager(BaseUserManager):
    def create_user(self, mobile, email, username, password):
        if not mobile:
            raise ValueError('Users must have a mobile')
        if not password:
            raise ValueError('Users must have a password')
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have a email')        

        user = self.model(
            mobile=mobile, 
            email=email, 
            username=username
            )
        user.set_password(password)
        user.save(using=self._db)        
        return user

    def create_superuser(self, mobile, username, password=None):
        user = self.model(
            mobile=mobile, 
            username=username
            )
        user.set_password(password)
        user.is_superuser = True
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    STATUS = (
        (0, _('active')),
        (1, _('inactive')),
        (2, _('blocked')),
    )

    id = models.UUIDField(
        primary_key=True, 
        editable=False, 
        default=uuid.uuid4
        )
    mobile = models.CharField(
        validators=[mobile_regex],
        max_length=11,
        unique=True,
    )
    is_admin = models.BooleanField(
        blank=True, 
        null=True, 
        default=False
        )
    username = models.CharField(
        max_length=25, 
        unique=True
        )
    first_name = models.CharField(
        max_length=80, 
        null=True, 
        blank=True
        )
    last_name = models.CharField(
        max_length=80, 
        null=True, 
        blank=True
        )
    slug = models.SlugField(
        allow_unicode=True, 
        )    
    email = models.EmailField(
        max_length=50, 
        unique=True
        )
    created_at = models.DateTimeField(
        default=now
        )
    status = models.SmallIntegerField(
        choices=STATUS, 
        default=0
        )
    objects = UserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'

    def __str__(self):
        return self.username

    def get_short_name(self):
        return self.mobile

    @property
    def is_staff(self):
        return self.is_admin
    
    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        self.slug = slugify(unidecode(str(self.username)))
        super(User, self).save(*args, **kwargs)


class Profile(models.Model):
    GENDER = (
        ('m', _('male')),
        ('f', _('female')),
    )  
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
        )
    gender = models.CharField(
        choices=GENDER, 
        null=True, 
        blank=True
        )
    birthday = models.DateField(
        null=True, 
        blank=True
        )
    avatar = models.ImageField(
        upload_to=get_img_upload_path, 
        null=True, 
        blank=True
        )
    about_me = models.TextField(
        null=True, 
        blank=True, 
        max_length=300
        )
    updated_at = models.DateTimeField(default=now)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User) 
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return self.user.username
    