from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from users.permissions import IsAdminOrStaff


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Staff/Admin can see all orders; customers see only their own
        user = self.request.user
        if user.is_authenticated and getattr(user, 'is_staff_user', False):
            return Order.objects.all().order_by('-created_at')
        return Order.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='status', permission_classes=[IsAdminOrStaff])
    def update_status(self, request, pk=None):
        """
        Staff/Admin: update order status.
        Body: { "status": "Packing|Shipping|Evaluate|Canceled" }
        """
        order = self.get_object()
        new_status = request.data.get('status')
        valid_values = [choice for choice, _ in Order.Status.choices]
        if not new_status or new_status not in valid_values:
            return Response({
                'detail': 'Invalid status',
                'allowed': valid_values
            }, status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        return Response({'id': order.id, 'status': order.status}, status=status.HTTP_200_OK)


# Create your views here.
