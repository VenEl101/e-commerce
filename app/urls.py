from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter

from app.views import CategoryModelViewSet, ProductListCreateAPIView, ProductRetrieveUpdateDestroyAPIView, \
    OrderListCreateAPIView, OrderDeleteAPIView, CartListAPIView, CartRetrieveUpdateDestroyAPIView, CartCreateAPIView, \
    CheckoutListAPIView, CheckoutPostAPIView, ShippingAddressModelViewSet, FavouritesListCreateAPIView, \
    FavouritesDeleteAPIView, SendOTPGenericAPIView, UserLoginGenericAPIView, VerifyOTPAndRegisterGenericAPIView

router = DefaultRouter()

# router.register('order', OrderViewSet, basename='orderview')
router.register('category', CategoryModelViewSet, basename='profile-view')
router.register('shipping-address', ShippingAddressModelViewSet, basename='shipping-address-view')


urlpatterns = [

    path('sign-up/', SendOTPGenericAPIView.as_view(), name='UserRegister'),
    path('login/', UserLoginGenericAPIView.as_view(), name='UserLogin'),
    path('verify-code/', VerifyOTPAndRegisterGenericAPIView.as_view(), name='verify'),

    path('', include(router.urls)),
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyAPIView.as_view(), name='product-detail'),

    path('cart/', CartListAPIView.as_view(), name='cart-list'),
    path('cart/create/', CartCreateAPIView.as_view(), name='cart-create'),
    path('cart/<int:pk>/', CartRetrieveUpdateDestroyAPIView.as_view(), name='cart-detail'),

    path('checkout-list/', CheckoutListAPIView.as_view(), name='checkout-list'),
    path('checkout-post/', CheckoutPostAPIView.as_view(), name='checkout-post'),

    path('order/', OrderListCreateAPIView.as_view(), name='order'),
    path('order/<int:pk>/', OrderDeleteAPIView.as_view(), name='order-delete'),

    path('favourites/', FavouritesListCreateAPIView.as_view(), name='favourites-list'),
    path('favourites-delete/', FavouritesDeleteAPIView.as_view(), name='favourites-delete'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('docs/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]