from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

#Create you models here
class Restaurant(models.Model):
    # A restaurant belongs to one owner.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    #Who is the owner of this restaurant
    name = models.CharField(max_length=500)

    # Whats the name of this restaurant
    phone = models.CharField(max_length=500)

    adress = models.CharField(max_length=500)
    logo = models.ImageField(upload_to='restaurant_logo/', blank=False)

    def __str__(self):
        return self.name

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    avatar = models.CharField(max_length=500)
    phone = models.CharField(max_length=500, blank=True)
    adress = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver')
    avatar = models.CharField(max_length=500)
    phone = models.CharField(max_length=500, blank=True)
    adress = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.user.get_full_name()

# Create models for the meals
class Meal(models.Model):
    restaurant = models.ForeignKey(Restaurant)
    # Name of the meals
    name = models.CharField(max_length = 500)
    short_description = models.CharField(max_length = 500)
    image = models.ImageField(upload_to = 'meal_images/', blank=False)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.name

# Create model for orders
class Order(models.Model):
    # Define 4 states for the order:
    COOKING = 1
    READY = 2
    ONTHEWAY = 3
    DELIVERED = 4

    STATUS_CHOICES = (
        (COOKING, "Cooking"),
        (READY, "Ready"),
        (ONTHEWAY, "On the way"),
        (DELIVERED, "Delivered"),
    )

    # An order needs information about the customer, restaurant and the Driver
    # We need to know Who the customer is, the restaurant and the Driver
    customer = models.ForeignKey(Customer)
    restaurant = models.ForeignKey(Restaurant)
    driver = models.ForeignKey(Driver, blank = True, null = True)
    adress = models.CharField(max_length=500)# Adress for the delivery
    total = models.IntegerField()#Valor a pagar
    status = models.IntegerField(choices = STATUS_CHOICES )
    created_at = models.DateTimeField(default = timezone.now)
    # Recall the time when the driver picked this order
    picked_at = models.DateTimeField(blank = True, null = True)

    def __str__(self):
        return str(self.id)


class OrderDetails(models.Model):
    order = models.ForeignKey(Order, related_name ='order_details')
    meal = models.ForeignKey(Meal)
    quantity = models.IntegerField()
    subtotal = models.IntegerField()

    def __str__(self):
        return str(self.id)
