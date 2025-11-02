from rest_framework import serializers
from django.conf import settings
from django.utils.text import slugify
from .models import Category, Product, Variant, Tag
import os


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']



class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ['id', 'sku', 'color', 'size', 'stock', 'price_override']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ProductSerializer(serializers.ModelSerializer):
    variants = VariantSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=Category.objects.all(), write_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(source='tags', many=True, queryset=Tag.objects.all(), write_only=True, required=False)
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'is_active',
            'category', 'category_id', 'tags', 'tag_ids', 'image_urls', 'variants', 'created_at', 'updated_at'
        ]

    def get_image_urls(self, obj):
        request = self.context.get('request')
        
        # Tìm tất cả ảnh theo tên với nhiều biến thể
        folder = os.path.join(settings.MEDIA_ROOT, 'products')
        
        if not os.path.exists(folder):
            return []
        
        image_urls = []
        found_files = set()  # Để tránh trùng lặp
        
        # Danh sách các biến thể tên file để thử
        name_variants = [
            obj.name,  # Original: "Basic T-Shirt"
            obj.name.replace(' ', '-'),  # "Basic-T-Shirt"
            obj.name.replace(' ', '_'),  # "Basic_T-Shirt"
            slugify(obj.name),  # "basic-t-shirt"
            obj.name.lower(),  # "basic t-shirt"
        ]
        
        extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG']
        
        # Thử từng biến thể tên để tìm exact match
        for variant in name_variants:
            for ext in extensions:
                filename = variant + ext
                if filename in found_files:
                    continue
                    
                file_path = os.path.join(folder, filename)
                if os.path.exists(file_path):
                    rel_path = f'products/{filename}'
                    if request:
                        url = request.build_absolute_uri(settings.MEDIA_URL + rel_path)
                    else:
                        url = settings.MEDIA_URL + rel_path
                    image_urls.append(url)
                    found_files.add(filename)
        
        # Tìm các file có tên chứa product name (partial match)
        product_words = set(obj.name.lower().split())
        for filename in os.listdir(folder):
            if filename in found_files:
                continue
                
            if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                file_words = set(filename.lower().replace('-', ' ').replace('_', ' ').replace('.', ' ').split())
                # Check if filename contains product name words
                if product_words.intersection(file_words):
                    rel_path = f'products/{filename}'
                    if request:
                        url = request.build_absolute_uri(settings.MEDIA_URL + rel_path)
                    else:
                        url = settings.MEDIA_URL + rel_path
                    image_urls.append(url)
                    found_files.add(filename)
        
        return image_urls  # Trả về array, có thể rỗng []


