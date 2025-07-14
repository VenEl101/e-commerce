from django.core.cache import cache
from django.db import transaction

from rest_framework.exceptions import PermissionDenied, NotFound

from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView, ListCreateAPIView, \
    GenericAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView, get_object_or_404

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from app.tasks import send_otp_email

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app.models.order import Order, Cart, CartItem, OrderItem, ShippingAddress, PromoCode
from app.models.shop import Product, Category, Favorites
from app.permisions import IsOwnerOrAdmin, IsAdminOrReadOnly, IsSellerOrAdmin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from app.utils import gen_random_code
from app.models.users import User
from app.serializers import PreRegisterSerializer, ProductModelSerializer, UserLoginSerializer, CategoryModelSerializer, \
    OrderSerializer, CartModelSerializer, CartItemModelSerializer, ShippingAddressModelSerializer, \
    FavouritesModelSerializer, UserProfileModelSerializer, OTPVerifySerializer


class SendOTPGenericAPIView(GenericAPIView):
    serializer_class = PreRegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')


        code = gen_random_code()

        cache.set(f'code_{email}', {'code': code, 'username': username, 'email': email, 'password': password},
                  timeout=120)
        send_otp_email.delay(email, code)


        return Response({'message': 'VerificationCode sent to email.'}, status=status.HTTP_200_OK)






class VerifyOTPAndRegisterGenericAPIView(GenericAPIView):
    serializer_class = OTPVerifySerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        code = int(serializer.validated_data.get('code'))

        cached_data = cache.get(f'code_{email}')

        if not cached_data:
            return Response({'error': 'VerificationCode expired or not found.'}, status=400)

        if code != cached_data['code']:
            return Response({'error': f'Invalid code!'}, status=400)

        email = cached_data.get('email')
        username = cached_data.get('username')
        password = cached_data.get('password')
        print(email, username, password, type(password))


        if User.objects.filter(email=email).exists():
            return Response({'error': 'This Email already exist.'}, status=400)

        User.objects.create_user(email=email, username=username, password=password)

        cache.delete(f'code_{email}')

        return Response({'message': 'User registered successfully!'}, status=201)





class UserLoginGenericAPIView(GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')


        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)




class CategoryModelViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryModelSerializer
    permission_classes = [IsAdminOrReadOnly]




class ProductListCreateAPIView(ListCreateAPIView):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductModelSerializer

    def perform_create(self, serializer):
        if self.request.user.role not in ['SELLER', 'ADMIN']:
            raise PermissionDenied('You do not have permission to perform this action.')
        serializer.save()



class ProductRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductModelSerializer
    permission_classes = [IsSellerOrAdmin, IsAuthenticated]



class CartListAPIView(ListAPIView):
    queryset = Cart.objects.select_related('user').all()
    serializer_class = CartModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)



class CartCreateAPIView(GenericAPIView):
    queryset = CartItem.objects.select_related('cart', 'product_item').all()
    serializer_class = CartItemModelSerializer
    permission_classes = [IsAuthenticated]


    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = Cart.objects.get_or_create(user=self.request.user)

        serializer.save(cart=cart)

        return Response(serializer.data, status=status.HTTP_201_CREATED)





class CartRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]



class CheckoutListAPIView(ListAPIView):
    queryset = Cart.objects.select_related('user').all()
    serializer_class = CartModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        cart = Cart.objects.select_related('user').prefetch_related('items__product_item').filter(user=user).first()

        if not cart or not cart.items.exists():
            raise NotFound("Your cart is empty!")

        return super().get_queryset().filter(user=user)



class CheckoutPostAPIView(GenericAPIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        user = self.request.user
        cart = Cart.objects.prefetch_related('items__product_item').filter(user=user).first()

        if not cart or not cart.items.exists():
            return Response({"message": "Your cart is empty!"})

        shipping_address = get_object_or_404(ShippingAddress, user=user)

        promo_code_id = request.data.get('promo_code')
        promo_code = None
        if promo_code_id:
            try:
                promo_code = PromoCode.objects.get(id=promo_code_id)
            except PromoCode.DoesNotExist:
                return Response({"detail": "Invalid promo code."}, status=status.HTTP_400_BAD_REQUEST)


        order = Order.objects.create(
            user=user,
            shipping=shipping_address,
            promo_code=promo_code,
        )


        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product_items=item.product_item,
                quantity=item.quantity
            )


        cart.items.all().delete()

        return Response(
            {"message": "Order created successfully.", "order_id": order.id},
            status=status.HTTP_201_CREATED
        )



class OrderListCreateAPIView(ListCreateAPIView):
    queryset = Order.objects.select_related('user').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class OrderDeleteAPIView(DestroyAPIView):

    queryset = Order.objects.select_related('user').all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]



class FavouritesListCreateAPIView(ListCreateAPIView):
    serializer_class = FavouritesModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorites.objects.select_related('user', 'product').filter(user=self.request.user)



class FavouritesDeleteAPIView(DestroyAPIView):
    serializer_class = FavouritesModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorites.objects.select_related('user', 'product').filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You do not have permission to perform this action.")

        self.perform_destroy(instance)
        return Response({"message": "Deleted Successfully!"}, status=status.HTTP_204_NO_CONTENT)



class UserProfileListAPIView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)



class UserProfileRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]



class ShippingAddressModelViewSet(ModelViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressModelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)











