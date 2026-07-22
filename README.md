# Django Data Migration

## Project Descritpion

This project demoonstrate how to handle migrations on Django when the database already has data and helps to avoid starting over. On ***main*** branch you'll se all of the changes applied but here is a rundown to se the progress by switching branches. The use case consists of a hypothetical scenario where a Django model might start growing and some of it attributes could conceive a new model to be related, to get to the point, a book that grew with attributes from its editorial.

## Key Points

- On ***main*** and ***dev*** branches: Final Project.
- On ***container-model*** branch: Initial ***Book*** model with Editorial attributes within.
- On ***data-migration*** branch: The migration process consisting of several steps.
  - Creating the ***Editorial*** Django model replicating the editorial attributes on ***Book*** and adding a Foreignkey editorial attribute to ***Book*** with `null=True` s that Django won't complain.
  - Creating an empty migration to handle the data migration logic.
  - Removing both previous editorial attributes from ***Book*** and editorial Foreignkey attribute nullity (`null=True`)
- On ***deployment-improvement*** branch: One final tuning in case the database is empty.

## The process

Our first version of the ***Book*** Django model it'll look like this:

```python
class Book(models.Model):
    title = models.CharField(unique=True, max_length=50)
    pub_date = models.DateTimeField()
    editorial_name = models.CharField(max_length=100)
    editorial_address = models.TextField()

    def __str__(self):
        return self.title
```

Both `editorial_name` and `editorial_address` attributes are the evidence of a growing model. Then let's create the ***Editorial*** Django model as needed.

```python
class Editorial(models.Model):
    name = models.CharField(unique=True, max_length=50)
    address = models.TextField()

    def __str__(self):
        return self.name


class Book(models.Model):
    editorial = models.ForeignKey(Editorial, on_delete=models.CASCADE, null=True) # temporary nullity
    title = models.CharField(unique=True, max_length=50)
    pub_date = models.DateTimeField()
    editorial_name = models.CharField(max_length=100)
    editorial_address = models.TextField()

    def __str__(self):
        return self.title
```

After this migration is created and applied by running `python manage.py makemigrations` and `python manage.py makemigrations` respectively.

Now these models gives us the posibility of transfering data from one to the other. Run `python manage.py makemigrations bookstore --empty` so that Django will store an empty auto migration in the `bookstore` app to handle the logic using this code.

```python
from django.db import migrations, transaction

def forward_migrate_editorial(apps, schema):
    """
    Creates Editorials from Book data and assign them
    """

    # get historical models versions as suggested here
    # https://docs.djangoproject.com/en/5.2/topics/migrations/#historical-models
    Book = apps.get_model('bookstore', 'Book')
    Editorial = apps.get_model('bookstore', 'Editorial')

    # iterate over every book in a transaction to ensure 
    # database performance and th fact that data
    # will be rolled back in case of failure
    with transaction.atomic():
        for book in Book.objects.all():
            # get_or_create returns a tuple of (object, created) 
            # the second value won't be necessary this time
            # that's whay the wildcard variable _
            editorial, _ = Editorial.objects.get_or_create(
                # check for coincidences no matter case sensitive
                name__iexact=book.editorial_name,
                # lets keep the name with original capitalization
                defaults={
                    'name': book.editorial_name,
                    'address': book.editorial_address
                }
            )

            # assign editorial to book
            book.editorial = editorial
            book.save()

def reverse_migrate_editorial(apps, schema_editor):
    """
    Undo the migration, put back editorial data as
    text fields in Book and deletes editorials
    """

    Book = apps.get_model('bookstore', 'Book')
    Editorial = apps.get_model('bookstore', 'Editorial')

    # iterate over every book related to an editorial
    # in a transaction
    with transaction.atomic():
        # select_related add performance over database searching
        # when retrieving foreign-key relationships
        for book in Book.objects.select_related('editorial').all():
            if book.editorial:
                book.editorial_name = book.editorial.name
                book.editorial_address = book.editorial.address
                book.save()
    
    # remove all Editorial objects
    Editorial.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('bookstore', '0003_editorial_book_editorial'),
    ]

    operations = [
        migrations.RunPython(
            code=forward_migrate_editorial, 
            reverse_code=reverse_migrate_editorial
        )
    ]
```

With the new models tables filled by the migration logic, first clean up previous attributes and nullity.

```python
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
```

Then create a second empty migration clean the data at dadabase level.

```python
from django.db import migrations, models


def ensure_all_books_have_editorial(apps, schema_editor):
    """
    Ensures all books have an editorial, if a book doesn't have
    any get assigned the first one, if no Editorial exists a default one
    is created
    """

    # get historical models
    Editorial = apps.get_model('bookstore', 'Editorial')
    Book = apps.get_model('bookstore', 'Book')

    # get first Editorial object
    first_editorial = Editorial.objects.first()

    # if no editorials create a default one
    if not first_editorial:
        first_editorial = Editorial.objects.create(
            name='Default editorial',
            address='Default editorial address',
        )
    
    # get all books without editorials and update them
    books_without_editorial = Book.objects.filter(editorial__isnull=True)
    books_without_editorial.update(editorial=first_editorial)


class Migration(migrations.Migration):

    dependencies = [
        ('bookstore', '0004_auto_20260720_2006'),
    ]

    operations = [
        # ensure all books gets assigned an editorial
        migrations.RunPython(
            code=ensure_all_books_have_editorial,
            reverse_code=migrations.RunPython.noop # this operation shouldn't be reverted
        ),
        # set editorial field to non null
        migrations.AlterField(
            model_name='Book',
            name='editorial',
            field=models.ForeignKey(to='bookstore.editorial', on_delete=models.CASCADE)
        ),
        # remove old fields
        migrations.RemoveField(
            model_name='book',
            name='editorial_name'
        ),
        migrations.RemoveField(
            model_name='book',
            name='editorial_address'
        )
    ]
```
