from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        # Sử dụng prefetch_related để load items với product và variant
        return Cart.objects.filter(
            user=self.request.user
        ).prefetch_related(
            'items__product',
            'items__variant'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'post'], url_path='me')
    def me(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            return Response(CartSerializer(cart).data)
        serializer = CartSerializer(cart, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Sử dụng select_related để load product và variant, tránh N+1 queries
        return CartItem.objects.filter(
            cart__user=self.request.user
        ).select_related('product', 'variant', 'cart')

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)



