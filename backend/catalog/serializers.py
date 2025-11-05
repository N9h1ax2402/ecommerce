from typing import Any
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
    image_urls = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(source='product', queryset=Product.objects.all(), write_only=True, required=True)
    class Meta:
        model = Variant
        fields = ['id', 'sku', 'color', 'size', 'stock', 'price_override', 'image_urls', 'product_id']

    def get_image_urls(self, obj):
        request = self.context.get('request')
        folder = os.path.join(settings.MEDIA_ROOT, 'products')

        if not os.path.exists(folder):
            return []

        image_urls = []
        found_files = set()

        extensions = ['.jpg', '.jpeg', '.png', '.webp']
        index_suffixes = ['', '-1', '-2', '-3', '-4', '-5', '-6']

        if not obj.sku:
            return []

        sku_base = obj.sku.rsplit('-', 1)[0] if '-' in obj.sku else obj.sku
        # Try both full SKU and color-level base to support existing files like P1-BLACK-M-1.jpg
        base_names = [
            sku_base

        ]
        seen = set()
        ordered_bases = []
        for b in base_names:
            if b not in seen:
                seen.add(b)
                ordered_bases.append(b)

        for base in ordered_bases:
            for suffix in index_suffixes:
                for ext in extensions:
                    filename = f"{base}{suffix}{ext}"
                    if filename in found_files:
                        continue
                    file_path = os.path.join(folder, filename)
                    if os.path.exists(file_path):
                        rel_path = f'products/{filename}'
                        url = request.build_absolute_uri(settings.MEDIA_URL + rel_path) if request else settings.MEDIA_URL + rel_path
                        image_urls.append(url)
                        found_files.add(filename)

        

        return image_urls


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
    # Removed product-level image_urls; now provided on each variant

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'is_active',
            'category', 'category_id', 'tags', 'tag_ids', 'variants', 'created_at', 'updated_at'
        ]



