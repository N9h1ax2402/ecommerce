from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, F, Sum
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from .models import Category, Product, Tag, Variant
from .serializers import CategorySerializer, ProductSerializer, VariantSerializer, ProductSalesSerializer
from users.permissions import IsAdminOrStaff


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
    
    def get_queryset(self):
        """
        - Public users see only active products
        - Staff/Admin can see all products (including inactive) for management
        """
        base_qs = Product.objects.all().order_by('-created_at')
        request = getattr(self, 'request', None)
        if request and request.user and request.user.is_authenticated and getattr(request.user, 'is_staff_user', False):
            return base_qs
        return base_qs.filter(is_active=True)

    def get_permissions(self):
        # Read-only for everyone; write actions require admin or staff
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsAdminOrStaff()]
    
    @action(detail=True, methods=['get'], url_path='recommend')
    def recommend(self, request, pk=None):
        """
        Rule-based product recommendation based on tags, category, and price
        GET /api/products/{id}/recommend/?limit=5
        """
        try:
            product = self.get_object()
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        limit = int(request.query_params.get('limit', 5))
        
        # Get recommendations using rule-based logic
        recommended_products = self._get_recommendations(product, limit)
        
        serializer = self.get_serializer(recommended_products, many=True)
        return Response({
            'product': ProductSerializer(product).data,
            'recommendations': serializer.data,
            'count': len(recommended_products)
        })
    
    def _get_recommendations(self, product, limit=5):
        """
        Rule-based recommendation algorithm:
        1. Same tags (highest priority) - weight: 10 points per matching tag
        2. Same category - weight: 5 points
        3. Similar price range (±20%) - weight: 3 points
        4. Exclude the current product
        """
        from django.db.models import Case, When, IntegerField, FloatField
        
        # Base queryset: active products excluding current
        queryset = Product.objects.filter(is_active=True).exclude(id=product.id)
        
        # Calculate price range (±20%)
        price_lower = float(product.price) * 0.8
        price_upper = float(product.price) * 1.2
        
        # Get product tags
        product_tags = product.tags.all()
        product_tag_ids = list(product_tags.values_list('id', flat=True))
        
        # Annotate with recommendation score
        queryset = queryset.annotate(
            # Score for matching tags (10 points per tag)
            matching_tags_count=Count('tags', filter=Q(tags__id__in=product_tag_ids)),
            tag_score=F('matching_tags_count') * 10,
            
            # Score for same category (5 points if same)
            category_score=Case(
                When(category=product.category, then=5),
                default=0,
                output_field=IntegerField()
            ),
            
            # Score for similar price (3 points if in range)
            price_score=Case(
                When(price__gte=price_lower, price__lte=price_upper, then=3),
                default=0,
                output_field=IntegerField()
            ),
        ).annotate(
            total_score=F('tag_score') + F('category_score') + F('price_score')
        ).filter(
            total_score__gt=0  # Only products with some match
        ).order_by('-total_score', '-created_at')[:limit]
        
        return list(queryset)

    @action(detail=False, methods=['get'], url_path='sales-stats', permission_classes=[IsAdminOrStaff])
    def list_by_sold(self, request):
        """
        Admin/Staff: list products ordered by sold desc
        GET /api/products/sales-stats/
        """
        products = Product.objects.all().order_by('-sold', '-updated_at')
        serializer = ProductSalesSerializer(products, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


# Create your views here.


class VariantViewSet(viewsets.ModelViewSet):
    queryset = Variant.objects.select_related('product').all()
    serializer_class = VariantSerializer
    permission_classes = [IsAdminOrStaff]

    def get_permissions(self):
        # All actions require staff/admin; no public access to variant CRUD
        return [IsAdminOrStaff()]
        