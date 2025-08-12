from django.shortcuts import render ,redirect,get_object_or_404
from .models import Product
from category.models import category
from carts.views import  _cart_id
from carts.models import CartItem
from django.core.paginator import Paginator ,EmptyPage,PageNotAnInteger
from django.db.models import Q
from .forms import ReviewForm 
from .models import ReviewRating
from orders.models import OrderProduct
from store.models import ProductGallery
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings



# Create your views here.

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(category, slug = category_slug)
        products = Product.objects.all().filter(category = categories,is_available=True).order_by('id')
        paginator = Paginator(products,2)
        
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products,3)
    

    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()
          
    context = {
        'products': paged_products,
        'product_count':product_count,   
    }
    return render(request, 'store/store.html',context)


def product_detail(request,category_slug,product_slug):
    try:
        product= Product.objects.get(category__slug = category_slug, slug = product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request),product = product).exists()  
    except Exception as e:
        raise e
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user,product_id=product.id).exists() 
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

        # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id = product.id)

    context = {
        'product':product,
        'in_cart' : in_cart,
        'orderproduct' : orderproduct,
        'reviews':reviews,
        'product_gallery': product_gallery
     
    }
    return render(request,'store/product_detail.html',context)


def search(request):
    products = []
    product_count = 0
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('created_date').filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
        else:
            products = Product.objects.filter(is_available=True).order_by('created_date')

        product_count = products.count()
    context={
        'products': products,
        'product_count' : products.count()

    }
    return render(request, 'store/store.html',context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            # Fetch the most recent review for this product by this user
            reviews = ReviewRating.objects.filter(
                user_id=request.user.id,
                product_id=product_id
            ).order_by('-id').first()  # Get latest review
            
            if reviews:
                # Update the existing review
                form = ReviewForm(request.POST, instance=reviews)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Thank you! Your review has been updated.')
            else:
                # Create a new review
                form = ReviewForm(request.POST)
                if form.is_valid():
                    data = ReviewRating()
                    data.subject = form.cleaned_data['subject']
                    data.rating = form.cleaned_data['rating']
                    data.review = form.cleaned_data['review']
                    data.ip = request.META.get('REMOTE_ADDR')
                    data.product_id = product_id
                    data.user = request.user
                    data.save()
                    messages.success(request, 'Thank you! Your review has been submitted.')

            return redirect(url)

        except Exception as e:
            messages.error(request, f"Error submitting review: {e}")
            return redirect(url)



def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_mail(
            subject,
            full_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],  # Apke email pe send hoga
        )

        messages.success(request, "Thank you! Your message has been sent.")
        return redirect('contact')

    return render(request, 'store/contact.html')