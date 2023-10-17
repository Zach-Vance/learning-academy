from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.db import transaction
from .models import User  # Importing the User model from the current app
from learn.models import Student

# Form for signing up as a teacher
class TeacherSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Using the User model from the current app
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True  # Assigning the role of a teacher to the user
        email = forms.EmailField()  
        first_name = forms.CharField(max_length=25)  
        last_name = forms.CharField(max_length=25)  
        if commit:
            user.save()  # Saving the user to the database
        return user

# Form for signing up as a student
class StudentSignUpForm(UserCreationForm):
    class Meta:
        model = User  # Using the User model from the current app
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True  # Assigning the role of a student to the user
        email = forms.EmailField()  
        first_name = forms.CharField(max_length=25)  
        last_name = forms.CharField(max_length=25) 
        user.save()  
        student = Student.objects.create(user=user)  # Creating a student associated with the user
        return user
