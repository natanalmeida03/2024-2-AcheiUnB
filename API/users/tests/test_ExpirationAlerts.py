from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils.timezone import now

from users.models import Item
from users.tasks import send_expiration_alerts

User = get_user_model()


class ExpirationAlertsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="password",
            email="testuser@example.com",
            first_name="Test",
        )
        self.item_expiring_soon = Item.objects.create(
            name="Expiring Soon Item",
            user=self.user,
        )
        self.item_not_expiring = Item.objects.create(
            name="Not Expiring Item",
            user=self.user,
        )

        self.item_expiring_soon.created_at = now() - timedelta(days=13)
        self.item_expiring_soon.save()

        self.item_not_expiring.created_at = now() - timedelta(days=5)
        self.item_not_expiring.save()

    def test_send_expiration_alert_email(self):
        from django.core import mail

        send_expiration_alerts()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.user.email)
        self.assertEqual(
            mail.outbox[0].subject, "Alerta de expiração do seu item no AcheiUnB"
        )
