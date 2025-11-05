from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models
from .serializers import RegisterSerializer, UserSerializer
<<<<<<< HEAD
from .permissions import IsAdmin, IsAdminOrStaff
=======
from rest_framework.permissions import BasePermission, IsAuthenticated
>>>>>>> 1438460a8559713023f1ef16c9a300149f6b3ab9

User = get_user_model()


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Register a new user
    POST /api/users/register/
    Body: {
        "username": "user123",
        "email": "user@example.com",
        "password": "password123",
        "password_confirm": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "message": "User registered successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    Login user and return JWT tokens
    POST /api/users/login/
    Body: {
        "username": "user123",
        "password": "password123"
    }
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"error": "User account is disabled"}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "message": "Login successful",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """
    Get current user profile
    GET /api/users/profile/
    Requires: Authorization: Bearer <token>
    """
    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


<<<<<<< HEAD
@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_list_users(request):
    """
    Admin: List users
    GET /api/admin/users/
    Optional query params:
      - search: filter by username or email (icontains)
    """
    search = request.query_params.get('search', '').strip()
    qs = User.objects.all().order_by('-id')
    if search:
        qs = qs.filter(models.Q(username__icontains=search) | models.Q(email__icontains=search))

    data = UserSerializer(qs, many=True).data
    return Response(data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAdmin])
def admin_update_user(request, pk):
    """
    Admin: Update user
    PATCH /api/admin/users/<pk>/
    Body: {
        "username": "user123",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "STAFF"
    }
    """
    user = User.objects.get(pk=pk)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAdminOrStaff])
def staff_modify_product(request):
    """
    Staff: Modify product
    POST /api/staff/products/
    Body: {
        "product_id": 1,
        "action": "approve"
    }
    """
    
=======
class IsAdminUserRole(BasePermission):
    """
    Custom permission: only role ADMIN or is_superuser
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (getattr(request.user, "role", None) == "ADMIN" or request.user.is_superuser)
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only endpoint to view list of users
    GET /api/users/
    """

    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]
>>>>>>> 1438460a8559713023f1ef16c9a300149f6b3ab9
