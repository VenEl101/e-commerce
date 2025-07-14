from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, SerializerMethodField
from rest_framework.serializers import Serializer

from app.models.shop import Product, Category, ProductItem, Favorites
from app.models.order import OrderItem, Order, ShippingAddress, CartItem, Cart
from app.models.users import User



class PreRegisterSerializer(Serializer):
    username = CharField()
    email = EmailField()
    password = CharField(write_only=True)


    def validate_password(self, value):
        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return value


class OTPVerifySerializer(Serializer):
    email = EmailField()
    code = CharField(max_length=6)



class UserLoginSerializer(Serializer):
    username_or_email = CharField()
    password = CharField()

    def validate(self, attrs):
        identifier = attrs.get('username_or_email')
        password = attrs.get('password')

        user = User.objects.filter(Q(email=identifier) | Q(username=identifier)).first()

        print(user.check_password(password))

        if not user:
            raise ValidationError("User not found.")

        if not user.check_password(password):
            raise ValidationError("Incorrect password.")

        if not user.is_active:
            raise ValidationError("User is inactive.")

        attrs['user'] = user
        return attrs


class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'description')


class ProductVariantSerializer(serializers.ModelSerializer):

    current_price = SerializerMethodField()

    class Meta:
        model = ProductItem
        fields = ('id', 'sku', 'color', 'size', 'current_price', 'stock_quantity',
                  'is_available')

    def get_current_price(self, obj):
        return obj.current_price


class ProductModelSerializer(serializers.ModelSerializer):

    variants = ProductVariantSerializer(many=True)

    class Meta:
        model = Product
        fields = ('id', 'category', 'name', 'discount', 'seller', 'description', 'variants')







class ProductDetailSerializer(ProductModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(source='has_stock', read_only=True)

    class Meta(ProductModelSerializer.Meta):
        fields = ProductModelSerializer.Meta.fields + (
            'description', 'variants', 'in_stock', 'updated_at'
        )



class CartItemModelSerializer(serializers.ModelSerializer):

    subtotal = SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_item', 'quantity', 'add_at', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal



class CartModelSerializer(serializers.ModelSerializer):

    total = SerializerMethodField()
    items = CartItemModelSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total', 'created_at']


    def get_total(self, obj):
        return obj.total



class ShippingAddressModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShippingAddress
        fields = ['id', 'user', 'recipient_name', 'street', 'city', 'postal_code', 'country', 'phone_number', 'shipping_cost']
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


    def validate_phone_number(self, value):
        if not value.startswith('+998') and len(value) != 9:
            raise ValidationError("Invalid phone number.")
        return value




class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_items', 'quantity', 'subtotal']


    def get_subtotal(self, obj):
        return obj.subtotal




class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    shipping_cost = SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'shipping', 'items', 'promo_code', 'status', 'total_price', 'shipping_cost', 'created_at'
        ]

    def get_shipping_cost(self, obj):
        return obj.shipping_cost


    def get_subtotal(self, obj):
        return obj.subtotal




class FavouritesModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorites
        fields = ['id', 'product', 'created_at']




class UserProfileModelSerializer(serializers.ModelSerializer):


    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_picture', 'first_name', 'last_name']


