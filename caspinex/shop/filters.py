import django_filters
from .models import Product, Category # Category might not be directly used here but good for context

class ProductFilter(django_filters.FilterSet):
    # Filter by product name, case-insensitive containment search
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains', label='Product Name')

    # Filter by category slug for more user-friendly URLs
    category_slug = django_filters.CharFilter(field_name='category__slug', lookup_expr='iexact', label='Category Slug')

    # Allow filtering by category name as well (case-insensitive containment)
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains', label='Category Name')

    # Filter for price range
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Minimum Price')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Maximum Price')

    # Filter by availability (True/False)
    available = django_filters.BooleanFilter(field_name='available', label='Is Available?')

    # Ordering Filter
    ordering = django_filters.OrderingFilter(
        fields=(
            ('price', 'price'),
            ('name', 'name'),
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
        ),
        label='Sort by'
    )

    class Meta:
        model = Product
        # The 'fields' in Meta is primarily for DRF's automatic filter generation if you don't define them
        # explicitly as class attributes. Since we've defined them explicitly, this list here mainly serves
        # to make them visible in DRF's browsable API filter controls.
        # It's good practice to list the filter names (keys of the attributes defined above).
        fields = [
            'name',
            'category_slug',
            'category_name',
            'min_price',
            'max_price',
            'available',
            # 'ordering' is not a model field, so it's not typically listed here.
            # DRF will pick up OrderingFilter automatically if it's a class attribute.
        ]
        # For fields where you want exact matches and haven't defined a custom filter, you can use:
        # fields = {'name': ['exact', 'icontains'], 'category__id': ['exact']}
