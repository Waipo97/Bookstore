from io import BytesIO, StringIO

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from openpyxl import load_workbook
from PIL import Image
from rest_framework.test import APIClient

from .models import Author, Book, BookPhoto, Genre, Order


def image_file(name="pic.png", color="red"):
    buf = BytesIO()
    Image.new("RGB", (20, 20), color).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def ids(rows):
    return {row["id"] for row in rows}


# ---------------------------------------------------------------------------
# Generic CRUD tests – every viewset class below inherits all of them.
# ---------------------------------------------------------------------------
class CRUDTests:
    url = None
    model = None

    def make(self, user, **kwargs):
        """Create one or more rows owned by `user`."""
        return baker.make(self.model, user=user, **kwargs)

    def create_payload(self, user):
        raise NotImplementedError

    def update_payload(self, user, obj):
        raise NotImplementedError

    def check_updated(self, obj, payload):
        for key, value in payload.items():
            assert str(getattr(obj, key)) == str(value)

    # ---- list -----------------------------------------------------------
    @pytest.mark.django_db
    def test_list(self, api, user):
        objs = self.make(user, _quantity=10)
        response = api.get(self.url)
        assert response.status_code == 200
        assert response.data["count"] == 10
        assert ids(response.data["results"]) == {o.id for o in objs}

    @pytest.mark.django_db
    def test_retrieve(self, api, user):
        obj = self.make(user)
        response = api.get(f"{self.url}{obj.id}/")
        assert response.status_code == 200
        assert response.data["id"] == obj.id

    # ---- create ---------------------------------------------------------
    @pytest.mark.django_db
    def test_create(self, api, user):
        payload = self.create_payload(user)
        before = self.model.objects.count()
        response = api.post(self.url, payload, format="json")
        assert response.status_code == 201, response.data
        assert self.model.objects.count() == before + 1
        created = self.model.objects.get(id=response.data["id"])
        self.check_updated(created, payload)
        assert created.user == user  # filled in from the request

    @pytest.mark.django_db
    def test_create_ignores_user_from_body(self, api, user, other_user):
        payload = {**self.create_payload(user), "user": other_user.id}
        response = api.post(self.url, payload, format="json")
        assert response.status_code == 201, response.data
        assert self.model.objects.get(id=response.data["id"]).user == user

    # ---- update ---------------------------------------------------------
    @pytest.mark.django_db
    def test_update(self, api, user):
        obj = self.make(user)
        payload = self.update_payload(user, obj)
        response = api.put(f"{self.url}{obj.id}/", payload, format="json")
        assert response.status_code == 200, response.data
        obj.refresh_from_db()  # reload from the DB and compare with what was sent
        self.check_updated(obj, payload)

    @pytest.mark.django_db
    def test_partial_update(self, api, user):
        obj = self.make(user)
        payload = self.update_payload(user, obj)
        key = next(iter(payload))
        response = api.patch(f"{self.url}{obj.id}/", {key: payload[key]}, format="json")
        assert response.status_code == 200, response.data
        obj.refresh_from_db()
        self.check_updated(obj, {key: payload[key]})

    # ---- delete ---------------------------------------------------------
    @pytest.mark.django_db
    def test_delete(self, api, user):
        objs = self.make(user, _quantity=10)
        victim = objs[0]
        assert self.model.objects.count() == 10
        response = api.delete(f"{self.url}{victim.id}/")
        assert response.status_code == 204
        assert not self.model.objects.filter(id=victim.id).exists()
        listing = api.get(self.url)
        assert victim.id not in ids(listing.data["results"])

    # ---- permissions / ownership ---------------------------------------
    @pytest.mark.django_db
    def test_anonymous_is_rejected(self):
        response = APIClient().get(self.url)
        assert response.status_code in (401, 403)

    @pytest.mark.django_db
    def test_user_sees_only_own_rows(self, api, user, other_user):
        mine = self.make(user, _quantity=3)
        theirs = self.make(other_user, _quantity=2)
        response = api.get(self.url)
        assert ids(response.data["results"]) == {o.id for o in mine}
        assert api.get(f"{self.url}{theirs[0].id}/").status_code == 404
        assert api.delete(f"{self.url}{theirs[0].id}/").status_code == 404
        assert self.model.objects.filter(id=theirs[0].id).exists()

    @pytest.mark.django_db
    def test_superuser_sees_all_and_can_filter_by_user(self, super_api, user, other_user):
        mine = self.make(user, _quantity=3)
        theirs = self.make(other_user, _quantity=2)
        everything = super_api.get(self.url)
        assert everything.data["count"] == 5
        only_theirs = super_api.get(self.url, {"user": other_user.id})
        assert ids(only_theirs.data["results"]) == {o.id for o in theirs}
        only_mine = super_api.get(self.url, {"user": user.id})
        assert ids(only_mine.data["results"]) == {o.id for o in mine}

    # ---- statistics & export -------------------------------------------
    @pytest.mark.django_db
    def test_stats(self, api, user, other_user):
        self.make(user, _quantity=4)
        self.make(other_user, _quantity=3)
        response = api.get(f"{self.url}stats/")
        assert response.status_code == 200
        assert response.data["total"] == 4

    @pytest.mark.django_db
    def test_export_to_excel(self, api, user):
        self.make(user, _quantity=5)
        response = api.get(f"{self.url}export/")
        assert response.status_code == 200
        assert "spreadsheetml" in response["Content-Type"]
        assert "attachment" in response["Content-Disposition"]
        sheet = load_workbook(BytesIO(response.content)).active
        assert sheet.max_row == 6  # header + 5 rows


