from datetime import datetime
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.models import User
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Max, Min, Q, Sum
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .filters import AuthorFilter, BookFilter, BookPhotoFilter, GenreFilter, OrderFilter
from .models import Author, Book, BookPhoto, Genre, Order
from .serializers import (
    AuthorSerializer,
    BookPhotoSerializer,
    BookSerializer,
    GenreSerializer,
    OrderSerializer,
    UserSerializer,
)


def num(value):
    """Aggregate results -> JSON friendly numbers (None -> 0)."""
    if value is None:
        return 0
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float):
        return round(value, 2)
    return value


def clean(value):
    """Convert a DB value to something openpyxl can write."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return value


class OwnedViewSet(viewsets.ModelViewSet):
    """
    Full CRUD + `stats` and `export` actions.

    * normal users only see rows they created;
    * superusers see everything and can narrow it with ?user=<id>.
    """

    search_fields = ()
    # [(column title, ORM lookup), ...] for the Excel export
    export_columns = ()
    export_name = "export"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            qs = qs.filter(user=user)
        return qs

    # ---- statistics -------------------------------------------------
    def build_stats(self, qs):
        return {"total": qs.count()}

    @action(detail=False, methods=["get"])
    def stats(self, request):
        # statistics follow the filters currently applied to the table
        qs = self.filter_queryset(self.get_queryset())
        return Response(self.build_stats(qs))

    # ---- Excel export -----------------------------------------------
    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = self.filter_queryset(self.get_queryset())
        headers = [title for title, _ in self.export_columns]
        lookups = [lookup for _, lookup in self.export_columns]

        wb = Workbook()
        ws = wb.active
        ws.title = self.export_name.capitalize()
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for row in qs.order_by("id").values_list(*lookups):
            ws.append([clean(v) for v in row])
        for column in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in column)
            ws.column_dimensions[column[0].column_letter].width = min(width + 2, 60)

        buffer = BytesIO()
        wb.save(buffer)
        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{self.export_name}.xlsx"'
        return response


class GenreViewSet(OwnedViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filterset_class = GenreFilter
    search_fields = ("name", "description")
    export_name = "genres"
    export_columns = (("ID", "id"), ("Name", "name"), ("Description", "description"),
                      ("User", "user__username"))

    def build_stats(self, qs):
        per_genre = qs.annotate(n=Count("books"))
        agg = per_genre.aggregate(total=Count("id"), books=Sum("n"), avg=Avg("n"), most=Max("n"))
        top = per_genre.order_by("-n", "name").values("id", "name", "n")[:5]
        return {
            "total": agg["total"],
            "books_total": num(agg["books"]),
            "avg_books_per_genre": num(agg["avg"]),
            "max_books_in_genre": num(agg["most"]),
            "top_genres": [{"name": g["name"], "books": g["n"]} for g in top],
        }


class AuthorViewSet(OwnedViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filterset_class = AuthorFilter
    search_fields = ("name", "country")
    export_name = "authors"
    export_columns = (("ID", "id"), ("Full name", "name"), ("Country", "country"),
                      ("Birth year", "birth_year"), ("User", "user__username"))

    def build_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            countries=Count("country", distinct=True, filter=~Q(country="")),
            avg_birth_year=Avg("birth_year"),
            oldest=Min("birth_year"),
            youngest=Max("birth_year"),
        )
        top = (qs.exclude(country="").values("country")
               .annotate(n=Count("id")).order_by("-n", "country")[:5])
        return {
            "total": agg["total"],
            "countries": agg["countries"],
            "avg_birth_year": num(agg["avg_birth_year"]),
            "oldest_birth_year": num(agg["oldest"]),
            "youngest_birth_year": num(agg["youngest"]),
            "top_countries": [{"country": r["country"], "authors": r["n"]} for r in top],
        }


class BookViewSet(OwnedViewSet):
    queryset = Book.objects.select_related("author", "genre")
    serializer_class = BookSerializer
    filterset_class = BookFilter
    search_fields = ("title", "author__name", "genre__name")
    export_name = "books"
    export_columns = (("ID", "id"), ("Title", "title"), ("Author", "author__name"),
                      ("Genre", "genre__name"), ("Price", "price"), ("Pages", "pages"),
                      ("Year published", "published_year"), ("In stock", "in_stock"),
                      ("User", "user__username"))

    def build_stats(self, qs):
        agg = qs.aggregate(
            total=Count("id"),
            avg_price=Avg("price"),
            min_price=Min("price"),
            max_price=Max("price"),
            total_pages=Sum("pages"),
            avg_pages=Avg("pages"),
            in_stock=Count("id", filter=Q(in_stock=True)),
        )
        by_genre = (qs.values("genre__name").annotate(n=Count("id"), avg_price=Avg("price"))
                    .order_by("-n", "genre__name")[:5])
        return {
            "total": agg["total"],
            "avg_price": num(agg["avg_price"]),
            "min_price": num(agg["min_price"]),
            "max_price": num(agg["max_price"]),
            "total_pages": num(agg["total_pages"]),
            "avg_pages": num(agg["avg_pages"]),
            "in_stock": agg["in_stock"],
            "out_of_stock": agg["total"] - agg["in_stock"],
            "by_genre": [{"genre": r["genre__name"] or "—", "books": r["n"],
                          "avg_price": num(r["avg_price"])} for r in by_genre],
        }


class BookPhotoViewSet(OwnedViewSet):
    queryset = BookPhoto.objects.select_related("book")
    serializer_class = BookPhotoSerializer
    filterset_class = BookPhotoFilter
    search_fields = ("caption", "book__title")
    export_name = "book_photos"
    export_columns = (("ID", "id"), ("Book", "book__title"), ("Caption", "caption"),
                      ("Image", "image"), ("User", "user__username"))

    def build_stats(self, qs):
        agg = qs.aggregate(total=Count("id"), books=Count("book", distinct=True))
        top = (qs.values("book__title").annotate(n=Count("id"))
               .order_by("-n", "book__title")[:5])
        return {
            "total": agg["total"],
            "books_with_photos": agg["books"],
            "avg_photos_per_book": num(agg["total"] / agg["books"]) if agg["books"] else 0,
            "top_books": [{"book": r["book__title"], "photos": r["n"]} for r in top],
        }


class OrderViewSet(OwnedViewSet):
    queryset = Order.objects.select_related("book")
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    search_fields = ("customer_name", "book__title")
    export_name = "orders"
    export_columns = (("ID", "id"), ("Customer", "customer_name"), ("Book", "book__title"),
                      ("Quantity", "quantity"), ("Status", "status"),
                      ("Created at", "created_at"), ("User", "user__username"))

    def build_stats(self, qs):
        line_total = ExpressionWrapper(
            F("quantity") * F("book__price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        agg = qs.aggregate(
            total=Count("id"),
            total_quantity=Sum("quantity"),
            avg_quantity=Avg("quantity"),
            revenue=Sum(line_total, filter=~Q(status=Order.Status.CANCELLED)),
        )
        by_status = qs.values("status").annotate(n=Count("id")).order_by("status")
        return {
            "total": agg["total"],
            "total_quantity": num(agg["total_quantity"]),
            "avg_quantity": num(agg["avg_quantity"]),
            "revenue": num(agg["revenue"]),
            "by_status": [{"status": r["status"], "orders": r["n"]} for r in by_status],
        }


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """User list for the superuser's "filter by user" dropdown."""

    queryset = User.objects.order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = ()
    pagination_class = None
