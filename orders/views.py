from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from carts.models import CartItem
from orders.models import Order, OrderProduct
from .forms import OrderForm
import datetime
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage
from orders.models import Payment



@login_required(login_url='login')
def payments(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        if order.is_ordered:
            return redirect('order_complete', order_id=order.id)
    except Order.DoesNotExist:
        return redirect('store')

    order_products = OrderProduct.objects.filter(order=order)

    total = 0
    for item in order_products:
        total += item.product_price * item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    context = {
        'order': order,
        'order_products': order_products,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'orders/payments.html', context)


@login_required(login_url='login')
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    if cart_items.count() <= 0:
        return redirect('store')

    # Calculate totals
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100
    grand_total = total + tax

    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f"Insufficient stock for {item.product.product_name}. Available: {item.product.stock}")
            return redirect('cart')


    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():     
            # Create Order object
            order = Order()
            order.user = current_user
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.email = form.cleaned_data['email']
            order.phone = form.cleaned_data['phone']
            order.address_line_1 = form.cleaned_data['address_line_1']
            order.address_line_2 = form.cleaned_data['address_line_2']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.pincode = form.cleaned_data['pincode']  
            order.order_note = form.cleaned_data['order_note']
            order.order_total = grand_total
            order.tax = tax
            order.ip = request.META.get('REMOTE_ADDR')
            order.is_ordered = False
            order.save()

            # Generate order number
            current_date = datetime.date.today().strftime('%Y%m%d')
            order_number = current_date + str(order.id)
            order.order_number = order_number
            order.save()

            #  Move cart items to OrderProduct
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order = order
                order_product.user = current_user
                order_product.product = item.product
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()

                # Save variations
                if item.variations.exists():
                    order_product.variation.set(item.variations.all())

                #  Reduce stock
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                else:
                    # Optional: rollback order if not enough stock
                    order.delete()
                    return redirect('cart')  # Or show an error message

            # Clear cart
            # cart_items.delete()

            # Redirect to payments
            return redirect('payments', order_id=order.id)

    return redirect('checkout')


@login_required(login_url='login')
def complete_payment(request, order_id):
    order = get_object_or_404(Order,id=order_id, user=request.user, is_ordered=False)
    
    # Mark order as completed
    order.is_ordered = True
    order.save()

    # Clear cart after payment
    CartItem.objects.filter(user=request.user).delete()

    return redirect('order_complete', order_id=order.id)

@login_required(login_url='login')
def order_complete(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)
        payment = Payment.objects.filter(order=order).last()

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        # Send confirmation email only if not sent already
        if not order.email_sent:
            subject = 'Order Confirmation 🎉'
            message = f"""
            <p>Hi {order.first_name},</p>
            <p>Thank you for your order 🎉</p>
            <p>Your order number is <strong>{order.order_number}</strong>.</p>
            <p>You can continue shopping <a href="http://127.0.0.1:8000/store">here</a>.</p>
            """
            email = EmailMessage(subject, message, to=[order.email])
            email.content_subtype = 'html'
            email.send()

            # Optional: set a flag to avoid sending email again on page refresh
            order.email_sent = True
            order.save()

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID':payment.payment_id if payment else None,
            'payment':payment,
            'subtotal':subtotal,
        }
        return render(request, 'orders/order_complete.html', context)

    except Order.DoesNotExist:
        return redirect('home')


    
