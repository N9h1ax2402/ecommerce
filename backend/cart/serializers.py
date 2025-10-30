from rest_framework import serializers
from .models import Cart, CartItem
from catalog.models import Product, Variant
from catalog.serializers import ProductSerializer, VariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True, required=False, allow_null=True)
    variant = VariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(source='variant', queryset=Variant.objects.all(), write_only=True, required=False, allow_null=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        instance = super().update(instance, validated_data)
        for item in items_data:
            CartItem.objects.update_or_create(
                cart=instance,
                product=item.get('product'),
                variant=item.get('variant'),
                defaults={'quantity': item.get('quantity', 1)},
            )
        return instance


