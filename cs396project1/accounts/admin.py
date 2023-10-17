from django.contrib import admin
from .models import User
from .forms import TeacherSignUpForm
from django.contrib.auth.admin import UserAdmin


# Register your models here.
class CustomUserAdmin(UserAdmin):
    model = User
    add_form = TeacherSignUpForm
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'Other Personal info',  #Adding this so the admin can distinguish student and teacher accounts from the admin panel
            {
                'fields': (
                    'is_teacher',
                    'is_student',
                )
            }
        )
    )


admin.site.register(User, CustomUserAdmin)