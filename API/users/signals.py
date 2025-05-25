import cloudinary.uploader
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.timezone import is_naive, make_aware

from .models import ItemImage, UserProfile
from .tasks import (
    send_ban_notification_email,
    send_unban_notification_email,
    send_welcome_email,
)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()


@receiver(user_logged_in)
def send_welcome_email_on_first_login(sender, request, user, **kwargs):
    if is_naive(user.date_joined):
        make_aware(user.date_joined)
    else:
        pass

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if not profile.welcome_email_sent:
        print("Primeiro login detectado. Enviando e-mail de boas-vindas.")
        send_welcome_email.delay(user.email, user.first_name)
        profile.welcome_email_sent = True
        profile.save()
    else:
        print("E-mail de boas-vindas já enviado anteriormente. Nenhuma ação tomada.")


@receiver(post_delete, sender=ItemImage)
def delete_image_from_cloudinary(sender, instance, **kwargs):
    """
    Remove a imagem do Cloudinary quando o ItemImage é deletado.
    """
    if instance.image_url:
        try:
            public_id = instance.image_url.split("/")[-1].split(".")[0]
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Erro ao remover a imagem do Cloudinary: {str(e)}")


@receiver(post_save, sender=UserProfile)
def notify_user_ban_status_change(sender, instance, **kwargs):
    if kwargs.get("update_fields") is None or "is_banned" in kwargs.get("update_fields", []):
        user = instance.user

        if instance.is_banned:
            send_ban_notification_email.delay(user.email, user.first_name, user.last_name)
        else:
            send_unban_notification_email.delay(user.email, user.first_name, user.last_name)
