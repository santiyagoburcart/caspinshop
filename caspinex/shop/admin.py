from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from .models import CustomUser, UserPaymentMethod, Category, Product, Order, OrderItem

# Actions for CustomUser
@admin.action(description=_('Mark selected users as identity verified'))
def mark_identity_verified(modeladmin, request, queryset):
    queryset.update(is_identity_verified=True)
    modeladmin.message_user(request, _("Selected users marked as identity verified."), messages.SUCCESS)

@admin.action(description=_('Mark selected users as identity NOT verified'))
def mark_identity_not_verified(modeladmin, request, queryset):
    queryset.update(is_identity_verified=False)
    modeladmin.message_user(request, _("Selected users marked as identity NOT verified."), messages.WARNING)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_identity_verified', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_identity_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    actions = [mark_identity_verified, mark_identity_not_verified]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'national_id', 'address', 'postal_code', 'is_identity_verified')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number',
                       'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('last_login', 'date_joined')

@admin.action(description=_('Mark selected payment methods as verified'))
def mark_payment_method_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)
    modeladmin.message_user(request, _("Selected payment methods marked as verified."), messages.SUCCESS)

@admin.action(description=_('Mark selected payment methods as NOT verified'))
def mark_payment_method_not_verified(modeladmin, request, queryset):
    queryset.update(is_verified=False)
    modeladmin.message_user(request, _("Selected payment methods marked as NOT verified."), messages.WARNING)

@admin.register(UserPaymentMethod)
class UserPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'card_holder_name', 'card_number_last_four', 'card_expiry_date', 'is_verified', 'added_at']
    list_filter = ['is_verified', 'user__is_identity_verified']
    search_fields = ['user__email', 'card_holder_name', 'card_number_last_four']
    actions = [mark_payment_method_verified, mark_payment_method_not_verified]
    autocomplete_fields = ['user']
    readonly_fields = ['added_at']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('User Email')
    user_email.admin_order_field = 'user__email'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'id']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    autocomplete_fields = ['parent']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_name', 'price', 'stock', 'available', 'updated_at']
    list_filter = ['available', 'category', 'updated_at']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug', 'category__name']
    autocomplete_fields = ['category']
    date_hierarchy = 'updated_at'
    readonly_fields = ('created_at', 'updated_at')

    def category_name(self, obj):
        if obj.category:
            return obj.category.name
        return "-"
    category_name.short_description = _('Category')
    category_name.admin_order_field = 'category__name'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price_at_order', 'item_total_cost']
    fields = ['product', 'quantity', 'price_at_order', 'item_total_cost']

    def price_at_order(self, obj):
        return obj.price
    price_at_order.short_description = _('Price (at order)')

    def item_total_cost(self, obj):
        return obj.get_cost()
    item_total_cost.short_description = _('Total Cost')

@admin.action(description=_('Mark selected orders as payment verified'))
def mark_order_payment_verified(modeladmin, request, queryset):
    queryset.update(payment_verified=True)
    modeladmin.message_user(request, _("Selected orders marked as payment verified."), messages.SUCCESS)

@admin.action(description=_('Mark selected orders as payment NOT verified'))
def mark_order_payment_not_verified(modeladmin, request, queryset):
    queryset.update(payment_verified=False)
    modeladmin.message_user(request, _("Selected orders marked as payment NOT verified."), messages.WARNING)

@admin.action(description=_('Change status to Processing'))
def change_status_to_processing(modeladmin, request, queryset):
    queryset.update(status=Order.STATUS_PROCESSING)
    modeladmin.message_user(request, _("Selected orders changed status to Processing."), messages.SUCCESS)

@admin.action(description=_('Change status to Shipped'))
def change_status_to_shipped(modeladmin, request, queryset):
    queryset.update(status=Order.STATUS_SHIPPED)
    modeladmin.message_user(request, _("Selected orders changed status to Shipped."), messages.SUCCESS)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email_display', 'status', 'total_paid_display', 'payment_verified', 'created_at']
    list_filter = ['status', 'payment_verified', 'created_at']
    search_fields = ['id', 'user__email', 'transaction_id']
    list_editable = ['status', 'payment_verified']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user']
    actions = [mark_order_payment_verified, mark_order_payment_not_verified, change_status_to_processing, change_status_to_shipped]
    fieldsets = (
        (_('Order Information'), {'fields': ('user', 'status', 'payment_verified', 'transaction_id')}),
        (_('Address Information'), {'fields': ('billing_address', 'shipping_address')}),
        (_('Financials'), {'fields': ('total_paid', 'calculated_total_items')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at', 'calculated_total_items')

    def user_email_display(self, obj):
        return obj.user.email
    user_email_display.short_description = _('User Email')
    user_email_display.admin_order_field = 'user__email'

    def total_paid_display(self, obj):
        return obj.total_paid
    total_paid_display.short_description = _('Total Paid (Recorded)')
    total_paid_display.admin_order_field = 'total_paid'

    def calculated_total_items(self, obj):
        return sum(item.get_cost() for item in obj.items.all())
    calculated_total_items.short_description = _('Calculated Total (from items)')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')

    def changelist_view(self, request, extra_context=None):
        total_revenue_verified = Order.objects.filter(payment_verified=True).aggregate(
            total_revenue=Coalesce(Sum('total_paid'), 0)
        )['total_revenue']

        total_revenue_all = Order.objects.aggregate(
            total_revenue=Coalesce(Sum('total_paid'), 0)
        )['total_revenue']

        verified_orders_count = Order.objects.filter(payment_verified=True).count()
        total_orders_count = Order.objects.count()

        extra_context = extra_context or {}
        extra_context['total_revenue_verified'] = total_revenue_verified
        extra_context['total_revenue_all'] = total_revenue_all
        extra_context['verified_orders_count'] = verified_orders_count
        extra_context['total_orders_count'] = total_orders_count

        return super().changelist_view(request, extra_context=extra_context)
