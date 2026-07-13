"""User domain events."""
from dataclasses import dataclass
from backend.core.events.bus import DomainEvent


@dataclass
class UserCreated(DomainEvent):
    email: str = ""
    full_name: str = ""


@dataclass
class UserUpdated(DomainEvent):
    pass


@dataclass
class UserDeactivated(DomainEvent):
    pass


@dataclass
class UserLoggedIn(DomainEvent):
    ip_address: str = ""
