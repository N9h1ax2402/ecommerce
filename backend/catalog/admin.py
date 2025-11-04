from django.contrib import admin
from django import forms
from django.conf import settings
from .models import Category, Product, Variant
import os


class VariantInlineForm(forms.ModelForm):
    variant_image = forms.ImageField(
        required=False,
        label='Variant Image',
        help_text='Ảnh sẽ lưu tại media/products/ với tên theo SKU của variant'
    )

    class Meta:
        model = Variant
        fields = ['sku', 'color', 'size', 'stock', 'price_override']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    prepopulated_fields = {"slug": ("name",)}


class VariantInline(admin.TabularInline):
    model = Variant
    form = VariantInlineForm
    extra = 1
    fields = ('sku', 'color', 'size', 'stock', 'price_override', 'variant_image')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'total_stock', 'sold', 'is_active')
    list_filter = ('category', 'is_active')
    readonly_fields = ('sold', 'total_stock')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VariantInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_stock', 'sold',),
            'description': 'Thống kê tổng stock và số lượng sản phẩm đã bán'
        }),
    )
    def save_formset(self, request, form, formset, change):
        response = super().save_formset(request, form, formset, change)
        # Handle variant image uploads: save as media/products/<SKU>.<ext>
        if isinstance(formset.model, type) and issubclass(formset.model, Variant) or formset.model is Variant:
            for inline_form in formset.forms:
                if not inline_form.is_valid():
                    continue
                cleaned = getattr(inline_form, 'cleaned_data', None)
                if not cleaned or cleaned.get('DELETE'):
                    continue
                sku = cleaned.get('sku') or getattr(inline_form.instance, 'sku', None)
                uploaded = cleaned.get('variant_image')
                if sku and uploaded:
                    file_ext = os.path.splitext(uploaded.name)[1].lower()

                    sku_base = sku.rsplit('-', 1)[0] if '-' in sku else sku
                    products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                    os.makedirs(products_dir, exist_ok=True)

                    filename = f"{sku_base}{file_ext}"
                    file_path = os.path.join(products_dir, filename)
                    if os.path.exists(file_path):
                        index = 1
                        while True:
                            candidate = f"{sku_base}-{index}{file_ext}"
                            candidate_path = os.path.join(products_dir, candidate)
                            if not os.path.exists(candidate_path):
                                filename = candidate
                                file_path = candidate_path
                                break
                            index += 1
                    with open(file_path, 'wb+') as destination:
                        for chunk in uploaded.chunks():
                            destination.write(chunk)
                    self.message_user(request, f'Uploaded image for SKU base {sku_base}: {filename}')
        return response


# Register your models here.
