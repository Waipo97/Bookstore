import django_filters as df

from .models import Author, Book, BookPhoto, Genre, Order


class GenreFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains")
    description = df.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Genre
        fields = ["name", "description", "user"]


class AuthorFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains")
    country = df.CharFilter(lookup_expr="icontains")
    birth_year_min = df.NumberFilter(field_name="birth_year", lookup_expr="gte")
    birth_year_max = df.NumberFilter(field_name="birth_year", lookup_expr="lte")

    class Meta:
        model = Author
        fields = ["name", "country", "birth_year", "user"]


class BookFilter(df.FilterSet):
    title = df.CharFilter(lookup_expr="icontains")
    author_name = df.CharFilter(field_name="author__name", lookup_expr="icontains")
    price_min = df.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = df.NumberFilter(field_name="price", lookup_expr="lte")
    pages_min = df.NumberFilter(field_name="pages", lookup_expr="gte")
    pages_max = df.NumberFilter(field_name="pages", lookup_expr="lte")
    year_min = df.NumberFilter(field_name="published_year", lookup_expr="gte")
    year_max = df.NumberFilter(field_name="published_year", lookup_expr="lte")

    class Meta:
        model = Book
        fields = ["title", "author", "genre", "in_stock", "user"]


class BookPhotoFilter(df.FilterSet):
    caption = df.CharFilter(lookup_expr="icontains")
    book_title = df.CharFilter(field_name="book__title", lookup_expr="icontains")

    class Meta:
        model = BookPhoto
        fields = ["book", "caption", "user"]


class OrderFilter(df.FilterSet):
    customer_name = df.CharFilter(lookup_expr="icontains")
    book_title = df.CharFilter(field_name="book__title", lookup_expr="icontains")
    quantity_min = df.NumberFilter(field_name="quantity", lookup_expr="gte")
    quantity_max = df.NumberFilter(field_name="quantity", lookup_expr="lte")
    created_from = df.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = df.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Order
        fields = ["customer_name", "book", "status", "user"]
