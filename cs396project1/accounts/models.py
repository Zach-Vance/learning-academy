from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    previous_login = models.DateTimeField(null=True, blank=True)

    def update_previous_login(self):
        self.previous_login = timezone.now()
        self.save()


    