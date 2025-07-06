import io
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from chat.models import ChatRoom
from users.match import (
    find_and_notify_matches,
    generate_match_data,
    get_potential_matches,
    hamming_distance,
)
from users.models import Brand, Category, Color, Item, ItemImage, Location, UserProfile
from users.tasks import (
    delete_old_items_and_chats,
    find_and_notify_matches_task,
    remove_images_from_item,
    send_match_notification,
    send_welcome_email,
    upload_images_to_cloudinary,
)


def clean_up(self):
    Category.objects.all().delete()
    Location.objects.all().delete()
    Color.objects.all().delete()
    Brand.objects.all().delete()
    Item.objects.all().delete()
    UserProfile.objects.all().delete()
    ChatRoom.objects.all().delete()


class SendMatchNotificationTests(TestCase):
    @patch("users.tasks.send_mail")
    @patch("users.tasks.render_to_string")
    def test_send_match_notification_success(self, mock_render, mock_send_mail):
        mock_render.return_value = "<p>Match found for Notebook</p>"
        to_email = "destinatario@example.com"
        item_name = "Notebook"
        matches = ["match1", "match2"]

        send_match_notification(to_email, item_name, matches)

        subject_expected = f"Possíveis matches para o seu item perdido: {item_name}"
        plain_expected = "Match found for Notebook"
        mock_send_mail.assert_called_once_with(
            subject_expected,
            plain_expected,
            "acheiunb2024@gmail.com",
            [to_email],
            html_message=mock_render.return_value,
        )


class SendWelcomeEmailTests(TestCase):
    @patch("users.tasks.send_mail")
    @patch("users.tasks.render_to_string")
    def test_send_welcome_email_success(self, mock_render, mock_send_mail):
        mock_render.return_value = "<p>Bem-vindo, João!</p>"
        user_email = "joao@example.com"
        user_name = "João"

        send_welcome_email(user_email, user_name)

        subject_expected = "Bem-vindo ao AcheiUnB!"
        plain_expected = "Bem-vindo, João!"

        mock_send_mail.assert_called_once_with(
            subject_expected,
            plain_expected,
            "acheiunb2024@gmail.com",
            [user_email],
            html_message=mock_render.return_value,
        )

    @patch("users.tasks.render_to_string", side_effect=Exception("Falha no template"))
    @patch("builtins.print")
    def test_send_welcome_email_exception(self, mock_print, mock_render):
        send_welcome_email("any@example.com", "Qualquer")
        mock_print.assert_called()


class FindAndNotifyMatchesTaskTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Dummy Item")

    @patch("users.match.find_and_notify_matches")
    def test_find_and_notify_matches_success(self, mock_find):
        find_and_notify_matches_task(self.item.id, max_distance=3)
        mock_find.assert_called_once_with(self.item, 3)

    def test_find_and_notify_matches_item_not_found(self):
        result = find_and_notify_matches_task(99999)
        assert result is None


class UploadImagesToCloudinaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )
        self.item = Item.objects.create(name="Item Test", user=self.user)

        if not UserProfile.objects.filter(user=self.user).exists():
            self.user_profile = UserProfile.objects.create(user=self.user)
        else:
            self.user_profile = UserProfile.objects.get(user=self.user)

    @patch("users.tasks.cloudinary.uploader.upload")
    def test_upload_images_to_cloudinary_item_success(self, mock_upload):
        mock_upload.return_value = {"secure_url": "http://dummy.com/image.jpg"}
        images = [io.BytesIO(b"dummy image data")]
        upload_images_to_cloudinary(self.item.id, images, object_type="item")
        assert ItemImage.objects.filter(
            item=self.item, image_url="http://dummy.com/image.jpg"
        ).exists()

    @patch("users.tasks.cloudinary.uploader.upload")
    def test_upload_images_to_cloudinary_user_success(self, mock_upload):
        mock_upload.return_value = {"secure_url": "http://dummy.com/user.jpg"}
        images = [io.BytesIO(b"user image")]
        upload_images_to_cloudinary(self.user_profile.id, images, object_type="user")
        self.user_profile.refresh_from_db()
        assert self.user_profile.profile_picture == "http://dummy.com/user.jpg"

    def test_upload_images_unknown_object_type(self):
        images = [io.BytesIO(b"dummy")]
        result = upload_images_to_cloudinary(1, images, object_type="unknown")
        assert result is None

    @patch("users.tasks.cloudinary.uploader.upload", side_effect=Exception("Upload error"))
    @patch("builtins.print")
    def test_upload_images_to_cloudinary_exception(self, mock_print, mock_upload):
        images = [io.BytesIO(b"dummy")]
        upload_images_to_cloudinary(self.item.id, images, object_type="item")
        mock_print.assert_called()


class RemoveImagesFromItemTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Item to remove images")
        self.image1 = ItemImage.objects.create(
            item=self.item, image_url="http://dummy.com/1.jpg"
        )
        self.image2 = ItemImage.objects.create(
            item=self.item, image_url="http://dummy.com/2.jpg"
        )

    def test_remove_images_from_item_success(self):
        remove_images_from_item([self.image1.id, self.image2.id])
        assert not ItemImage.objects.filter(id__in=[self.image1.id, self.image2.id]).exists()

    @patch("users.tasks.ItemImage.objects.filter")
    @patch("builtins.print")
    def test_remove_images_from_item_exception(self, mock_print, mock_filter):
        mock_filter.side_effect = Exception("Delete error")
        remove_images_from_item([self.image1.id])
        mock_print.assert_called()


class DeleteOldItemsAndChatsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        past_date = now() - timedelta(weeks=3)
        self.old_item = Item.objects.create(name="Old Item", user=self.user)
        Item.objects.filter(id=self.old_item.id).update(created_at=past_date)

        self.new_item = Item.objects.create(name="New Item", user=self.user)

    def test_delete_old_items_and_chats(self):
        result = delete_old_items_and_chats()
        assert "1 itens" in result
        assert not Item.objects.filter(id=self.old_item.id).exists()
        assert Item.objects.filter(id=self.new_item.id).exists()

    def test_delete_old_items_and_chats_no_old_items(self):
        Item.objects.all().delete()
        result = delete_old_items_and_chats()
        assert "0 itens" in result


User = get_user_model()


