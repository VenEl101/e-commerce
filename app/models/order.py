from decimal import Decimal

from django.db.models import Model, CharField, TextField, DecimalField, BooleanField, DateTimeField, ForeignKey, \
    PositiveIntegerField, PROTECT, CASCADE, SET_NULL, TextChoices

from app.models.base import TimeBaseModel
from app.models.shop import ProductItem, Product
from app.models.users import User


class PromoCode(Model):
    code = CharField(max_length=20, unique=True)
    discount_present = DecimalField(max_digits=5, decimal_places=2)
    is_active = BooleanField(default=True)
    valid_from = DateTimeField()
    valid_until = DateTimeField()


class ShippingAddress(Model):
    user = ForeignKey(User, on_delete=CASCADE,
                             related_name='addresses')
    recipient_name = CharField(max_length=100)
    street = CharField(max_length=100)
    city = CharField(max_length=50)
    state = CharField(max_length=100)
    postal_code = CharField(max_length=20)
    country = CharField(max_length=50)
    phone_number = CharField(max_length=20)
    is_default = BooleanField(default=False)
    shipping_cost = DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = 'Shipping Addresses'
        ordering = ['-is_default']

    def __str__(self):
        return f"{self.recipient_name}, {self.city}"



class Cart(TimeBaseModel):

    user = ForeignKey(User, on_delete=CASCADE)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"{self.user.username}, {self.user.id}"


    class Meta:
        ordering = ['-created_at']



class CartItem(Model):
    cart = ForeignKey(Cart, on_delete=CASCADE, related_name='items')
    product_item = ForeignKey(ProductItem, on_delete=CASCADE)
    quantity = PositiveIntegerField()
    add_at = DateTimeField(auto_now_add=True)

    @property
    def subtotal(self):
        return self.quantity * self.product_item.current_price


    class Meta:
        verbose_name_plural = 'Cart'


    def __str__(self):
        return f"{self.cart.user.username}, {self.cart.id}"



class Order(TimeBaseModel):

    class Status(TextChoices):
        PENDING = 'PENDING', 'pending'
        ACCEPTED = 'ACCEPTED', 'accepted'
        REJECTED = 'REJECTED', 'rejected'
        DELIVERED = 'DELIVERED', 'delivered'


    user = ForeignKey(User, on_delete=CASCADE)
    shipping = ForeignKey('ShippingAddress', on_delete=PROTECT, related_name='shipping_address')
    promo_code = ForeignKey('PromoCode', on_delete=SET_NULL, null=True, blank=True)
    status = CharField(max_length=25, choices=Status, default='PENDING', blank=True, null=True)


    @property
    def shipping_cost(self):
        return self.shipping.shipping_cost

    @property
    def total_price(self):
        items_total = sum(Decimal(item.subtotal) for item in self.items.all())
        return items_total + self.shipping.shipping_cost


    def __str__(self):
        return f"Order #{self.id}"




class OrderItem(Model):
    order = ForeignKey(Order, on_delete=CASCADE, related_name='items')
    product_items = ForeignKey(ProductItem, on_delete=PROTECT)
    quantity = PositiveIntegerField(default=1)


    @property
    def subtotal(self):
        return self.quantity * self.product_items.current_price


    def __str__(self):
        return f"{self.quantity} × {self.product_items.product.name}"