from django.shortcuts import render, redirect, get_object_or_404
from .models import CartItem, Cart
from store.models import Product, Variation
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    current_user = request.user
    product_variation = []

    # --- 1. Get selected variations from POST ---
    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # --- 2. Determine if user is authenticated or guest ---
    if current_user.is_authenticated:
        # Authenticated user -> Use user for CartItem
        cart_item_qs = CartItem.objects.filter(product=product, user=current_user)
    else:
        # Guest user -> Use session cart
        cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
        cart_item_qs = CartItem.objects.filter(product=product, cart=cart)

    # --- 3. Check if cart item already exists ---
    if cart_item_qs.exists():
        existing_variations_list = []
        ids = []

        for item in cart_item_qs:
            existing_variations_list.append(list(item.variations.all()))
            ids.append(item.id)

        if product_variation in existing_variations_list:
            # If same variation exists -> increase quantity
            index = existing_variations_list.index(product_variation)
            item_id = ids[index]
            item = CartItem.objects.get(id=item_id)
            item.quantity += 1
            item.save()
        else:
            # If different variation -> create a new cart item
            item = CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user if current_user.is_authenticated else None,
                cart=None if current_user.is_authenticated else cart,
            )
            if product_variation:
                item.variations.add(*product_variation)
            item.save()
    else:
        # --- 4. Create new cart item if product not in cart ---
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            user=current_user if current_user.is_authenticated else None,
            cart=None if current_user.is_authenticated else cart,
        )
        if product_variation:
            cart_item.variations.add(*product_variation)
        cart_item.save()

    return redirect('cart')


def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    current_user = request.user

    try:
        if current_user.is_authenticated:
            # User-based cart
            cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
        else:
            # Guest/session-based cart
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        # Decrease quantity or delete
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        pass  # Safe fallback

    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    current_user = request.user

    try:
        if current_user.is_authenticated:
            # Remove for logged-in user
            cart_item = CartItem.objects.get(product=product, user=current_user, id=cart_item_id)
        else:
            # Remove for guest/session cart
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        # Delete the cart item completely
        cart_item.delete()

    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        pass  # Safe fallback

    return redirect('cart')



def cart(request , total=0,quantity=0,cart_item = None):
    tax = 0
    grand_total =0
    cart_items = []

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user,is_active=True)
        
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity )
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass


    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax' : tax,
        'grand_total':grand_total,
    }
    return render(request,'store/cart.html',context)



@login_required(login_url='login')
def checkout(request, total=0,quantity=0,cart_item = None):
        tax = 0
        grand_total =0
        cart_items = []

        try:
            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user,is_active=True)
        
            else:
                cart_items = CartItem.objects.filter(cart=cart,is_active=True)
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity )
                quantity += cart_item.quantity
            tax = (2 * total)/100
            grand_total = total + tax

        except ObjectDoesNotExist:
            pass


        context={
            'total': total,
            'quantity': quantity,
            'cart_items': cart_items,
            'tax' : tax,
            'grand_total':grand_total,
        }
        return render(request,'store/checkout.html',context)