# ---------------------------------------------------------------------------
# One class per viewset
# ---------------------------------------------------------------------------
class TestGenreViewSet(CRUDTests):
    url = "/api/genres/"
    model = Genre

    def create_payload(self, user):
        return {"name": "Fantasy", "description": "Dragons and swords"}

    def update_payload(self, user, obj):
        return {"name": "Sci-Fi", "description": "Spaceships"}

    @pytest.mark.django_db
    def test_filter_by_name(self, api, user):
        baker.make(Genre, user=user, name="Science Fiction")
        baker.make(Genre, user=user, name="Cooking")
        response = api.get(self.url, {"name": "fiction"})
        assert [g["name"] for g in response.data["results"]] == ["Science Fiction"]

    @pytest.mark.django_db
    def test_stats_values(self, api, user):
        genre = baker.make(Genre, user=user)
        baker.make(Genre, user=user)
        baker.make(Book, user=user, genre=genre, _quantity=3)
        stats = api.get(f"{self.url}stats/").data
        assert stats["total"] == 2
        assert stats["books_total"] == 3
        assert stats["max_books_in_genre"] == 3
        assert stats["top_genres"][0]["books"] == 3


class TestAuthorViewSet(CRUDTests):
    url = "/api/authors/"
    model = Author

    def create_payload(self, user):
        return {"name": "Leo Tolstoy", "country": "Russia", "birth_year": 1828}

    def update_payload(self, user, obj):
        return {"name": "Fyodor Dostoevsky", "country": "Russia", "birth_year": 1821}

    @pytest.mark.django_db
    def test_filters(self, api, user):
        baker.make(Author, user=user, name="Old", country="France", birth_year=1800)
        baker.make(Author, user=user, name="New", country="Russia", birth_year=1980)
        assert api.get(self.url, {"country": "rus"}).data["count"] == 1
        assert api.get(self.url, {"birth_year_min": 1900}).data["results"][0]["name"] == "New"
        assert api.get(self.url, {"birth_year_max": 1900}).data["results"][0]["name"] == "Old"

    @pytest.mark.django_db
    def test_stats_values(self, api, user):
        baker.make(Author, user=user, country="Russia", birth_year=1800)
        baker.make(Author, user=user, country="Russia", birth_year=1900)
        baker.make(Author, user=user, country="France", birth_year=1850)
        stats = api.get(f"{self.url}stats/").data
        assert stats["total"] == 3
        assert stats["countries"] == 2
        assert stats["avg_birth_year"] == 1850
        assert stats["oldest_birth_year"] == 1800
        assert stats["top_countries"][0] == {"country": "Russia", "authors": 2}

    @pytest.mark.django_db
    def test_upload_and_change_photo(self, api, user):
        response = api.post(self.url, {"name": "With photo", "photo": image_file("a.png")},
                            format="multipart")
        assert response.status_code == 201, response.data
        author = Author.objects.get(id=response.data["id"])
        assert author.photo.name.startswith("authors/")
        first = author.photo.name
        response = api.patch(f"{self.url}{author.id}/", {"photo": image_file("b.png", "blue")},
                             format="multipart")
        assert response.status_code == 200
        author.refresh_from_db()
        assert author.photo.name != first
        assert response.data["photo"].endswith(author.photo.name)


