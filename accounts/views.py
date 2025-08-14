from django.shortcuts import render , redirect,get_object_or_404
from accounts.forms import RegistrationForm ,UserForm,UserProfileForm
from django.contrib import messages , auth
from accounts.models import Account
from orders.models import Order, OrderProduct 
from django.contrib.auth.decorators import login_required 

# Verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User

from carts.views import _cart_id
from carts.models import Cart,CartItem
import requests
from .models import UserProfile


# Create your views here.
from django.db import IntegrityError
from django.contrib import messages
from accounts.models import Account

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            # Prevent duplicate email (case-insensitive)
            if Account.objects.filter(email__iexact=email).exists():
                messages.error(request, "An account with this email already exists. Please log in or use Forgot Password.")
                return redirect('login')

            # (Optional) also avoid username collisions if username is unique
            if Account.objects.filter(username__iexact=username).exists():
                messages.error(request, "Username derived from email already exists. Please choose another email.")
                return redirect('register')

            try:
                user = Account.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    username=username,
                    password=password
                )
                user.phone_number = phone_number
                user.is_active = True  # activate immediately
                user.save()

                messages.success(request, "Your account has been created successfully! You can log in now.")
                return redirect('login')
            except IntegrityError:
                # Safety net in case a race condition slips through
                messages.error(request, "This email is already registered. Please log in or reset your password.")
                return redirect('login')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

    
   

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                # Merge guest cart to user cart
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)

                if cart_items.exists():
                    product_variation_list = []  # variations of guest cart

                    for item in cart_items:
                        variations = list(item.variations.all())
                        product_variation_list.append(variations)

                    # Get existing user cart items
                    user_cart_items = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id_list = []

                    for item in user_cart_items:
                        existing_variations = list(item.variations.all())
                        ex_var_list.append(existing_variations)
                        id_list.append(item.id)

                    # Merge guest cart into user cart
                    for idx, pr in enumerate(product_variation_list):
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id_list[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += cart_items[idx].quantity
                            item.save()
                            cart_items[idx].delete()  # delete guest cart item
                        else:
                            # Assign guest cart item to user
                            cart_items[idx].user = user
                            cart_items[idx].save()
            except Cart.DoesNotExist:
                pass

            auth.login(request, user)
            messages.success(request, "You are now logged in!") 
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params= dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextpage = params['next']
                    return redirect(nextpage)
                
            except:
                return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'accounts/login.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, " Your account has been activated successfully.")
        return redirect('login')  # change 'login' to your actual login page name
    else:
        messages.error(request, " Activation link is invalid or has expired.")
        return redirect('signup')  # change 'signup' to your actual signup page name

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)  #  This clears the session
    messages.info(request, "You have been logged out successfully!")
    return redirect('home')  # Redirect to login page or home page

@login_required(login_url = 'login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
    orders_count = orders.count()
    userprofile = UserProfile.objects.get(user_id = request.user.id)
    context = {
        'orders_count':orders_count,
        'userprofile' : userprofile,
    }
    return render(request,'accounts/dashboard.html',context)

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset password email 
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html',{
                'user': user,
                'domain':current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token' : default_token_generator.make_token(user)

            })
            to_email = email
            send_email = EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()


            messages.success(request,'Password reset email has been sent to your email address.')
            return redirect('login')
 
        else:
            message.error(request,'Account does not exist!')    
            return redirect('forgotPassword')

    return render(request,'accounts/forgotPassword.html')


def resetpassword_validate(request ,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.success(request,'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request,'This link has been expired!')
        return redirect('login')


@login_required(login_url = 'login')
def resetPassword(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk = uid)
            user.set_password(password)
            user.save()
            messages.success(request,'Password Reset Successful')
            return redirect('login')
        else:
            messages.error(request,'Password do not match!')
            return redirect('resetPassword')
    else:
        return render(request,'accounts/resetPassword.html')


@login_required(login_url = 'login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context = {
        'orders':orders
    }
    return render(request,'accounts/my_orders.html',context)


@login_required(login_url = 'login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile,user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST,instance = request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,'Your profile has been updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form= UserProfileForm(instance=userprofile)
    context= {
        'user_form':user_form,
        'profile_form':profile_form,
        'userprofile':userprofile,
    }
    return render(request,'accounts/edit_profile.html',context)


@login_required(login_url = 'login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact = request.user.username)
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
# auth.Logout(request)  --> if want to logout after change password uncomment it 
                messages.success(request,'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request,'Please Enter Valid Password')
                return redirect('change_password')
        else:
            messages.error(request,'Password Does Not Match')
            return redirect('change_password')
    return render(request,'accounts/change_password.html')


@login_required(login_url = 'login')
def order_detail(request,order_id):
    order_detail = OrderProduct.objects.filter(order__order_number = order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    context = {
        'order_detail': order_detail,
        'order':order,
        'subtotal': subtotal,
    }
    return render(request,'accounts/order_detail.html',context)
