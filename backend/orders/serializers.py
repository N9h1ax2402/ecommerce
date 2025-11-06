from rest_framework import serializers
from django.db import transaction
from .models import Order, OrderItem, CanceledOrderFeedback, OrderRating


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "variant", "product_name", "unit_price", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    feedback = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total_amount",
            "shipping_full_name",
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
            "items",
            "feedback",
            "rating",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "status", "total_amount"]

    def get_feedback(self, obj):
        """Return feedback if it exists for this order"""
        try:
            feedback = obj.canceled_feedback
            return CanceledOrderFeedbackSerializer(feedback).data
        except CanceledOrderFeedback.DoesNotExist:
            return None

    def get_rating(self, obj):
        try:
            rating = obj.rating
            return OrderRatingSerializer(rating).data
        except OrderRating.DoesNotExist:
            return None

    def validate_items(self, items_data):
        for item_data in items_data:
            variant = item_data.get("variant")
            quantity = item_data.get("quantity", 1)

            if variant:
                if variant.stock < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {variant}. Currently stock: {variant.stock}, requested: {quantity}"
                    )
        return items_data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        total = 0

        for item in items_data:
            quantity = item.get("quantity", 1)
            unit_price = item["unit_price"]
            total += unit_price * quantity

            # Tạo OrderItem
            OrderItem.objects.create(order=order, **item)

        order.total_amount = total
        order.save(update_fields=["total_amount"])
        return order


class CanceledOrderFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanceledOrderFeedback
        fields = ["id", "order", "reason", "other_description", "created_at"]
        read_only_fields = ["id", "order", "created_at"]


class OrderRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRating
        fields = ["id", "order", "score", "comment", "created_at"]
        read_only_fields = ["id", "order", "created_at"]