class TestBookViewSet(CRUDTests):
    url = "/api/books/"
    model = Book

    def make(self, user, **kwargs):
        # a book needs an author; give it one owned by the same user
        if "author" not in kwargs:
            kwargs["author"] = baker.make(Author, user=user)
        return super().make(user, **kwargs)

    def create_payload(self, user):
        return {
            "title": "War and Peace",
            "author": baker.make(Author, user=user).id,
            "genre": baker.make(Genre, user=user).id,
            "price": "19.99",
            "pages": 1225,
            "published_year": 1869,
            "in_stock": True,
        }

    def update_payload(self, user, obj):
        return {
            "title": "Anna Karenina",
            "author": baker.make(Author, user=user).id,
            "genre": baker.make(Genre, user=user).id,
            "price": "12.50",
            "pages": 864,
            "published_year": 1877,
            "in_stock": False,
        }

    def check_updated(self, obj, payload):
        for key, value in payload.items():
            if key in ("author", "genre"):
                assert getattr(obj, f"{key}_id") == value
            elif key == "price":
                assert float(obj.price) == float(value)
            else:
                assert getattr(obj, key) == value

    @pytest.mark.django_db
    def test_response_has_related_names(self, api, user):
        book = self.make(user, author=baker.make(Author, user=user, name="Pushkin"),
                         genre=baker.make(Genre, user=user, name="Poetry"))
        data = api.get(f"{self.url}{book.id}/").data
        assert data["author_name"] == "Pushkin"
        assert data["genre_name"] == "Poetry"

    @pytest.mark.django_db
    def test_cannot_link_to_other_users_author(self, api, user, other_user):
        foreign = baker.make(Author, user=other_user)
        payload = {**self.create_payload(user), "author": foreign.id}
        response = api.post(self.url, payload, format="json")
        assert response.status_code == 400
        assert "author" in response.data

    @pytest.mark.django_db
    def test_deleting_author_deletes_books(self, api, user):
        book = self.make(user)
        book.author.delete()
        assert not Book.objects.filter(id=book.id).exists()

    @pytest.mark.django_db
    def test_filters(self, api, user):
        author = baker.make(Author, user=user, name="Gogol")
        genre = baker.make(Genre, user=user)
        cheap = baker.make(Book, user=user, author=author, genre=genre, price=5, pages=100,
                           published_year=1900, in_stock=True, title="Cheap one")
        dear = baker.make(Book, user=user, author=baker.make(Author, user=user), price=50,
                          pages=900, published_year=2000, in_stock=False, title="Dear one")
        check = lambda params, expected: ids(api.get(self.url, params).data["results"]) == {  # noqa
            b.id for b in expected}
        assert check({"title": "cheap"}, [cheap])
        assert check({"author_name": "gog"}, [cheap])
        assert check({"author": dear.author_id}, [dear])
        assert check({"genre": genre.id}, [cheap])
        assert check({"price_min": 10}, [dear])
        assert check({"price_max": 10}, [cheap])
        assert check({"pages_min": 500}, [dear])
        assert check({"pages_max": 500}, [cheap])
        assert check({"year_min": 1950}, [dear])
        assert check({"year_max": 1950}, [cheap])
        assert check({"in_stock": "false"}, [dear])

    @pytest.mark.django_db
    def test_stats_values(self, api, user):
        baker.make(Book, user=user, author=baker.make(Author, user=user), price=10, pages=100,
                   in_stock=True)
        baker.make(Book, user=user, author=baker.make(Author, user=user), price=30, pages=300,
                   in_stock=False)
        stats = api.get(f"{self.url}stats/").data
        assert stats["total"] == 2
        assert stats["avg_price"] == 20
        assert stats["min_price"] == 10
        assert stats["max_price"] == 30
        assert stats["total_pages"] == 400
        assert stats["in_stock"] == 1
        assert stats["out_of_stock"] == 1

    @pytest.mark.django_db
    def test_stats_follow_filters(self, api, user):
        self.make(user, price=10)
        self.make(user, price=100)
        assert api.get(f"{self.url}stats/", {"price_min": 50}).data["total"] == 1

    @pytest.mark.django_db
    def test_upload_and_change_cover(self, api, user):
        payload = {**self.create_payload(user), "cover": image_file("c.png")}
        response = api.post(self.url, payload, format="multipart")
        assert response.status_code == 201, response.data
        book = Book.objects.get(id=response.data["id"])
        assert book.cover.name.startswith("covers/")
        first = book.cover.name
        response = api.patch(f"{self.url}{book.id}/", {"cover": image_file("d.png", "green")},
                             format="multipart")
        assert response.status_code == 200
        book.refresh_from_db()
        assert book.cover.name != first


