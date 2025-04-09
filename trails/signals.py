from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from .models import AuditTrail
from users.models import PrideUser
from .threadlocals import get_current_user

@receiver(pre_save, sender=PrideUser)
def log_user_update(sender, instance, **kwargs):
    """
    Capture updates to PrideUser before the actual save (for comparison with old values).
    """
    if instance.pk:
        try:
            old_instance = PrideUser.objects.get(pk=instance.pk)

            for field in instance._meta.fields:
                field_name = field.name

                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)
                if old_value != new_value:
                    user = get_current_user()
                    AuditTrail.objects.create(
                        action='UPDATE',
                        model_name='PrideUser',
                        object_id=instance.pk,
                        field_name=field_name,
                        old_value=str(old_value),
                        new_value=str(new_value),
                        user=user,
                    )
        except PrideUser.DoesNotExist:
            pass

@receiver(post_save, sender=PrideUser)
def log_user_creation(sender, instance, created, **kwargs):
    """
    Capture creation of new PrideUser.
    """
    if created:
        user = get_current_user()
        AuditTrail.objects.create(
            action='CREATE',
            model_name='PrideUser',
            object_id=instance.pk,
            user=user,
        )

    if instance.password_changed_at:
        user = get_current_user()
        AuditTrail.objects.create(
            action='UPDATE',
            model_name='PrideUser',
            object_id=instance.pk,
            field_name='password',
            old_value='Old password',
            new_value='New password',
            user=user,
        )



@receiver(pre_save, sender=Group)
def log_group_update(sender, instance, **kwargs):
    """
    Capture updates to Group before the actual save (for comparison with old values).
    """
    if instance.pk:
        try:
            old_instance = Group.objects.get(pk=instance.pk)

            for field in instance._meta.fields:
                field_name = field.name

                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)
                if old_value != new_value:
                    user = get_current_user()
                    AuditTrail.objects.create(
                        action='UPDATE',
                        model_name='Group',
                        object_id=instance.pk,
                        field_name=field_name,
                        old_value=str(old_value),
                        new_value=str(new_value),
                        user=user,
                    )
        except Group.DoesNotExist:
            pass

@receiver(post_save, sender=Group)
def log_group_creation(sender, instance, created, **kwargs):
    """
    Capture creation of new Group.
    """
    if created:
        user = get_current_user()
        AuditTrail.objects.create(
            action='CREATE',
            model_name='Group',
            object_id=instance.pk,
            user=user,
        )

@receiver(m2m_changed, sender=Group.permissions.through)
def log_permission_assignment(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Track when permissions are added or removed from a group.
    """
    user = get_current_user()

    for permission_id in pk_set:
        try:
            permission = Permission.objects.get(id=permission_id)
            action_type = 'ASSIGN' if action == 'post_add' else 'REMOVE'

            AuditTrail.objects.create(
                action=action_type,
                model_name='Permission',
                object_id=permission.id,
                user=user,
                field_name='permission',
                old_value=None if action == 'post_add' else permission.name,
                new_value=permission.name if action == 'post_add' else None,
            )
        except Permission.DoesNotExist:
            pass

@receiver(m2m_changed, sender=PrideUser.groups.through)
def log_group_assignment(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Track when groups are added or removed from a user.
    """
    user = get_current_user()

    for group_id in pk_set:
        try:
            group = Group.objects.get(id=group_id)
            action_type = 'ADD' if action == 'post_add' else 'REMOVE'

            AuditTrail.objects.create(
                action=action_type,
                model_name='Group',
                object_id=group.id,
                user=user,
                field_name='group',
                old_value=None if action == 'post_add' else group.name,
                new_value=group.name if action == 'post_add' else None,
            )
        except Group.DoesNotExist:
            pass