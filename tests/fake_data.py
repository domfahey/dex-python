"""Fake data generators for tests using Faker."""

from faker import Faker

# Use seed for reproducible test data
fake = Faker()
Faker.seed(42)


def fake_contact() -> dict:
    """Generate a fake contact dictionary."""
    return {
        "id": fake.uuid4(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "job_title": fake.job(),
        "contact_emails": [{"email": fake.email()}],
        "contact_phones": [{"phone_number": fake.phone_number(), "label": "mobile"}],
        "linkedin": f"https://linkedin.com/in/{fake.user_name()}",
        "twitter": fake.user_name(),
        "website": fake.url(),
    }


def fake_contact_create() -> dict:
    """Generate fake data for ContactCreate."""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "job_title": fake.job(),
    }


def fake_reminder() -> dict:
    """Generate a fake reminder dictionary."""
    return {
        "id": fake.uuid4(),
        "title": fake.sentence(nb_words=4),
        "remind_at": fake.future_datetime().isoformat(),
        "completed": fake.boolean(),
    }


def fake_note() -> dict:
    """Generate a fake note dictionary."""
    return {
        "id": fake.uuid4(),
        "note": fake.paragraph(),
        "event_time": fake.past_datetime().isoformat(),
    }
