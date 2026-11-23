from django.conf import settings
from django.db import models


class OwnedModel(models.Model):
    """Abstract base: every record is linked to the user who created it."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True


class Genre(OwnedModel):
    name = models.CharField("Name", max_length=100)
    description = models.TextField("Description", blank=True, default="")

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Author(OwnedModel):
    name = models.CharField("Full name", max_length=200)
    country = models.CharField("Country", max_length=100, blank=True, default="")
    birth_year = models.PositiveSmallIntegerField("Birth year", null=True, blank=True)
    photo = models.ImageField("Photo", null=True, blank=True, upload_to="authors")

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(OwnedModel):
    title = models.CharField("Title", max_length=255)
    author = models.ForeignKey(
        Author,
        verbose_name="Author",
        on_delete=models.CASCADE,
        related_name="books",
    )
    genre = models.ForeignKey(
        Genre,
        verbose_name="Genre",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    price = models.DecimalField("Price", max_digits=8, decimal_places=2, default=0)
    pages = models.PositiveIntegerField("Pages", default=0)
    published_year = models.PositiveSmallIntegerField("Year published", null=True, blank=True)
    in_stock = models.BooleanField("In stock", default=True)
    cover = models.ImageField("Cover", null=True, blank=True, upload_to="covers")

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ["title"]

    def __str__(self):
        return self.title


class BookPhoto(OwnedModel):
    """Extra photos of a book – together they form the book's photo album."""

    book = models.ForeignKey(
        Book,
        verbose_name="Book",
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField("Image", upload_to="albums")
    caption = models.CharField("Caption", max_length=200, blank=True, default="")

    class Meta:
        verbose_name = "Book photo"
        verbose_name_plural = "Book photos"
        ordering = ["id"]

    def __str__(self):
        return f"{self.book} #{self.pk}"


class Order(OwnedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"

    book = models.ForeignKey(
        Book,
        verbose_name="Book",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    customer_name = models.CharField("Customer", max_length=200)
    quantity = models.PositiveIntegerField("Quantity", default=1)
    status = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.NEW
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Order #{self.pk}: {self.customer_name}"
