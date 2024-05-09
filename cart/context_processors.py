from .models import CartItem,Cart
from .views import _cart_id
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum 
from django.contrib.auth.decorators import login_required
def counter(request):
     cart_count = 0
     if 'admin' in request.path:
        return {}
     else:
        try:
            if request.user.is_authenticated:
                # Filter CartItem instances by the active cart of the logged-in user
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            else:
                # Get the cart using the cart_id from the session
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            # Sum the quantity of all items in the cart
            cart_count = cart_items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        except Cart.DoesNotExist:
            # If the cart does not exist, set cart_count to 0
            cart_count = 0

     return {'cart_count': cart_count}
# Context processor to add cart_count to all templates
# Uses counter function to get the number of items in the cart
# and adds it to the dictionary which is then accessible from
# all templates.