class TestBookPhotoViewSet(CRUDTests):
    url = "/api/book-photos/"
    model = BookPhoto

    def make(self, user, **kwargs):
        if "book" not in kwargs:
            kwargs["book"] = baker.make(Book, user=user, author=baker.make(Author, user=user))
        return super().make(user, **kwargs)

    def _book(self, user):
        return baker.make(Book, user=user, author=baker.make(Author, user=user))

    def create_payload(self, user):
        # JSON can't carry a file, so the album is filled through multipart in test_create
        raise NotImplementedError

    def update_payload(self, user, obj):
        return {"caption": "New caption"}

    # `image` is required, so creation goes through multipart
    @pytest.mark.django_db
    def test_create(self, api, user):
        book = self._book(user)
        response = api.post(self.url, {"book": book.id, "caption": "Back side",
                                       "image": image_file()}, format="multipart")
        assert response.status_code == 201, response.data
        photo = BookPhoto.objects.get(id=response.data["id"])
        assert photo.book == book and photo.caption == "Back side"
        assert photo.image.name.startswith("albums/")
        assert photo.user == user

    @pytest.mark.django_db
    def test_create_ignores_user_from_body(self, api, user, other_user):
        book = self._book(user)
        response = api.post(self.url, {"book": book.id, "image": image_file(),
                                       "user": other_user.id}, format="multipart")
        assert response.status_code == 201, response.data
        assert BookPhoto.objects.get(id=response.data["id"]).user == user

    @pytest.mark.django_db
    def test_update(self, api, user):
        photo = self.make(user)
        response = api.put(f"{self.url}{photo.id}/",
                           {"book": photo.book_id, "caption": "Edited", "image": image_file()},
                           format="multipart")
        assert response.status_code == 200, response.data
        photo.refresh_from_db()
        assert photo.caption == "Edited"

    @pytest.mark.django_db
    def test_album_of_one_book(self, api, user):
        book = self._book(user)
        other_book = self._book(user)
        for _ in range(3):
            api.post(self.url, {"book": book.id, "image": image_file()}, format="multipart")
        api.post(self.url, {"book": other_book.id, "image": image_file()}, format="multipart")
        album = api.get(self.url, {"book": book.id})
        assert album.data["count"] == 3
        assert api.get(f"/api/books/{book.id}/").data["photos_count"] == 3

    @pytest.mark.django_db
    def test_cannot_add_photo_to_other_users_book(self, api, user, other_user):
        foreign = baker.make(Book, user=other_user, author=baker.make(Author, user=other_user))
        response = api.post(self.url, {"book": foreign.id, "image": image_file()},
                            format="multipart")
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_stats_values(self, api, user):
        book = self._book(user)
        baker.make(BookPhoto, user=user, book=book, _quantity=3)
        baker.make(BookPhoto, user=user, book=self._book(user))
        stats = api.get(f"{self.url}stats/").data
        assert stats["total"] == 4
        assert stats["books_with_photos"] == 2
        assert stats["avg_photos_per_book"] == 2
        assert stats["top_books"][0]["photos"] == 3


class TestOrderViewSet(CRUDTests):
    url = "/api/orders/"
    model = Order

    def make(self, user, **kwargs):
        if "book" not in kwargs:
            kwargs["book"] = baker.make(Book, user=user, author=baker.make(Author, user=user))
        return super().make(user, **kwargs)

    def create_payload(self, user):
        book = baker.make(Book, user=user, author=baker.make(Author, user=user))
        return {"book": book.id, "customer_name": "Ivan Petrov", "quantity": 2, "status": "new"}

    def update_payload(self, user, obj):
        return {"book": obj.book_id, "customer_name": "Anna Smirnova", "quantity": 5,
                "status": "paid"}

    def check_updated(self, obj, payload):
        for key, value in payload.items():
            if key == "book":
                assert obj.book_id == value
            else:
                assert getattr(obj, key) == value

    @pytest.mark.django_db
    def test_total_price(self, api, user):
        book = baker.make(Book, user=user, author=baker.make(Author, user=user), price="9.50")
        order = baker.make(Order, user=user, book=book, quantity=4)
        data = api.get(f"{self.url}{order.id}/").data
        assert float(data["total_price"]) == 38.0
        assert data["book_title"] == book.title

    @pytest.mark.django_db
    def test_invalid_status_rejected(self, api, user):
        payload = {**self.create_payload(user), "status": "teleported"}
        assert api.post(self.url, payload, format="json").status_code == 400

    @pytest.mark.django_db
    def test_filters(self, api, user):
        book = baker.make(Book, user=user, author=baker.make(Author, user=user), title="Dune")
        a = baker.make(Order, user=user, book=book, customer_name="Alice", quantity=1, status="new")
        b = baker.make(Order, user=user, book=self._other_book(user), customer_name="Bob",
                       quantity=5, status="paid")
        check = lambda params, expected: ids(api.get(self.url, params).data["results"]) == {  # noqa
            o.id for o in expected}
        assert check({"customer_name": "ali"}, [a])
        assert check({"book_title": "dun"}, [a])
        assert check({"book": b.book_id}, [b])
        assert check({"status": "paid"}, [b])
        assert check({"quantity_min": 3}, [b])
        assert check({"quantity_max": 3}, [a])
        assert check({"created_from": "2999-01-01"}, [])
        assert check({"created_to": "2999-01-01"}, [a, b])

    def _other_book(self, user):
        return baker.make(Book, user=user, author=baker.make(Author, user=user))

    @pytest.mark.django_db
    def test_stats_values(self, api, user):
        book = baker.make(Book, user=user, author=baker.make(Author, user=user), price=10)
        baker.make(Order, user=user, book=book, quantity=3, status="paid")
        baker.make(Order, user=user, book=book, quantity=1, status="new")
        baker.make(Order, user=user, book=book, quantity=5, status="cancelled")  # not revenue
        stats = api.get(f"{self.url}stats/").data
        assert stats["total"] == 3
        assert stats["total_quantity"] == 9
        assert stats["revenue"] == 40
        assert {s["status"]: s["orders"] for s in stats["by_status"]} == {
            "paid": 1, "new": 1, "cancelled": 1}


