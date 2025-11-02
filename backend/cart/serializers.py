from rest_framework import serializers
from .models import Cart, CartItem
from catalog.models import Product, Variant
from catalog.serializers import ProductSerializer, VariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho CartItem
    
    Payload format khi tạo mới:
    - Nếu có variant:
      {
        "variant_id": 1,  # ID của variant
        "quantity": 2
      }
      (product sẽ tự động được lấy từ variant.product)
    
    - Nếu chỉ có product (không có variant):
      {
        "product_id": 1,  # ID của product
        "quantity": 2
      }
    
    - Có thể gửi cả product_id và variant_id:
      {
        "product_id": 1,
        "variant_id": 1,
        "quantity": 2
      }
      (nếu có variant, product sẽ được lấy từ variant.product)
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True, required=False, allow_null=True)
    variant = VariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(source='variant', queryset=Variant.objects.all(), write_only=True, required=False, allow_null=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'variant', 'variant_id', 'quantity']
    
    def to_representation(self, instance):
        """Override để đảm bảo product/variant được serialize đúng"""
        data = super().to_representation(instance)
        # Kiểm tra nếu product hoặc variant là None nhưng instance có giá trị
        if not data.get('product') and instance.product:
            data['product'] = ProductSerializer(instance.product).data
        if not data.get('variant') and instance.variant:
            data['variant'] = VariantSerializer(instance.variant).data
        return data

    def validate(self, data):
        """Kiểm tra validation khi thêm/update cart item"""
        product = data.get('product')
        variant = data.get('variant')
        quantity = data.get('quantity', 1)
        
        # Nếu có variant nhưng chưa có product, lấy product từ variant
        if variant and not product:
            data['product'] = variant.product
        
        # Phải có ít nhất product hoặc variant
        if not product and not variant:
            raise serializers.ValidationError("Phải có ít nhất product hoặc variant")
        
        # Kiểm tra quantity > 0
        if quantity <= 0:
            raise serializers.ValidationError("Quantity phải lớn hơn 0")
        
        # Nếu có variant, kiểm tra stock
        if variant:
            # Kiểm tra stock cơ bản
            if variant.stock < quantity:
                raise serializers.ValidationError(
                    f"Không đủ stock cho variant {variant}. Stock hiện tại: {variant.stock}, yêu cầu: {quantity}"
                )
        
        return data

    def create(self, validated_data):
        """Override create để xử lý khi thêm mới cart item"""
        cart = validated_data.get('cart')
        variant = validated_data.get('variant')
        product = validated_data.get('product')
        quantity = validated_data.get('quantity', 1)
        
        # Đảm bảo product được set từ variant nếu có variant
        if variant and not product:
            product = variant.product
            validated_data['product'] = product
        
        if cart:
            # Tìm cart item hiện có với cùng product/variant (theo UniqueConstraint: cart, product, variant)
            lookup = {'cart': cart}
            if variant:
                lookup['variant'] = variant
                lookup['product'] = product  # product từ variant
            else:
                lookup['product'] = product
                lookup['variant'] = None
            
            try:
                existing_item = CartItem.objects.select_related('product', 'variant').get(**lookup)
                # Đảm bảo product được set nếu có variant nhưng product chưa có
                if variant and not existing_item.product:
                    existing_item.product = variant.product
                # Nếu đã có, cộng thêm quantity
                if variant:
                    total_quantity = existing_item.quantity + quantity
                    if variant.stock < total_quantity:
                        raise serializers.ValidationError(
                            f"Không đủ stock. Trong cart đã có {existing_item.quantity} sản phẩm, "
                            f"thêm {quantity} sẽ vượt quá stock hiện tại ({variant.stock})"
                        )
                # Update quantity và product nếu cần
                existing_item.quantity += quantity
                existing_item.save()
                # Refresh từ DB để đảm bảo có đầy đủ data
                existing_item.refresh_from_db()
                return existing_item
            except CartItem.DoesNotExist:
                # Chưa có, đã kiểm tra stock trong validate()
                pass
        
        # Đảm bảo product được set trong validated_data trước khi tạo
        if not validated_data.get('product') and variant:
            validated_data['product'] = variant.product
        
        # Tạo cart item mới
        cart_item = super().create(validated_data)
        # Refresh từ DB để đảm bảo có đầy đủ data
        cart_item.refresh_from_db()
        return cart_item

    def update(self, instance, validated_data):
        """Override update để xử lý khi update cart item"""
        variant = validated_data.get('variant', instance.variant)
        quantity = validated_data.get('quantity', instance.quantity)
        
        # Kiểm tra stock tổng trong cart
        if variant:
            # Tính tổng quantity của variant này trong cart
            existing_items = CartItem.objects.filter(cart=instance.cart, variant=variant).exclude(pk=instance.pk)
            total_quantity = sum(item.quantity for item in existing_items) + quantity
            
            if variant.stock < total_quantity:
                raise serializers.ValidationError(
                    f"Không đủ stock. Trong cart đã có {sum(item.quantity for item in existing_items)} sản phẩm, "
                    f"cập nhật thành {quantity} sẽ vượt quá stock hiện tại ({variant.stock})"
                )
        
        return super().update(instance, validated_data)


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer cho Cart
    
    Payload format khi update cart (POST /api/cart/me/):
    {
      "items": [
        {
          "variant_id": 1,  # hoặc "product_id": 1 nếu không có variant
          "quantity": 2
        },
        {
          "variant_id": 2,
          "quantity": 1
        }
      ]
    }
    """
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user']

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        instance = super().update(instance, validated_data)
        
        # Xử lý từng item trong cart
        for item_data in items_data:
            # Lấy product và variant từ item_data
            product = item_data.get('product')
            variant = item_data.get('variant')
            quantity = item_data.get('quantity', 1)
            
            # Đảm bảo product được set từ variant nếu có variant
            if variant and not product:
                product = variant.product
            
            # Tìm hoặc tạo cart item
            CartItem.objects.update_or_create(
                cart=instance,
                variant=variant if variant else None,
                product=product if not variant else product,  # product từ variant
                defaults={'quantity': quantity},
            )
        return instance


