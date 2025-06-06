from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caspinex.shop' # Corrected full Python path to the app
    label = 'shop'         # Explicitly set the app label
