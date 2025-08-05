from .models import Cart, CartItem
from .views import _cart_id

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    
    try:
        if request.user.is_authenticated:
            # For logged-in user, use user-based cart items
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            # For guest user, use session cart
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            cart_count += cart_item.quantity

    except Cart.DoesNotExist:
        cart_count = 0

    return {'cart_count': cart_count}
