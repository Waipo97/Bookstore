import random
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from PIL import Image

from books.models import Author, Book, BookPhoto, Genre, Order

GENRES = [
    "Fantasy", "Science Fiction", "Mystery", "Thriller", "Romance", "Historical Fiction",
    "Horror", "Biography", "Autobiography", "History", "Science", "Philosophy", "Poetry",
    "Drama", "Adventure", "Children's", "Young Adult", "Self-Help", "Business", "Cooking",
    "Travel", "Art", "Religion", "Psychology", "Computing", "Mathematics", "Humor",
    "Classics", "Graphic Novel", "True Crime",
]


def fake_image(color, size=(240, 320)):
    """A small solid-colour PNG so no external files are needed."""
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Fill the database with random data (>= 1000 rows in the main tables)."

    def add_arguments(self, parser):
        parser.add_argument("--user", help="username that will own the data (default: first superuser)")
        parser.add_argument("--authors", type=int, default=1000)
        parser.add_argument("--books", type=int, default=1500)
        parser.add_argument("--orders", type=int, default=2000)
        parser.add_argument("--photos", type=int, default=1000)
        parser.add_argument("--covers", type=int, default=50,
                            help="how many books get a generated cover image")

    def handle(self, *args, **opts):
        User = get_user_model()
        if opts["user"]:
            user = User.objects.filter(username=opts["user"]).first()
        else:
            user = User.objects.filter(is_superuser=True).first()
        if user is None:
            raise CommandError("User not found. Create one with `python manage.py createsuperuser`.")

        fake = Faker("en_US")
        rnd = random.Random()

        genres = Genre.objects.bulk_create(
            [Genre(name=name, description=fake.sentence(), user=user) for name in GENRES]
        )

        authors = Author.objects.bulk_create(
            [
                Author(
                    name=fake.name(),
                    country=fake.country(),
                    birth_year=rnd.randint(1850, 2000),
                    user=user,
                )
                for _ in range(opts["authors"])
            ]
        )

        books = Book.objects.bulk_create(
            [
                Book(
                    title=fake.catch_phrase().title(),
                    author=rnd.choice(authors),
                    genre=rnd.choice(genres),
                    price=round(rnd.uniform(3, 90), 2),
                    pages=rnd.randint(40, 1200),
                    published_year=rnd.randint(1900, 2025),
                    in_stock=rnd.random() > 0.15,
                    user=user,
                )
                for _ in range(opts["books"])
            ]
        )

        for book in rnd.sample(books, min(opts["covers"], len(books))):
            book.cover.save(f"cover_{book.pk}.png", fake_image(fake.color()), save=True)

        photos = []
        for i in range(opts["photos"]):
            photo = BookPhoto(book=rnd.choice(books), caption=fake.sentence(nb_words=4), user=user)
            photo.image.save(f"photo_{i}.png", fake_image(fake.color(), (160, 120)), save=False)
            photos.append(photo)
        BookPhoto.objects.bulk_create(photos)

        Order.objects.bulk_create(
            [
                Order(
                    book=rnd.choice(books),
                    customer_name=fake.name(),
                    quantity=rnd.randint(1, 5),
                    status=rnd.choice(Order.Status.values),
                    user=user,
                )
                for _ in range(opts["orders"])
            ]
        )

        self.stdout.write(self.style.SUCCESS(
            f"Created for '{user.username}': {len(genres)} genres, {len(authors)} authors, "
            f"{len(books)} books, {len(photos)} book photos, {opts['orders']} orders."
        ))
