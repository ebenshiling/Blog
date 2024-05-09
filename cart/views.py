from django.shortcuts import render,redirect,get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product
from .models import Cart,CartItem
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging


# Create your views here.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # This is for authenticated users
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            product=product,
            user=request.user,  # Associate the cart item with the user
            defaults={'quantity': 1}
        )
        if not created:
            # If the cart item exists, increment the quantity
            cart_item.quantity += 1
            cart_item.save()

    else:
        # This is for anonymous users, using the session cart_id system
        cart_id = _cart_id(request)
        cart, created = Cart.objects.get_or_create(cart_id=cart_id)

        cart_item, created = CartItem.objects.get_or_create(
            product=product,
            cart=cart,  # Associate the cart item with the session-based cart
            defaults={'quantity': 1}
        )
        if not created:
            # If the cart item exists, increment the quantity
            cart_item.quantity += 1
            cart_item.save()

    return redirect('cart')  # Replace 'cart' with the name of your cart URL
def remove_cart(request, product_id ):

    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')



@login_required
def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_items = CartItem.objects.filter(product=product, user=request.user)

    for cart_item in cart_items:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

# If you want to handle the case for anonymous users as well
def remove_cart_item_for_anonymous(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=request.user)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    for cart_item in cart_items:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

    
def cart(request, total=0, quantity=0, cart_items=None):
   
    try:
        tax = 0  
        grand_total = 0
              
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:    
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        # If the cart does not exist, you can decide what to do here.
        # Maybe you want to display a message that the cart is empty.
        pass  # just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/cart.html', context)
@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        messages.info(request, "Your cart is empty.")
        return redirect('store')  # Replace 'store' with the name of your store URL or appropriate view

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'store/checkout.html', context)