class MatchTestCase(TestCase):
    def clean_up(self):

        Category.objects.all().delete()
        Location.objects.all().delete()
        Color.objects.all().delete()
        Brand.objects.all().delete()
        Item.objects.all().delete()
        User.objects.all().delete()

    def setUp(self):
        self.clean_up()

        self.user1 = User.objects.create_user(
            username="user1", password="password", email="user1@email.com"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password", email="user2@email.com"
        )

        self.category1 = Category.objects.create(name="Eletrônicos", category_id="01")
        self.category2 = Category.objects.create(name="Roupas", category_id="02")

        self.location1 = Location.objects.create(name="Biblioteca", location_id="01")
        self.location2 = Location.objects.create(name="RU", location_id="02")

        self.color1 = Color.objects.create(name="Preto", color_id="01")
        self.color2 = Color.objects.create(name="Azul", color_id="02")

        self.brand1 = Brand.objects.create(name="Samsung", brand_id="01")
        self.brand2 = Brand.objects.create(name="Apple", brand_id="02")

        self.item_lost = Item.objects.create(
            user=self.user1,
            name="Notebook Perdido",
            category=self.category1,
            location=self.location1,
            color=self.color1,
            brand=self.brand1,
            status="lost",
        )
        self.item_found = Item.objects.create(
            user=self.user2,
            name="Notebook Encontrado",
            category=self.category1,
            location=self.location1,
            color=self.color1,
            brand=self.brand2,
            status="found",
        )

        self.item_lost.save()
        self.item_found.save()

        self.item_irrelevante = Item.objects.create(
            user=self.user2,
            name="Celular Encontrado",
            barcode="11111111",
            category=self.category1,
            location=self.location2,
            color=self.color2,
            brand=self.brand1,
            status="found",
        )

    def test_hamming_distance(self):
        distance = hamming_distance(self.item_lost.barcode, self.item_found.barcode)
        assert distance > 0, f"Esperado > 0, mas recebido {distance}"

    def test_get_potential_matches(self):
        matches = get_potential_matches(
            self.item_lost, opposite_status="found", max_distance=2
        )
        assert self.item_found in matches
        assert self.item_irrelevante not in matches

    def test_generate_match_data(self):
        matches = [self.item_found]
        match_data = generate_match_data(matches)

        expected_data = [
            {
                "id": self.item_found.id,
                "name": "Notebook Encontrado",
                "description": self.item_found.description,
                "location": "Biblioteca",
                "found_lost_date": "Data não especificada",
                "image_url": None,
            }
        ]

        assert match_data == expected_data

    @patch("users.tasks.send_match_notification.delay")
    def test_find_and_notify_matches(self, mock_send_match_notification):
        find_and_notify_matches(self.item_lost, max_distance=2)

        self.item_lost.refresh_from_db()
        assert self.item_found in self.item_lost.matches.all()

        mock_send_match_notification.assert_called_once()
        args, kwargs = mock_send_match_notification.call_args
        assert kwargs["to_email"] == self.item_lost.user.email
        assert kwargs["item_name"] == self.item_lost.name
        assert kwargs["matches"]

    @patch("users.tasks.send_match_notification.delay")
    def test_no_matches(self, mock_send_match_notification):
        find_and_notify_matches(self.item_irrelevante, max_distance=2)

        self.item_irrelevante.refresh_from_db()
        assert self.item_irrelevante.matches.count() == 0

        mock_send_match_notification.assert_not_called()


User = get_user_model()


class MatchNotificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user3",
            email="231026714@aluno.unb.br",
            password="password",
        )

        self.category = Category.objects.create(name="Eletrônicos", category_id="01")
        self.location = Location.objects.create(name="Biblioteca", location_id="01")
        self.color = Color.objects.create(name="Preto", color_id="01")
        self.brand = Brand.objects.create(name="Samsung", brand_id="01")

        self.item_lost = Item.objects.create(
            user=self.user,
            name="Relógio de Ouro Perdido",
            category=self.category,
            location=self.location,
            color=self.color,
            brand=self.brand,
            status="lost",
        )

        self.item_found = Item.objects.create(
            user=self.user,
            name="Relógio de Ouro Encontrado",
            category=self.category,
            location=self.location,
            color=self.color,
            brand=self.brand,
            status="found",
        )


User = get_user_model()


class CleanOldItemsTest(TestCase):
    def setUp(self):

        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")

        self.recent_item = Item.objects.create(
            name="Recent Item",
            user=self.user1,
        )
        self.old_item = Item.objects.create(
            name="Old Item",
            user=self.user2,
        )

        self.recent_item.created_at = now() - timedelta(days=10)
        self.recent_item.save()

        self.old_item.created_at = now() - timedelta(days=20)
        self.old_item.save()

        self.chat_recent = ChatRoom.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            item=self.recent_item,
        )
        self.chat_old = ChatRoom.objects.create(
            participant_1=self.user1,
            participant_2=self.user2,
            item=self.old_item,
        )

    def test_clean_old_items(self):

        delete_old_items_and_chats()

        assert not Item.objects.filter(id=self.old_item.id).exists()

        assert not ChatRoom.objects.filter(id=self.chat_old.id).exists()

        assert Item.objects.filter(id=self.recent_item.id).exists()

        assert ChatRoom.objects.filter(id=self.chat_recent.id).exists()
