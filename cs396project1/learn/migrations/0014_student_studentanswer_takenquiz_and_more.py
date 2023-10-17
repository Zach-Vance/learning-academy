# Generated by Django 4.2.4 on 2023-09-25 00:54

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0002_delete_student"),
        ("learn", "0013_remove_lesson_file_remove_post_file_lesson_file1_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Student",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudentAnswer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TakenQuiz",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("score", models.FloatField()),
                ("date", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="answer",
            name="correct",
        ),
        migrations.RemoveField(
            model_name="answer",
            name="created",
        ),
        migrations.RemoveField(
            model_name="question",
            name="created",
        ),
        migrations.RemoveField(
            model_name="quiz",
            name="num_questions",
        ),
        migrations.AddField(
            model_name="answer",
            name="is_correct",
            field=models.BooleanField(default=False, verbose_name="Correct answer"),
        ),
        migrations.AddField(
            model_name="quiz",
            name="owner",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quizzes",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="answers",
                to="learn.question",
            ),
        ),
        migrations.AlterField(
            model_name="answer",
            name="text",
            field=models.CharField(max_length=255, verbose_name="Answer"),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="file1",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="file2",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="file3",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="images/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["jpg", "gif", "jpeg"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="lesson",
            name="video",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["mp4"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="file1",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="file2",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="file3",
            field=models.FileField(
                blank=True,
                upload_to="documents/",
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx", "txt"]
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="quiz",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="learn.quiz",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="text",
            field=models.CharField(max_length=255, verbose_name="Question"),
        ),
        migrations.AlterField(
            model_name="quiz",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.DeleteModel(
            name="Results",
        ),
        migrations.AddField(
            model_name="takenquiz",
            name="quiz",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="taken_quizzes",
                to="learn.quiz",
            ),
        ),
        migrations.AddField(
            model_name="takenquiz",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="taken_quizzes",
                to="learn.student",
            ),
        ),
        migrations.AddField(
            model_name="studentanswer",
            name="answer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="learn.answer",
            ),
        ),
        migrations.AddField(
            model_name="studentanswer",
            name="student",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quiz_answers",
                to="learn.student",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="quizzes",
            field=models.ManyToManyField(through="learn.TakenQuiz", to="learn.quiz"),
        ),
    ]
