from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework import generics, filters, status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from authentication.models import User, Profile
from .serializers import (
    SendOtpSerializer,
    VerifyOtpSerializer,
    UserSignUpSerializer,
    LogInByOtpSerializer,
    LogInByPasswordSerializer,
    ChangeForgetPasswordSerializer,
    ChangePasswordSerializer,
    UserSerializer,
    GetProfileSerializer,
    UpdateProfileSerializer,
)
from .utils import (
    user_send_otp_code,
    delete_otp_from_redis,
    token_generator,
    get_user_from_request,
)
from .exceptions import PermissionException


@permission_classes((AllowAny,))
@throttle_classes([AnonRateThrottle])
class SendOtpView(APIView):
    def post(self, request, *args, **kwargs):
        has_account = request.query_params.get('has_account')
        serializer = SendOtpSerializer(data=request.data, context={'has_account': has_account})
        serializer.is_valid(raise_exception=True)
        mobile = serializer.validated_data.get('mobile')
        result = user_send_otp_code(mobile=mobile, expiration=60*2)
        if result:
            return Response(
                {'detail': 'otp code has been sent successfully.'},
                status=status.HTTP_201_CREATED
            )


@permission_classes((AllowAny,))
class VerifyOtpView(APIView):
    def post(self, request, *arg, **kwargs):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {'detail': 'otp code verified.'},
            status=status.HTTP_200_OK
        )


@permission_classes((AllowAny,))
@throttle_classes([AnonRateThrottle])
class UserSignUpView(APIView):
    def post(self, request, *arg, **kwargs):
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        delete_otp_from_redis(serializer.validated_data.get('mobile'))
        return Response(
            {'detail': 'user created.'},
            status=status.HTTP_201_CREATED
        )


@permission_classes((AllowAny,))
@throttle_classes([AnonRateThrottle])
class LoginByOtpView(APIView):
    def post(self, request, *arg, **kwargs):
        serializer = LogInByOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_otp_from_redis(serializer.validated_data.get('mobile'))
        return Response(
                {'JWT token': token_generator(serializer.user)},
                status=status.HTTP_200_OK
            )


@permission_classes((AllowAny,))
class LoginByPasswordView(APIView):
    def post(self, request):
        serializer = LogInByPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {'JWT token': token_generator(serializer.user)},
            status=status.HTTP_200_OK
        )


@throttle_classes([AnonRateThrottle])
class ChangeForgetPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChangeForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.set_password()
        delete_otp_from_redis(serializer.validated_data.get('mobile'))
        return Response(
            {'detail': 'password changed successfully.'},
            status=status.HTTP_200_OK
        )


@throttle_classes([AnonRateThrottle])
class ChangePasswordView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.set_password()
        return Response(
            {'detail': 'password changed successfully.'},
            status=status.HTTP_200_OK
        )


class ProfileView(APIView):
    def get(self, request, slug):
        instance = get_object_or_404(Profile, user__slug=slug)
        serializer = GetProfileSerializer(
            instance=instance,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def put(self, request, slug=None):
        instance = get_object_or_404(Profile, user__slug=slug)
        logged_user = get_user_from_request(request)
        if logged_user != instance.user:
            raise PermissionException
        serializer = UpdateProfileSerializer(
            instance=instance,
            data=request.data,
            context={'request': request, 'user': logged_user}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.update(instance, request.data)

        return Response(
            {'detail': 'profile updated.'},
            status=status.HTTP_201_CREATED
        )


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    filterset_fields = [
        'username',
        'first_name',
        'last_name'
    ]

