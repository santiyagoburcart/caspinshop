from django.core.management.base import BaseCommand
from django.utils.text import slugify
from caspinex.shop.models import Category, Product # Corrected import path
import decimal

class Command(BaseCommand):
    help = 'Populates the database with sample categories and products for testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Deleting existing Category and Product data...'))
        Product.objects.all().delete()
        Category.objects.all().delete() # Delete in reverse order of dependency if ForeignKeys have PROTECT
                                        # Here, Product depends on Category, so Category should be deleted after Product.
                                        # Or, if Product.category is SET_NULL, order doesn't matter as much for deletion.
                                        # Let's ensure Product is deleted first.
        # Correct order:
        # Product.objects.all().delete()
        # Category.objects.all().delete() -> This is fine as Product.category is on_delete=models.SET_NULL for some, PROTECT for OrderItem.
        # For sample data, simple deletion is okay. If SET_NULL, category field becomes null.
        # If PROTECT, and a product was linked, it would fail. But these are fresh products.

        self.stdout.write(self.style.SUCCESS('Starting to populate sample data...'))

        # Create Categories
        cat_electronics, _ = Category.objects.get_or_create(
            name='لوازم الکترونیکی',
            defaults={'slug': slugify('لوازم الکترونیکی', allow_unicode=True), 'description': 'انواع لوازم الکترونیکی مصرفی'}
        )
        cat_laptops, _ = Category.objects.get_or_create(
            name='لپ تاپ',
            defaults={'slug': slugify('لپ تاپ', allow_unicode=True), 'parent': cat_electronics, 'description': 'انواع لپ تاپ های جدید'}
        )
        cat_mobiles, _ = Category.objects.get_or_create(
            name='گوشی موبایل',
            defaults={'slug': slugify('گوشی موبایل', allow_unicode=True), 'parent': cat_electronics, 'description': 'انواع گوشی های هوشمند'}
        )
        cat_books, _ = Category.objects.get_or_create(
            name='کتاب',
            defaults={'slug': slugify('کتاب', allow_unicode=True), 'description': 'کتاب های آموزشی و داستانی'}
        )
        cat_programming_books, _ = Category.objects.get_or_create(
            name='کتاب برنامه نویسی',
            defaults={'slug': slugify('کتاب برنامه نویسی', allow_unicode=True), 'parent': cat_books, 'description': 'کتاب های آموزش برنامه نویسی'}
        )

        self.stdout.write(self.style.SUCCESS(f'Categories processed. Total categories: {Category.objects.count()}'))

        # Create Products
        Product.objects.get_or_create(
            name='لپ تاپ مدل ایکس ۲۰۰', # Use name as the primary lookup for get_or_create
            category=cat_laptops,      # Pass category directly
            defaults={
                'slug': slugify('لپ تاپ مدل ایکس ۲۰۰', allow_unicode=True),
                'description': 'یک لپ تاپ قدرتمند برای کارهای حرفه ای.',
                'price': decimal.Decimal('35000000.00'),
                'stock': 15,
                'available': True,
                'features': {'ram': '16GB', 'ssd': '512GB', 'cpu': 'Core i7'}
            }
        )
        Product.objects.get_or_create(
            name='لپ تاپ گیمینگ زد ۵۰',
            category=cat_laptops,
            defaults={
                'slug': slugify('لپ تاپ گیمینگ زد ۵۰', allow_unicode=True),
                'description': 'لپ تاپ مخصوص بازی با گرافیک بالا.',
                'price': decimal.Decimal('55000000.00'),
                'stock': 8,
                'available': True,
                'features': {'ram': '32GB', 'ssd': '1TB', 'gpu': 'RTX 4070'}
            }
        )
        Product.objects.get_or_create(
            name='گوشی هوشمند گلکسی اس ۲۵',
            category=cat_mobiles,
            defaults={
                'slug': slugify('گوشی هوشمند گلکسی اس ۲۵', allow_unicode=True),
                'description': 'جدیدترین پرچمدار سامسونگ با دوربین فوق العاده.',
                'price': decimal.Decimal('42000000.00'),
                'stock': 25,
                'available': True,
                'features': {'camera': '200MP', 'storage': '256GB', 'display': 'AMOLED 2X'}
            }
        )
        Product.objects.get_or_create(
            name='گوشی میان رده آلفا ۱۰',
            category=cat_mobiles,
            defaults={
                'slug': slugify('گوشی میان رده آلفا ۱۰', allow_unicode=True),
                'description': 'گوشی اقتصادی با امکانات خوب.',
                'price': decimal.Decimal('8500000.00'),
                'stock': 0, # Unavailable
                'available': False,
                'features': {'camera': '48MP', 'storage': '128GB'}
            }
        )
        Product.objects.get_or_create(
            name='کتاب آموزش پایتون جامع',
            category=cat_programming_books,
            defaults={
                'slug': slugify('کتاب آموزش پایتون جامع', allow_unicode=True),
                'description': 'مرجع کامل یادگیری زبان برنامه نویسی پایتون.',
                'price': decimal.Decimal('350000.00'),
                'stock': 50,
                'available': True,
                'features': {'pages': 700, 'level': 'beginner to advanced'}
            }
        )
        Product.objects.get_or_create(
            name='کتاب کلین کد',
            category=cat_programming_books,
            defaults={
                'slug': slugify('کتاب کلین کد', allow_unicode=True),
                'description': 'راهنمایی برای نوشتن کد تمیز و قابل نگهداری.',
                'price': decimal.Decimal('280000.00'),
                'stock': 30,
                'available': True,
                'features': {'author': 'Robert C. Martin', 'language': 'Software Engineering Principles'}
            }
        )
        Product.objects.get_or_create(
            name='داستان شازده کوچولو',
            category=cat_books,
            defaults={
                'slug': slugify('داستان شازده کوچولو', allow_unicode=True),
                'description': 'یک داستان کلاسیک و دوست داشتنی.',
                'price': decimal.Decimal('150000.00'),
                'stock': 5, # Low stock
                'available': True,
                'features': {'author': 'Antoine de Saint-Exupéry'}
            }
        )

        self.stdout.write(self.style.SUCCESS(f'Products processed. Total products: {Product.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('Sample data population complete.'))
