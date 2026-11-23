from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Author, Book, BookPhoto, Genre, Order


class OwnedSerializer(serializers.ModelSerializer):
    """Fills `user` from the request and stops users linking to other people's rows."""

    # names of relation fields that must belong to the current user
    owned_relations = ()

    def create(self, validated_data):
        # `context['request']` is filled in by DRF when the serializer is built in a view
        if "request" in self.context:
            validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            for name in self.owned_relations:
                obj = attrs.get(name)
                if obj is not None and obj.user_id != request.user.id:
                    raise serializers.ValidationError({name: "Object not found."})
        return super().validate(attrs)


class GenreSerializer(OwnedSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "description", "user"]
        read_only_fields = ["user"]


class AuthorSerializer(OwnedSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "country", "birth_year", "photo", "user"]
        read_only_fields = ["user"]


class BookSerializer(OwnedSerializer):
    owned_relations = ("author", "genre")

    author_name = serializers.CharField(source="author.name", read_only=True)
    genre_name = serializers.CharField(source="genre.name", read_only=True, default=None)
    photos_count = serializers.IntegerField(source="photos.count", read_only=True)

    class Meta:
        model = Book
        fields = [
            "id", "title", "author", "author_name", "genre", "genre_name",
            "price", "pages", "published_year", "in_stock", "cover",
            "photos_count", "user",
        ]
        read_only_fields = ["user"]


class BookPhotoSerializer(OwnedSerializer):
    owned_relations = ("book",)

    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = BookPhoto
        fields = ["id", "book", "book_title", "image", "caption", "user"]
        read_only_fields = ["user"]


class OrderSerializer(OwnedSerializer):
    owned_relations = ("book",)

    book_title = serializers.CharField(source="book.title", read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        return str(obj.quantity * obj.book.price)

    class Meta:
        model = Order
        fields = [
            "id", "book", "book_title", "customer_name", "quantity",
            "status", "total_price", "created_at", "user",
        ]
        read_only_fields = ["user", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]
