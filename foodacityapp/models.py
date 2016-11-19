from django.db import models
from django.contrib.auth.models import User

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
