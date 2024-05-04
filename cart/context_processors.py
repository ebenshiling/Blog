from .models import CartItem,Cart
from .views import _cart_id
def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return{}
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.all().filter(cart=cart)
        
            for cart_item in cart_items:
             cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0

    return dict(cart_count = cart_count)
# Context processor to add cart_count to all templates
# Uses counter function to get the number of items in the cart
# and adds it to the dictionary which is then accessible from
# all templates.
