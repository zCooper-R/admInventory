import factory
from factory.django import DjangoModelFactory

from apps.users.models import User, UserRole
from apps.locations.models import Organization, Location
from apps.inventory.models import Device, DeviceType, DeviceStatus, StorageType


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.Faker("name", locale="ru_RU")
    role = UserRole.USER
    is_active = True


class AdminUserFactory(UserFactory):
    role = UserRole.ADMIN
    is_staff = True
    is_superuser = True


class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Организация {n}")
    normalized_name = factory.LazyAttribute(lambda obj: obj.name.lower())


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Площадка {n}")
    address = factory.Faker("address", locale="ru_RU")
    organization = factory.SubFactory(OrganizationFactory)


class DeviceFactory(DjangoModelFactory):
    class Meta:
        model = Device

    name = factory.Sequence(lambda n: f"ПК-{n:03d}")
    inventory_number = factory.Sequence(lambda n: f"INV-TEST-{n:04d}")
    device_type = DeviceType.PC
    cpu = "Intel Core i5-12400"
    ram = 16
    storage_type = StorageType.SSD
    storage_size = 512
    os = "Windows 11 Pro"
    status = DeviceStatus.ACTIVE
    organization = factory.SubFactory(OrganizationFactory)
    location = factory.SubFactory(LocationFactory, organization=factory.SelfAttribute("..organization"))
    assigned_to = None
