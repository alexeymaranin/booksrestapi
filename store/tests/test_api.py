import json

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer


class BooksApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.book1 = Book.objects.create(name='Test book1', price=25, author_name='C Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book2', price=55, author_name='B Author 2')
        self.book3 = Book.objects.create(name='Test book3 about Author 1', price=55, author_name='A Author 3')

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        serializer_data = BooksSerializer([self.book1, self.book2, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        serializer_data = BooksSerializer([self.book1, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_order_price(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'price'})
        serializer_data = BooksSerializer([self.book1, self.book2, self.book3], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_get_order_author(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'author_name'})
        serializer_data = BooksSerializer([self.book3, self.book2, self.book1], many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)

    def test_create(self):
        # проверяем что начальное количество книг равно 3
        self.assertEqual(3, Book.objects.all().count())
        # получаем url
        url = reverse('book-list')
        # создаем данные json которые будем отправлять запросом
        data = {"name": "Programming in Python 3",
                "price": 150,
                "author_name": "Mark Summerfield"}
        # переводим в json
        json_data = json.dumps(data)
        # логиним пользователя чтобы можно было отправлять запросы
        self.client.force_login(self.user)
        # получаем ответ на POST запрос через клиент на определенный url и передаем данные
        response = self.client.post(url, data=json_data, content_type="application/json")
        # проверяем статус коды на равенство
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        # проверяем что количество книг увеличилось на 1
        self.assertEqual(4, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)

    def test_update(self):
        # получаем url и с определенным аргументом (в нашем случаем id)
        url = reverse('book-detail', args=(self.book1.id,))
        # создаем данные json которые будем отправлять запросом
        data = {"name": self.book1.name,
                "price": 575,
                "author_name": self.book1.author_name}
        # переводим в json
        json_data = json.dumps(data)
        # логиним пользователя чтобы можно было отправлять запросы
        self.client.force_login(self.user)
        # получаем ответ на PUT запрос через клиент на определенный url и передаем данные
        response = self.client.put(url, data=json_data, content_type="application/json")
        # проверяем статус коды на равенство
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # обновляем локальную информацию с базы данных просто перезаписав книгу
        self.book1 = Book.objects.get(id=self.book1.id)
        # или так:
        # self.book1.refresh_from_db()
        # проверяем что цена изменилась
        self.assertEqual(575, self.book1.price)

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username_2')
        url = reverse('book-detail', args=(self.book1.id,))
        data = {"name": self.book1.name,
                "price": 575,
                "author_name": self.book1.author_name}
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type="application/json")
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.book1 = Book.objects.get(id=self.book1.id)
        self.assertEqual(25, self.book1.price)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username_2', is_staff=True)
        url = reverse('book-detail', args=(self.book1.id,))
        data = {"name": self.book1.name,
                "price": 575,
                "author_name": self.book1.author_name}
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data, content_type="application/json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book1 = Book.objects.get(id=self.book1.id)
        self.assertEqual(575, self.book1.price)

    def test_delete(self):
        # получаем url и с определенным аргументом (в нашем случаем id)
        url = reverse('book-detail', args=(self.book1.id,))
        # логиним пользователя чтобы можно было отправлять запросы
        self.client.force_login(self.user)
        # получаем ответ на DELETE запрос через клиент на определенный url
        response = self.client.delete(url)
        # проверяем статус коды на равенство
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        # ищем книгу с таким id
        self.book1 = Book.objects.filter(id=self.book1.id).first()
        # проверяем что такой книги в базе данных нету
        self.assertEqual(None, self.book1)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='test_username_2')
        url = reverse('book-detail', args=(self.book1.id,))
        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.book1 = Book.objects.filter(id=self.book1.id).first()
        self.assertEqual(self.book1, self.book1)

    def test_detail(self):
        url = reverse('book-detail', args=(self.book1.id,))
        response = self.client.get(url)
        serializer_data = BooksSerializer(self.book1).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)


class BooksRelationApiTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username2')
        self.book1 = Book.objects.create(name='Test book1', price=25, author_name='C Author 1', owner=self.user)
        self.book2 = Book.objects.create(name='Test book2', price=55, author_name='B Author 2')

    def test_like(self):
        # получаем url с аргументом id книги
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        # передаем что поставили лайк
        data = {
            "like": True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        # патч отличается от пут тем что не надо передавать все поля, а можно только одно
        response = self.client.patch(url, data=json_data, content_type="application/json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # получаем с БД отношение книги и пользователя
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        # проверяем что лайк поставился
        self.assertTrue(relation.like)
        # передаем что добавили в закладки
        data = {
            "in_bookmarks": True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data, content_type="application/json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        # проверяем что добавлено в закладки
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        # получаем url с аргументом id книги
        url = reverse('userbookrelation-detail', args=(self.book1.id,))
        # передаем что поставили лайк
        data = {
            "rate": 3,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        # патч отличается от пут тем что не надо передавать все поля, а можно только одно
        response = self.client.patch(url, data=json_data, content_type="application/json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        # получаем с БД отношение книги и пользователя
        relation = UserBookRelation.objects.get(user=self.user, book=self.book1)
        # проверяем что лайк поставился
        self.assertEqual(3, relation.rate)