# ---------------------------------------------------------------------------
# Authorisation endpoints used by the Vue login page
# ---------------------------------------------------------------------------
class TestAuth:
    @pytest.mark.django_db
    def test_me_anonymous(self):
        response = APIClient().get("/api/auth/me/")
        assert response.status_code == 200
        assert response.data == {"is_authenticated": False}
        assert "csrftoken" in response.cookies

    @pytest.mark.django_db
    def test_login_logout(self):
        User.objects.create_user("ann", password="s3cret-pass")
        client = APIClient()
        bad = client.post("/api/auth/login/", {"username": "ann", "password": "nope"})
        assert bad.status_code == 400
        ok = client.post("/api/auth/login/", {"username": "ann", "password": "s3cret-pass"})
        assert ok.status_code == 200
        assert ok.data["username"] == "ann" and ok.data["is_authenticated"]
        assert client.get("/api/auth/me/").data["username"] == "ann"
        assert client.get("/api/books/").status_code == 200
        assert client.post("/api/auth/logout/").status_code == 204
        assert client.get("/api/auth/me/").data["is_authenticated"] is False
        assert client.get("/api/books/").status_code in (401, 403)

    @pytest.mark.django_db
    def test_register(self):
        client = APIClient()
        response = client.post("/api/auth/register/", {"username": "newbie",
                                                       "password": "Str0ng-pass-123"})
        assert response.status_code == 201
        assert User.objects.filter(username="newbie").exists()
        assert client.get("/api/auth/me/").data["username"] == "newbie"
        dup = client.post("/api/auth/register/", {"username": "newbie", "password": "Str0ng-pass-123"})
        assert dup.status_code == 400
        weak = client.post("/api/auth/register/", {"username": "x", "password": "123"})
        assert weak.status_code == 400


class TestUserViewSet:
    @pytest.mark.django_db
    def test_superuser_can_list_users(self, super_api, user, other_user):
        response = super_api.get("/api/users/")
        assert response.status_code == 200
        assert {u["username"] for u in response.data} >= {"reader", "stranger", "boss"}

    @pytest.mark.django_db
    def test_normal_user_cannot_list_users(self, api):
        assert api.get("/api/users/").status_code == 403

    @pytest.mark.django_db
    def test_book_photo_filter_by_book_title(self, api, user):
        book = baker.make(Book, user=user, author=baker.make(Author, user=user), title="Dune")
        baker.make(BookPhoto, user=user, book=book)
        baker.make(BookPhoto, user=user, book=baker.make(Book, user=user, title="Emma",
                                                          author=baker.make(Author, user=user)))
        assert api.get("/api/book-photos/", {"book_title": "dun"}).data["count"] == 1


# ---------------------------------------------------------------------------
# Data generation command
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_generate_data_command(user):
    from django.core.management import call_command

    call_command("generate_data", user=user.username, authors=1000, books=1000, orders=1000,
                 photos=10, covers=2, stdout=StringIO())
    assert Author.objects.filter(user=user).count() >= 1000
    assert Book.objects.filter(user=user).count() >= 1000
    assert Order.objects.filter(user=user).count() >= 1000
    assert Genre.objects.filter(user=user).exists()
