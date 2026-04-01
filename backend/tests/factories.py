import factory
from apps.inventory.models import Device, DeviceType, ReplacementStatus, StorageType
from apps.locations.models import Organization
from apps.users.models import User, UserRole
from factory.django import DjangoModelFactory


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
    address = factory.Faker("address", locale="ru_RU")


class DeviceFactory(DjangoModelFactory):
    class Meta:
        model = Device

    inventory_number = factory.Sequence(lambda n: f"INV-TEST-{n:04d}")
    device_type = DeviceType.PC
    cpu_model = "Intel Core i5-12400"
    ram = 16
    storage_type = StorageType.SSD
    storage_size = 512
    os = "Windows 11 Pro"
    organization = factory.SubFactory(OrganizationFactory)
    employee_name = factory.Faker("name", locale="ru_RU")
    replacement_status = ReplacementStatus.OK
    replacement_score = 90
    replacement_reason = ""
