from rest_framework import serializers
from django.conf import settings
from django.utils.text import slugify
from .models import Category, Product, Variant, Tag
import os


def normalize_filename(name):
    """Normalize product name to match image filename
    Handles variations like: "Basic T-Shirt" -> "Basic-T-Shirt" or "Basic T-Shirt"
    """
    # Try multiple formats to match filename
    # Format 1: Original name (case-insensitive)
    # Format 2: Slug with dashes
    # Format 3: Title case with dashes
    base = name.strip()
    return base


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
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'is_active',
            'category', 'category_id', 'tags', 'tag_ids', 'image_url', 'variants', 'created_at', 'updated_at'
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        
        # Tìm ảnh theo tên với nhiều biến thể
        folder = os.path.join(settings.MEDIA_ROOT, 'products')
        
        if not os.path.exists(folder):
            return None
        
        # Danh sách các biến thể tên file để thử
        name_variants = [
            obj.name,  # Original: "Basic T-Shirt"
            obj.name.replace(' ', '-'),  # "Basic-T-Shirt"
            obj.name.replace(' ', '_'),  # "Basic_T-Shirt"
            slugify(obj.name),  # "basic-t-shirt"
            obj.name.lower(),  # "basic t-shirt"
        ]
        
        extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG']
        
        # Thử từng biến thể tên
        for variant in name_variants:
            for ext in extensions:
                filename = variant + ext
                file_path = os.path.join(folder, filename)
                if os.path.exists(file_path):
                    rel_path = f'products/{filename}'
                    if request:
                        return request.build_absolute_uri(settings.MEDIA_URL + rel_path)
                    else:
                        return settings.MEDIA_URL + rel_path
        
        # Nếu không tìm thấy, thử tìm bất kỳ file nào chứa tên product
        for ext in extensions:
            for filename in os.listdir(folder):
                if filename.lower().endswith(ext.lower()):
                    # Check if filename contains product name words
                    product_words = set(obj.name.lower().split())
                    file_words = set(filename.lower().replace('-', ' ').replace('_', ' ').split())
                    if product_words.intersection(file_words):
                        rel_path = f'products/{filename}'
                        if request:
                            return request.build_absolute_uri(settings.MEDIA_URL + rel_path)
                        else:
                            return settings.MEDIA_URL + rel_path
                        break
        
        return None  # Nếu không có ảnh phù hợp


