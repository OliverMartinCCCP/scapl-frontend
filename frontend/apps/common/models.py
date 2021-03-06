# -*- coding: UTF-8 -*-
import os
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
try:
    from bootstrap_themes import list_themes
except ImportError:
    list_themes = lambda: tuple()

"""
This module defines base models for handling users information such as the title, rank, address and their related fields.
It defines a generic user model with the following characteristics:
 - The key field is the email
 - A new instance is created as inactive and without staff responsibility (that is, the user has no access to the admin site)
 - All other fields are optional
"""


class Title(models.Model):
    """ This model handles user's titles """
    short = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = _("Title")
        verbose_name_plural = _("Titles")

    def __str__(self):
        return self.short


class Rank(models.Model):
    """ This model handles user's ranks """
    short = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=60, unique=True)

    class Meta:
        verbose_name = _("Rank")
        verbose_name_plural = _("Ranks")

    def __str__(self):
        return self.short


class Country(models.Model):
    """ This model handles countries for use with localities """
    label = models.CharField(max_length=60, default="Belgium", unique=True)

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")

    def __str__(self):
        return self.label


class Locality(models.Model):
    """ This model handles localities for use with addresses """
    label = models.CharField(max_length=60, default="Brussels")
    postal_code = models.CharField(max_length=6, db_index=True)
    country = models.ForeignKey(Country, default=1, related_name="locality_country")

    class Meta:
        verbose_name = _("Locality")
        verbose_name_plural = _("Localities")

    def __str__(self):
        return u"{} {}".format(self.postal_code, self.label)


class Address(models.Model):
    """ This model handles addresses for use with departments """
    street = models.CharField(max_length=100, default=None, blank=True, null=True)
    number = models.CharField(max_length=6, default=None, blank=True, null=True)
    locality = models.ForeignKey(Locality, default=None, blank=True, null=True, related_name="addresses")

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def __str__(self):
        return "{}, {} - {}".format(self.street, self.number, self.locality)


class Element(models.Model):
    """ This generic model handles the base information of an organization's element """
    name = models.CharField(max_length=60, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    class Meta:
        abstract = True


class OrganizationalUnit(Element):
    """ This model handles organizational units for use with departments """

    class Meta:
        verbose_name = _("Organizational unit")
        verbose_name_plural = _("Organizational units")

    def __str__(self):
        return u'{}'.format(self.abbreviation)


class Department(Element):
    """ This model handles departments for use with services """
    organization = models.ForeignKey(OrganizationalUnit, related_name="departments")

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")

    def __str__(self):
        return u'{}/{}'.format(str(self.organization), self.abbreviation).strip(" /")


class Service(Element):
    """ This model handles user's services """
    department = models.ForeignKey(Department, related_name="services")

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self):
        return u'{}/{}'.format(str(self.department), self.abbreviation).strip(" /")


class GenericUserManager(BaseUserManager):
    """ This manager handles the creation of a user according to the custom model GenericUser based on the
     email instead of the username """
    def create_user(self, email=None, password=None, **extra_fields):
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(email=email, is_superuser=False, last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        # only one superuser should be created by the SuperUserBackend ; this prevents from creating another one
        #  as self.create_user will set is_superuser=False
        return self.create_user(email, password, **extra_fields)


def upload_avatar(self, fn):
    filename, extension = os.path.splitext(fn)
    return '{}/{}_{}{}'.format(settings.AVATARS_LOCATION, str(self.id).zfill(3), slugify(filename), extension)


class GenericUser(AbstractBaseUser, PermissionsMixin):
    """ This model defines a new generic user with additional fields compared to auth module's User model
     using the email as the authentication data """
    email = models.EmailField(max_length=254, unique=True, db_index=True)
    first_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    last_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    title = models.ForeignKey(Title, default=None, blank=True, null=True, related_name="users")
    rank = models.ForeignKey(Rank, default=None, blank=True, null=True, related_name="users")
    service = models.ForeignKey(Service, default=None, blank=True, null=True, related_name="users")
    phone1 = models.CharField(max_length=30, default=None, blank=True, null=True)
    phone2 = models.CharField(max_length=30, default=None, blank=True, null=True)
    comments = models.TextField(max_length=1000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to=upload_avatar, default='{}/default.png'.format(settings.AVATARS_LOCATION))
    theme = models.CharField(max_length=128, default=settings.DEFAULT_BOOTSTRAP_THEME, choices=list_themes())

    objects = GenericUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELD = ('email', )

    def __str__(self):
        name = self.get_extended_name()
        return u'{} ({})'.format(self.email, name).strip(" ()" if name == '' else "")

    def clean_first_name(self, first_name):
        return first_name.capitalize()

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def clean_last_name(self, last_name):
        return last_name.capitalize()

    def get_full_name(self):
        return u'{} {}'.format(self.first_name or '', self.last_name or '').strip(" ")

    def get_short_name(self):
        short_name = u'{}. {}'.format(self.first_name[0] if self.first_name else '', self.last_name or '').strip(" .")
        return self.first_name if len(short_name) == 1 else (short_name if short_name != '' else _('undefined name'))

    def get_extended_name(self):
        return u'{} {} {}'.format(self.rank or '', self.get_short_name() or '', self.title or '').strip(" ")

    def natural_key(self):
        return (self.pk, )


class Tooltip(models.Model):
    base_url = models.CharField(max_length=255, db_index=True)
    selector = models.CharField(max_length=50, default='', blank=False, null=False, help_text='label:contains("example")')
    type = models.CharField(max_length=24, default='question-circle', blank=False, null=False)
    title = models.CharField(max_length=255)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)


@receiver(pre_delete, sender=GenericUser)
def delete_user(sender, instance, **kwargs):
    if instance.is_superuser:
        raise PermissionDenied
