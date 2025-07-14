from django.contrib import admin

from app.models.users import User
from app.models.shop import Product, ProductItem
from app.models.order import Order, OrderItem, PromoCode, ShippingAddress
# Register your models here.

admin.site.register([User, Product, ProductItem, Order, OrderItem, ShippingAddress, PromoCode])