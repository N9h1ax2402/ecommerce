from django.contrib import admin
from django import forms
from django.conf import settings
from .models import Category, Product, Variant
import os


class ProductImageForm(forms.ModelForm):
    """Form với field upload ảnh"""
    product_image = forms.ImageField(
        required=False,
        label='Product Image',
        help_text='Upload image sẽ được lưu vào media/products/ với tên theo product name'
    )
    
    class Meta:
        model = Product
        fields = '__all__'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    prepopulated_fields = {"slug": ("name",)}


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductImageForm
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VariantInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'tags')
        }),
        ('Pricing', {
            'fields': ('price', 'is_active')
        }),
        ('Image Upload', {
            'fields': ('product_image',),
            'description': 'Upload ảnh cho product. Ảnh sẽ được lưu vào media/products/ với tên theo product name.'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save để xử lý upload ảnh"""
        # Save product trước để có ID nếu là product mới
        super().save_model(request, obj, form, change)
        
        # Xử lý upload ảnh nếu có
        if 'product_image' in form.cleaned_data and form.cleaned_data['product_image']:
            uploaded_file = form.cleaned_data['product_image']
            
            # Tạo tên file theo product name
            product_name = obj.name
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            # Đảm bảo thư mục products tồn tại
            products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
            os.makedirs(products_dir, exist_ok=True)
            
            # Tên file: sử dụng product name, nếu trùng thì thêm số hoặc timestamp
            base_filename = product_name + file_ext
            filename = base_filename
            counter = 1
            while os.path.exists(os.path.join(products_dir, filename)):
                # Nếu đã có file, thêm số vào để có thể upload nhiều ảnh cho cùng 1 product
                filename = f"{product_name} ({counter}){file_ext}"
                counter += 1
            
            # Lưu file
            file_path = os.path.join(products_dir, filename)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Optional: Log success message
            self.message_user(request, f'Image uploaded successfully: {filename}')


# Register your models here.
