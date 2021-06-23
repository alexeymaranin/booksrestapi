from django.test import TestCase

from store.models import Book
from store.serializers import BooksSerializer


class BookSerializerTestCase(TestCase):
    def test_ok(self):
        book1 = Book.objects.create(name='Test book1', price=25, author_name='Author 1')
        book2 = Book.objects.create(name='Test book2', price=55, author_name='Author 2')
        data = BooksSerializer([book1, book2], many=True).data
        expected_data = [
            {
                'id': book1.id,
                'name': 'Test book1',
                'price': '25.00',
                'author_name': 'Author 1'
            },
            {
                'id': book2.id,
                'name': 'Test book2',
                'price': '55.00',
                'author_name': 'Author 2'
            },
        ]

        self.assertEqual(expected_data, data)
