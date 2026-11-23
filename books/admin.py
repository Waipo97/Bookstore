from django.contrib import admin

from .models import Author, Book, BookPhoto, Genre, Order


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user")
    search_fields = ("name",)
    list_filter = ("user",)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country", "birth_year", "user")
    search_fields = ("name", "country")
    list_filter = ("country", "user")


class BookPhotoInline(admin.TabularInline):
    model = BookPhoto
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "genre__name", "price", "in_stock", "user")
    list_filter = ("genre", "in_stock", "user")
    search_fields = ("title", "author__name")
    list_select_related = ("author", "genre", "user")
    inlines = [BookPhotoInline]


@admin.register(BookPhoto)
class BookPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "book", "caption", "user")
    list_filter = ("user",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "book", "quantity", "status", "created_at", "user")
    list_filter = ("status", "user")
    search_fields = ("customer_name", "book__title")
    list_select_related = ("book", "user")
