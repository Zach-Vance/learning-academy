from django.contrib import admin
from . models import Post, Comment, Lesson, Quiz, Subject, Question, Answer, TakenQuiz, StudentAnswer, StudentSubjectScore, StudentQuestionAnswer, QuestionAttempts, TeacherSubjectView

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Lesson)
admin.site.register(Quiz)
admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Answer)

admin.site.register(TakenQuiz)
admin.site.register(StudentAnswer)
admin.site.register(StudentSubjectScore)
admin.site.register(StudentQuestionAnswer)
admin.site.register(QuestionAttempts)

admin.site.register(TeacherSubjectView)