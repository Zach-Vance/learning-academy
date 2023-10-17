from django.urls import path
# from . import views
from .views import (HomeView, 
                    LessonView,
                    CreatePostView, 
                    CreateLessonView, 
                    LessonFeedView,
                    PostView,
                    QuizListView,
                    QuizCreateView,
                    QuizUpdateView,
                    QuizDeleteView,
                    QuizResultsView,
                    question_add,
                    question_change,
                    QuestionDeleteView,
                    StudentQuizListView,
                    TakenQuizListView,
                    take_quiz,
                    )
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('post/<int:pk>', PostView.as_view(), name='post'),
    path('lesson/<int:pk>', LessonView.as_view(), name='lesson'),
    path('create_post/', CreatePostView.as_view(), name='create_post'),
    path('create_lesson/', CreateLessonView.as_view(), name='create_lesson'),
    path('lesson_feed/', LessonFeedView.as_view(), name='lesson_feed'),
    path('teacher_quiz_list/', QuizListView.as_view(), name="teacher_quiz_list"),
    path('create_quiz/', QuizCreateView.as_view(), name="create_quiz"),
    path('quiz/add/', QuizCreateView.as_view(), name='quiz_add'),
    path('quiz/<int:pk>/', QuizUpdateView.as_view(), name='edit_quiz'),
    path('quiz/<int:pk>/delete/', QuizDeleteView.as_view(), name='quiz_delete'),
    path('quiz/<int:pk>/results/', QuizResultsView.as_view(), name='quiz_results'),
    path('quiz/<int:pk>/question/add/', question_add, name='question_add'),
    path('quiz/<int:quiz_pk>/question/<int:question_pk>/', question_change, name='question_change'),
    path('quiz/<int:quiz_pk>/question/<int:question_pk>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
    path('student_quiz_list/', StudentQuizListView.as_view(), name='student_quiz_list'),
    path('student_quiz_results/', TakenQuizListView.as_view(), name='student_quiz_results'),
    path('student_quiz/<int:pk>/', take_quiz, name='take_quiz'),
] 
