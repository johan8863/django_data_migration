from django.db import models


class Editorial(models.Model):
    name = models.CharField(unique=True, max_length=50)
    address = models.TextField()

    def __str__(self):
        return self.name


class Book(models.Model):
    editorial = models.ForeignKey(Editorial, on_delete=models.CASCADE)
    title = models.CharField(unique=True, max_length=50)
    pub_date = models.DateTimeField()

    def __str__(self):
        return self.title

