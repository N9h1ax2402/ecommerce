from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, CanceledOrderFeedback
from .serializers import OrderSerializer, CanceledOrderFeedbackSerializer
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

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        """
        Customer: cancel their own order.
        Only orders in PACKING or SHIPPING status can be canceled by customers.
        """
        order = self.get_object()
        
        # Check if order belongs to the customer
        if order.user != request.user:
            return Response(
                {'detail': 'You can only cancel your own orders.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if order is already canceled
        if order.status == Order.Status.CANCELED:
            return Response(
                {'detail': 'This order is already canceled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if order can be canceled (only PACKING or SHIPPING)
        if order.status not in [Order.Status.PACKING, Order.Status.SHIPPING]:
            return Response(
                {
                    'detail': f'Orders with status "{order.get_status_display()}" cannot be canceled.',
                    'current_status': order.status,
                    'allowed_statuses': [Order.Status.PACKING, Order.Status.SHIPPING]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the order (stock restoration is handled by the signal)
        order.status = Order.Status.CANCELED
        order.save(update_fields=['status', 'updated_at'])
        
        return Response({
            'id': order.id,
            'status': order.status,
            'message': 'Order has been canceled successfully.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='feedback')
    def submit_feedback(self, request, pk=None):
        """
        Body: { "reason": "Change shipping address|Change size|", "other_description": "optional text" }
        """
        order = self.get_object()
        
        # Check if order belongs to the customer
        if order.user != request.user:
            return Response(
                {'detail': 'You can only submit feedback for your own orders.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if order is canceled
        if order.status != Order.Status.CANCELED:
            return Response(
                {'detail': 'Feedback can only be submitted for canceled orders.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if feedback already exists
        if CanceledOrderFeedback.objects.filter(order=order).exists():
            return Response(
                {'detail': 'Feedback has already been submitted for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create feedback
        serializer = CanceledOrderFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
