from django.db import models
from accounts.models import Account
# from orders.models import Payment,Order
from store.models import Product, Variation



# Create your models here.

class Payment(models.Model):
    user = models.ForeignKey(Account,on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id


class Order(models.Model):
    #  Define order statuses
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    #  Foreign keys for user and payment
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)

    #  Order details
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)

    #  Shipping address
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6,default='000000')
    order_note = models.CharField(max_length=100, blank=True)

    #  Order amounts
    order_total = models.FloatField()
    tax = models.FloatField()

    #  Order status & tracking info
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(max_length=20, blank=True)
    is_ordered = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)


    #  Auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #  String representation for admin panel
    def full_name(self):
        return f'{self.first_name } {self.last_name}'
    
    def full_address(self):
        return f'{self.address_line_1 } {self.address_line_2}'

    def __str__(self):
         return f'{self.first_name } {self.last_name}'
 


class OrderProduct(models.Model):
    # Relations with other models
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)              # Order this product is part of
    payment = models.ForeignKey('orders.Payment', on_delete=models.SET_NULL, blank=True, null=True)  # Payment info
    user = models.ForeignKey(Account, on_delete=models.CASCADE)             # User who purchased the product
    product = models.ForeignKey(Product, on_delete=models.CASCADE)          # Product being purchased
    variation = models.ManyToManyField(Variation, blank=True)     # Product variation (size/color)

    # Product details
    # color = models.CharField(max_length=50)                                 # Color of the product
    # size = models.CharField(max_length=50)                                  # Size of the product
    quantity = models.IntegerField()                                        # Quantity purchased
    product_price = models.FloatField()                                     # Price per unit
    ordered = models.BooleanField(default=False)                            # Mark if the product is already ordered

    # Auto timestamps
    created_at = models.DateTimeField(auto_now_add=True)                     # When this record is created
    updated_at = models.DateTimeField(auto_now=True)                         # When this record was last updated

    def __str__(self):
        return self.product.product_name                                     # Display product name in admin
