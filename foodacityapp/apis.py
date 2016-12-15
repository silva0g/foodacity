import json

from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.models import AccessToken

from foodacityapp.models import Restaurant, Meal, Order, OrderDetails, Driver
from foodacityapp.serializers import RestaurantSerializer, \
    MealSerializer, \
    OrderSerializer

# Import stripe token
import stripe
from foodacity.settings import STRIPE_API_KEY

stripe.api_key = STRIPE_API_KEY


##############
## CUSTOMER
#############

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"restaurants": restaurants})

def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id = restaurant_id).order_by("-id"),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"meals": meals})

@csrf_exempt
def customer_add_order(request):
    """
        params:
            access_token
            restaurant_id
            address
            order_details (json format), example:
                [{"meal_id": 1, "quantity": 2}, {"meal_id": 2, "quantity": 3}]
            stripe_token

            return:
                {"status": "success"}

    """
    if request.method == "POST":
        # Get token from the parameter:
        #access_token = AccessToken.objects.get(token = request.POST.get("access_token"), expires__gt = timezone.now())
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())
        # Get profile
        customer = access_token.user.customer

        # GET Stripe token
        stripe_token = request.POST["stripe_token"]

        # Check whether the customer has any order that is not delivered
        if Order.objects.filter(customer = customer).exclude(status = Order.DELIVERED):
            return JsonResponse({"status": "failed", "error": "Your last order must be completed." })

        # Check the address:
        if not request.POST["adress"]: # That means the user has not provided the address
            return JsonResponse({"status": "failed", "error": "You must provide your address."})

        # Get Order Details
        order_details = json.loads(request.POST["order_details"])

        order_total = 0
        for meal in order_details:
            order_total += Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]

        if len(order_details) > 0:

            # Step 1: Create a charge: This will charge customer's card
            charge = stripe.Charge.create(
                amount = order_total * 100, # Amount in cents
                currency = "eur",
                source = stripe_token,
                #descriprion =   "Foodacity Order"
            )

            # In here we need to Check
            if charge.status != "failed":
                # Step 2 - Create an order
                order = Order.objects.create(
                    customer = customer,
                    restaurant_id = request.POST["restaurant_id"],
                    total = order_total,
                    status = Order.COOKING,
                    adress = request.POST["adress"]
                )

                # Step 3 - Create an order details
                for meal in order_details:
                    OrderDetails.objects.create(
                        order = order,
                        meal_id = meal["meal_id"],
                        quantity = meal["quantity"],
                        subtotal = Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
                    )

                    return JsonResponse({"status": "success"})
            else:
                # if everything is wrong we will say:
                return JsonResponse({"status": "failed", "error": "failed connect to stripe"})


def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(token = request.GET.get("access_token"),
        expires__gt = timezone.now())

    customer = access_token.user.customer
    order = OrderSerializer(Order.objects.filter(customer = customer).last()).data

    return JsonResponse({"order": order})

# GET request
#Params: access_token
def customer_driver_location(request):
    access_token = AccessToken.objects.get(token = request.GET.get("access_token"),
        expires__gt = timezone.now())

    customer = access_token.user.customer
    current_order = Order.objects.filter(customer = customer, status = Order.ONTHEWAY).last()
    location = current_order.driver.location

    return JsonResponse({"location": location})

##############
## RESTAURANT
#############

# Added this to display all the restaurants in the database:
def restaurant_front():

    return JsonResponse()

def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(restaurant = request.user.restaurant,
        created_at__gt = last_request_time).count()

    # SQL Language
    #select count(*) from Orders where
    #restaurant = request.user.restaurant AND created_at > last_request_time

    return JsonResponse({"notification": notification })


##############
## DRIVERS
#############
def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status = Order.READY, driver = None).order_by("-id"),
        many = True
    ).data
    return JsonResponse({"orders": orders})


# POST
#params: access_token, order_id
@csrf_exempt # We put it because of the POST request
def driver_pick_order(request):

    if request.method == "POST":
        # Get Token:
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())

        # Get Driver based on the token
        driver = access_token.user.driver

        # Check if driver can pick one order at the same time
        if Order.objects.filter(driver = driver).exclude(status = Order.ONTHEWAY):
            return JsonResponse({"status": "failed", "error": "You can only pick one order at the same time "})
        try:
            order = Order.objects.get(
                id = request.POST["order_id"],
                driver = None,
                status = Order.READY
            )
            order.driver = driver
            order.status = Order.ONTHEWAY
            order.picked_at = timezone.now()
            order.save()

            return JsonResponse({"status": "success"})

        except Order.DoesNotExist:
            return JsonResponse({"status": "failed", "error": "This order has been picked up by another"})

    return JsonResponse({})

def driver_get_latest_order(request):

    # GET
    # Params: access_token, order_id
    access_token = AccessToken.objects.get(token = request.GET.get("access_token"),
        expires__gt = timezone.now())

    driver = access_token.user.driver
    order = OrderSerializer(
        Order.objects.filter(driver = driver).order_by("picked_at").last()
    ).data
    return JsonResponse({"order": order})

# POST request
# Params: access_token:
@csrf_exempt # We put it because of POST request
def driver_complete_order(request):
    # Get token
    access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
        expires__gt = timezone.now())

    driver = access_token.user.driver

    order = Order.objects.get(id = request.POST["order_id"], driver = driver)
    order.status = Order.DELIVERED
    order.save()
    return JsonResponse({ "status": "success"})

# GET method
# params: WE're gonna pass the access_token
def driver_get_revenue(request):
    # Get access_token
    access_token = AccessToken.objects.get(token = request.GET.get("access_token"),
        expires__gt = timezone.now())

    driver = access_token.user.driver

    from datetime import timedelta

    revenue = {} # Here we define the revenue variable as an empty dictionary
    today = timezone.now() # Create a new variable called today
    # Created a new array variable called current_weekdays
    current_weekdays = [today + timedelta(days = i) for i in range(0 - today.weekday(), 7 - today.weekday())]

    for day in current_weekdays:
        orders = Order.objects.filter(
            driver = driver,
            status = Order.DELIVERED,
            created_at__year = day.year,
            created_at__month = day.month,
            created_at__day = day.day
        )

        revenue[day.strftime("%a")] = sum(order.total for order in orders)

    # Now we need to return the revenue as an array
    return JsonResponse({"revenue": revenue})

# POST request
# Params: access_token, latitude, longitude
@csrf_exempt
def driver_update_location(request):
    if request.method == "POST":
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())

        driver = access_token.user.driver
        # SET the location String => database
        driver.location = request.POST["location"]
        driver.save()

        return JsonResponse({"status": "success"})
