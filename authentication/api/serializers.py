from rest_framework import serializers
from django.db.models import Q
from django.contrib.auth import authenticate

from authentication.models import User, Profile
from .regex_validators import (
    username_format,
    mobile_format,
    otp_format,
)
from .utils import (
    check_dirty_content,
    get_user_from_request,
    user_verify_otp
)
from .exceptions import (
    NotConfirmedPasswordException,
    UserExistException,
    IncorrectMobileException,
    BlockedException,
    IncorrectMobileEmailUsernameException,
    IncorrectPasswordException,
)


class SendOtpSerializer(serializers.Serializer):
    mobile = serializers.RegexField(
        required=True,
        regex=mobile_format,
    )

    def validate(self, data):
        has_account = self.context.get('has_account', False)
        user = User.objects.filter(mobile__iexact=data['mobile'])
        if has_account:
            if not user.exists():
                raise IncorrectMobileException()
        else:
            if user.exists():
                raise UserExistException()
        return data


class VerifyOtpSerializer(serializers.Serializer):
    otp = serializers.RegexField(
        required=True,
        regex=otp_format,
    )
    mobile = serializers.RegexField(
        required=True,
        regex=mobile_format,
    )

    def validate(self, data):
        user_verify_otp(data['mobile'], data['otp'])
        return data


class UserSignUpSerializer(serializers.Serializer):
    otp = serializers.RegexField(
        required=True,
        regex=otp_format,
    )
    mobile = serializers.RegexField(
        required=True,
        regex=mobile_format,
    )
    username = serializers.RegexField(
        regex=username_format,
        required=True,
        min_length=5,
    )
    email = serializers.EmailField(
        required=True,
    )
    password = serializers.CharField(
        min_length=6,
        required=True,
    )
    password2 = serializers.CharField(
        required=True,
    )

    def validate(self, data):
        if data['password'] != data['password2']:
            raise NotConfirmedPasswordException()
        user_verify_otp(
            mobile=data['mobile'],
            otp=data['otp'],
            set_again_in_redis=False
        )
        check_dirty_content(data['username'])
        user = User.objects.filter(
            Q(mobile__iexact=data['mobile']) | Q(email__iexact=data['email']) | Q(username__iexact=data['username'])
        )
        if user.exists():
            raise UserExistException()
        return data

    def create(self, data):
        user = User.objects.create_user(
            mobile=data['mobile'],
            email=data['email'],
            username=data['username'],
            password=data['password'],
        )
        return user


class LogInByOtpSerializer(VerifyOtpSerializer):
    BLOCKED_STATUS = 3

    def get_user(self, mobile):
        user = User.objects.filter(mobile__iexact=mobile)
        if not user.exists():
            raise IncorrectMobileException()
        self.user = user.first()

    def validate(self, data):
        self.get_user(data['mobile'])
        if self.user.status == self.BLOCKED_STATUS:
            raise BlockedException()
        user_verify_otp(
            mobile=data['mobile'],
            otp=data['otp'],
            set_again_in_redis=False
        )
        return data


class LogInByPasswordSerializer(serializers.Serializer):
    BLOCKED_STATUS = 3

    mobile_or_email_or_username = serializers.CharField(
        required=True,
    )
    password = serializers.CharField(
        required=True,
    )

    def get_user(self, mobile_or_email_or_username):
        user = User.objects.filter(
            Q(mobile=mobile_or_email_or_username) |
            Q(email=mobile_or_email_or_username) |
            Q(username=mobile_or_email_or_username)
        )
        if not user.exists():
            raise IncorrectMobileEmailUsernameException
        self.user = user.first()
        return self

    def authenticate_user(self, password):
        user = authenticate(mobile=self.user.mobile, password=password)
        if user is None:
            raise IncorrectMobileEmailUsernameException()

    def validate(self, data):
        self.get_user(data['mobile_or_email_or_username']).authenticate_user(data['password'])
        if self.user.status == self.BLOCKED_STATUS:
            raise BlockedException()
        return data


class ChangeForgetPasswordSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        required=True,
    )
    otp = serializers.CharField(
        required=True,
    )
    password = serializers.CharField(
        required=True,
    )
    password2 = serializers.CharField(
        required=True,
    )

    def get_user(self, mobile):
        user = User.objects.filter(mobile=mobile)
        if not user.exists():
            raise IncorrectMobileException()
        self.user = user.first()

    def validate(self, data):
        if data['password'] != data['password2']:
            raise NotConfirmedPasswordException()
        user_verify_otp(
            mobile=data['mobile'],
            otp=data['otp'],
            set_again_in_redis=False
        )
        self.get_user(data['mobile'])
        self.password = data['password']
        return data

    def set_password(self):
        self.user.set_password(self.password)
        self.user.save()


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=True,
    )
    new_password = serializers.CharField(
        required=True,
        min_length=5,
    )
    new_password2 = serializers.CharField(
        required=True,
    )

    def check_user_password(self, request, password):
        user = get_user_from_request(request)
        user = authenticate(mobile=user.mobile, password=password)
        if user is None:
            raise IncorrectPasswordException()
        self.user = user

    def validate(self, data):
        self.check_user_password(self.context.get('request'), data['password'])
        if data['new_password'] != data['new_password2']:
            raise NotConfirmedPasswordException()
        self.new_password = data['new_password']
        return data

    def set_password(self):
        self.user.set_password(self.new_password)
        self.user.save()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'slug', 'username', 'first_name', 'last_name', 'avatar']

    avatar = serializers.ImageField(source='profile.avatar')
    url = serializers.HyperlinkedIdentityField(view_name='profile', lookup_field='slug', read_only=True)


class GetProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ['user', 'about_me_status']
        extra_fields = ['first_name', 'last_name', 'about_user', 'notification']

    about_user = serializers.SerializerMethodField('get_about_user')
    notification = serializers.SerializerMethodField('get_notification')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')

    def get_about_user(self, obj):
        if obj.about_me_status == 1:
            return obj.about_me

    def get_logged_user(self):
        return get_user_from_request(self.context['request'])

    def get_fields(self):
        fields = super().get_fields()
        if self.get_logged_user() != self.instance.user:
            [fields.pop(i) for i in list(fields) if i in ['url', 'notification', 'about_me']]
        else:
            [fields.pop(i) for i in list(fields) if i in ['url', 'about_user']]
        return fields


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        required=False,
        min_length=3,
    )
    last_name = serializers.CharField(
        required=False,
        min_length=3,
    )
    gender = serializers.IntegerField(
        required=False,
    )
    birthday = serializers.DateField(
        required=False,
    )
    avatar = serializers.ImageField(
        required=False,
    )
    about_me = serializers.CharField(
        required=False,
        max_length=512,
    )
    twitter_accounts = serializers.URLField(
        required=False,
    )
    telegram_accounts = serializers.URLField(
        required=False,
    )
    instagram_accounts = serializers.URLField(
        required=False,
    )
    website = serializers.URLField(
        required=False,
    )

    def validate(self, data):
        for field in data:
            if field in ['first_name', 'last_name', 'about_me']:
                check_dirty_content(data[field])
        return data

    def update_user(self, user, validated_data):
        if 'first_name' in validated_data:
            user.first_name = validated_data.get('first_name')
        if 'last_name' in validated_data:
            user.last_name = validated_data.get('last_name')
        user.save()

    def update(self, obj, validated_data):
        user = obj.user
        self.update_user(user, validated_data)
        validated_data = {
            field: validated_data[field] for field in validated_data if field not in [
                'first_name', 'last_name'
            ]
        }
        Profile.objects.filter(pk=obj.pk).update(**validated_data)
