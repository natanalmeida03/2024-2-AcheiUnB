from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from chat.models import ChatRoom
from users.models import Item
from users.tasks import delete_old_items_and_chats

User = get_user_model()


class CleanOldItemsTest(TestCase):
    def setUp(self):

        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(
            username="user2", password="password2", email="testuser@example.com"
        )

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

    def test_send_email_on_old_item_deletion(self):
        from django.core import mail

        delete_old_items_and_chats()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user2.email)
        self.assertEqual(mail.outbox[0].subject, "Seu item foi removido do AcheiUnB")
