from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from cart.models import CartItem, Cart
from .forms import OrderForm
import datetime
from store.models import Product
from .models import Order, OrderProduct, Payment
from accounts.models import Account
from django.utils import timezone

# Create your views here.
import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import logging
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
stripe.api_key = settings.STRIPE_SECRET_KEY


logger = logging.getLogger(__name__)
def place_order(request, total=0, quantity=0,):
   current_user = request.user
   
   # if cart count is less than or equal to 0, then redirect back to shop
   cart_items = CartItem.objects.filter(user=current_user)
   cart_count = cart_items.count()
   if cart_count <= 0:
        return redirect('store')
   
   grand_total = 0
   tax = 0
   for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
   tax = (2 * total) / 100
   grand_total = total + tax   
    
    
   if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data ['first_name']
            data.last_name = form.cleaned_data ['last_name']
            data.phone = form.cleaned_data ['phone']
            data.email = form.cleaned_data ['email']
            data.address_line_1 = form.cleaned_data ['address_line_1']
            data.address_line_2 = form.cleaned_data ['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'public_key': settings.STRIPE_PUBLIC_KEY
                
            }
            
            return render(request, 'orders/payments.html', context)
   else:
            return redirect('checkout')
            
# Set your secret key: remember to change this to your live secret key in production
stripe.api_key = "sk_test_51PEwENEMKhA1kqzwjqkF2kjFbrGr5NXfyB04JaG5WjiGunNd05NR88L38eoge5HOuPC3tVL0LPcqivDSW6nv47sw00yaDHGC3b"
@csrf_exempt  # Only for demonstration, use CSRF protection in production
@require_POST
def create_charge(request):
    try:
        data = json.loads(request.body)
        token = data.get('stripeToken')
        user = request.user
        order_id = data.get('orderID')

        with transaction.atomic():
            # Attempt to retrieve the order
            order = Order.objects.get(user=user, is_ordered=False, order_number=order_id)

            # Calculate the total charge in cents for Stripe
            amount_to_charge = int(order.order_total * 100)  # Convert to cents

            # Create the charge on Stripe's servers
            charge = stripe.Charge.create(
                amount=amount_to_charge,
                currency="usd",
                description="Example charge",
                source=token,
            )

            # Create a payment object and link it to the order
            payment = Payment(
                user=user,
                payment_id=charge.id,
                payment_method=data['payment_method'],
                status=charge.status,
                amount_paid=order.order_total,
            )
            payment.save()
            order.payment = payment
            order.is_ordered = True
            order.save()
            # move the cart items to the Order Product table
            cart_items = CartItem.objects.filter(user=user)
            for item in cart_items:
                order_product = OrderProduct()
                order_product.order_id = order.id
                order_product.payment = payment
                order_product.user_id = request.user.id
                order_product.product_id = item.product_id
                order_product.quantity = item.quantity
                order_product.product_price = item.product.price
                order_product.ordered = True
                order_product.save()
            # Reduce the quantity of the sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()
            # Clear the cart
            CartItem.objects.filter(user=user).delete()
            
            # Send an order received email to the customer
            mail_subject = 'Thank You For Your Order'
            message = render_to_string('orders/order_received_email.html', {
                'user': request.user,
                'order': order,
                'current_year': timezone.now().year,
              
            })
            to_email = request.user.email
            send_email = EmailMessage (mail_subject, message, to=[to_email])
            send_email.content_subtype = 'html'
            send_email.send()
            # Send order number and transaction id back to sendData method via JsonResponse 

            # If the charge is successful, return a JSON response
            return JsonResponse({
                                     'status': 'Success',
                                        'message': 'Charge successful.',
                                        'order_number': order.order_number,
                                        'transaction_id': charge.id
                                 
                                 })

    except stripe.error.StripeError as e:
        logger.error('Stripe error: %s', e)
        # If there's an error from Stripe, respond with the error message
        return JsonResponse({'status': 'Failure', 'message': str(e)}, status=400)
    except ObjectDoesNotExist:
        logger.error('Object does not exist error') 
        # If the order does not exist, respond with an error message
        return JsonResponse({'status': 'Failure', 'message': 'Order not found.'}, status=404)
    except Exception as e:
        logger.exception('An unexpected error occurred while processing payment')
        # Log the exception and respond with a generic error message
        # Consider using Django's logging system to log the exception
        return JsonResponse({'status': 'Failure', 'message': 'An error occurred while processing your payment.'}, status=500)
def get_cart_total(user):
    # Filter CartItem instances by the user and sum the sub_total of each item.
    cart_items = CartItem.objects.filter(user=user, is_active=True)
    total = sum(item.sub_total() for item in cart_items)
    return total
def order_completed(request):
    order_id = request.GET.get('order_number')
    payment_id = request.GET.get('transaction_id')
    try:
        
        order = Order.objects.get(order_number=order_id, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order_id)
        subtotal = 0
        for  item in order.orderproduct_set.all():
            subtotal += item.product_price * item.quantity

        
            
        payment = Payment.objects.get(payment_id=payment_id)
        
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_id': order_id,
            'transaction_id':payment.payment_id,
            'payment':payment,
             'subtotal':subtotal,
            
        }
    
        
    
        return render(request, 'orders/order_completed.html',context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home') 

