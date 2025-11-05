from django.db import models, transaction
from django.conf import settings
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from catalog.models import Product, Variant


class Order(models.Model):
    class Status(models.TextChoices):
        PACKING = 'packing', 'Packing'
        SHIPPING = 'shipping', 'Shipping'
        EVALUATE = 'evaluate', 'Evaluate'
        CANCELED = 'canceled', 'Canceled'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PACKING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_full_name = models.CharField(max_length=255)
    shipping_address = models.CharField(max_length=500)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order #{self.id} - {self.user}"

    def restore_stock_and_sold(self):
        for item in self.items.all():
            variant = item.variant
            product = item.product
            quantity = item.quantity
            
            if variant:
                # Hoàn trả stock variant
                variant.stock += quantity
                variant.save(update_fields=['stock'])
                # Giảm sold của product
                if variant.product:
                    variant.product.sold = max(0, variant.product.sold - quantity)
                    variant.product.save(update_fields=['sold'])
            elif product:
                # Giảm sold của product
                product.sold = max(0, product.sold - quantity)
                product.save(update_fields=['sold'])


@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """Xử lý khi order status thay đổi thành CANCELED"""
    if instance.pk:  # Chỉ xử lý khi order đã tồn tại (update)
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            # Nếu status chuyển từ không phải CANCELED sang CANCELED
            if old_instance.status != Order.Status.CANCELED and instance.status == Order.Status.CANCELED:
                old_instance.restore_stock_and_sold()
        except Order.DoesNotExist:
            pass


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    variant = models.ForeignKey(Variant, null=True, blank=True, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def line_total(self) -> float:
        return self.quantity * self.unit_price

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"


@receiver(pre_save, sender=OrderItem)
def order_item_capture_old_quantity(sender, instance: 'OrderItem', **kwargs):
    """Capture old quantity before save to compute delta in post_save."""
    if instance.pk:
        try:
            old = OrderItem.objects.get(pk=instance.pk)
            instance._old_quantity = old.quantity
        except OrderItem.DoesNotExist:
            instance._old_quantity = 0
    else:
        instance._old_quantity = 0


@receiver(post_save, sender=OrderItem)
def order_item_adjust_on_save(sender, instance: 'OrderItem', created: bool, **kwargs):
    old_qty = getattr(instance, '_old_quantity', 0) or 0
    delta = instance.quantity - old_qty
    if delta == 0:
        return
    with transaction.atomic():
        if instance.variant:
            variant = instance.variant
            product = variant.product
            variant.stock = max(0, variant.stock - delta)
            variant.save(update_fields=['stock'])
            if product:
                product.sold = max(0, product.sold + delta)
                product.save(update_fields=['sold'])
        elif instance.product:
            product = instance.product
            product.sold = max(0, product.sold + delta)
            product.save(update_fields=['sold'])


@receiver(post_delete, sender=OrderItem)
def order_item_restore_on_delete(sender, instance: 'OrderItem', **kwargs):
    """Restore stock and sold when an order item is removed."""
    qty = instance.quantity
    if qty <= 0:
        return
    if instance.variant:
        variant = instance.variant
        product = variant.product
        variant.stock = variant.stock + qty
        variant.save(update_fields=['stock'])
        if product:
            product.sold = max(0, product.sold - qty)
            product.save(update_fields=['sold'])
    elif instance.product:
        product = instance.product
        product.sold = max(0, product.sold - qty)
        product.save(update_fields=['sold'])


# Create your models here.
