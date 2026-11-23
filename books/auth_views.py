from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def user_payload(user):
    if not user.is_authenticated:
        return {"is_authenticated": False}
    return {
        "is_authenticated": True,
        "id": user.id,
        "username": user.username,
        "is_superuser": user.is_superuser,
        "is_staff": user.is_staff,
    }


class MeView(APIView):
    """Current user. Also makes sure the browser receives the csrftoken cookie."""

    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)  # sets the csrftoken cookie
        return Response(user_payload(request.user))


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username", ""),
            password=request.data.get("password", ""),
        )
        if user is None:
            return Response({"detail": "Invalid username or password."},
                            status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(user_payload(user))


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        if not username or not password:
            return Response({"detail": "Username and password are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "This username is already taken."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({"detail": " ".join(e.messages)},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return Response(user_payload(user), status=status.HTTP_201_CREATED)
