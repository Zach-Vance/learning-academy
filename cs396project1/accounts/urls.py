from django.urls import path
from django.contrib import admin
from .views import TeacherSignUpView, StudentSignUpView

urlpatterns = [
    # # path('register/', UserRegistrationView.as_view(), name=('register')),
    # path('admin', admin.site.urls, name='admin'),
    path('signup/teacher/', TeacherSignUpView.as_view(), name='teacher_signup'),
    path('signup/student/', StudentSignUpView.as_view(), name='student_signup'),
    # path('accounts/signup/teacher/', TeacherSignUpView.as_view(), name='teacher_signup'),
]