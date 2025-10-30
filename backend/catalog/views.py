from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from .models import Category, Product, Tag
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']


class ProductFilter(FilterSet):
    category_name = CharFilter(field_name='category__name', method='filter_category_names')
    tag_names = CharFilter(field_name='tags__name', method='filter_tag_names')

    def filter_category_names(self, queryset, name, value):
        # Accept comma-separated list of names, e.g. ?category_name=Áo,Quần
        names = [v.strip() for v in value.split(',') if v.strip()]
        if names:
            return queryset.filter(category__name__in=names)
        return queryset

    def filter_tag_names(self, queryset, name, value):
        # e.g. ?tag_names=casual,streetwear
        names = [v.strip() for v in value.split(',') if v.strip()]
        if names:
            return queryset.filter(tags__name__in=names).distinct()
        return queryset

    class Meta:
        model = Product
        fields = ['category_name', 'tag_names']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


# Create your views here.
