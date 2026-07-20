from django.db import models


class Book(models.Model):
    title = models.CharField(unique=True, max_length=50)
    pub_date = models.DateTimeField()
    editorial_name = models.CharField(unique=True, max_length=100)
    editorial_address = models.TextField()

    def __str__(self):
        return self.title

