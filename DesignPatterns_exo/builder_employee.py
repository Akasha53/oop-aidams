"""Creational - Builder: refactor of create_employee() and its 17 positional arguments."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Employee:
    """The product: a plain data container."""

    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    salary: float
    start_date: str
    manager_id: int | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    has_parking: bool = False
    has_laptop: bool = False
    has_vpn_access: bool = False
    has_admin_rights: bool = False
    office_location: str | None = None
    contract_type: str = "permanent"


class EmployeeBuilder:
    """Collects the fields step by step; every with_* returns self so calls can be chained."""

    def __init__(self) -> None:
        self._fields: dict = {"start_date": date.today().isoformat()}

    def with_name(self, first_name: str, last_name: str) -> EmployeeBuilder:
        self._fields.update(first_name=first_name, last_name=last_name)
        return self

    def with_email(self, email: str) -> EmployeeBuilder:
        self._fields["email"] = email
        return self

    def with_job(self, department: str, position: str, salary: float) -> EmployeeBuilder:
        self._fields.update(department=department, position=position, salary=salary)
        return self

    def with_start_date(self, start_date: str) -> EmployeeBuilder:
        self._fields["start_date"] = start_date
        return self

    def with_manager(self, manager_id: int) -> EmployeeBuilder:
        self._fields["manager_id"] = manager_id
        return self

    def with_contact(self, phone: str | None = None, address: str | None = None,
                     emergency_contact: str | None = None) -> EmployeeBuilder:
        self._fields.update(phone=phone, address=address, emergency_contact=emergency_contact)
        return self

    def with_equipment(self, laptop: bool = False, parking: bool = False) -> EmployeeBuilder:
        self._fields.update(has_laptop=laptop, has_parking=parking)
        return self

    def with_access(self, vpn: bool = False, admin: bool = False) -> EmployeeBuilder:
        self._fields.update(has_vpn_access=vpn, has_admin_rights=admin)
        return self

    def with_office(self, location: str) -> EmployeeBuilder:
        self._fields["office_location"] = location
        return self

    def with_contract(self, contract_type: str) -> EmployeeBuilder:
        self._fields["contract_type"] = contract_type
        return self

    def build(self) -> Employee:
        """All the validation lives here, in one place."""
        f = self._fields
        if not f.get("first_name") or not f.get("last_name"):
            raise ValueError("Name is required")
        if "@" not in (f.get("email") or ""):
            raise ValueError("Valid email is required")
        if "position" not in f:
            raise ValueError("Job is required (with_job)")
        if f["salary"] < 0:
            raise ValueError("Salary cannot be negative")
        return Employee(**f)


class DeveloperBuilder(EmployeeBuilder):
    """Preset: developers get a laptop and the VPN, seniors also get admin rights."""

    def __init__(self, first_name: str, last_name: str, email: str, senior: bool = False) -> None:
        super().__init__()
        position = "Senior Developer" if senior else "Developer"
        (self.with_name(first_name, last_name)
             .with_email(email)
             .with_job("Engineering", position, 75000 if senior else 55000)
             .with_equipment(laptop=True)
             .with_access(vpn=True, admin=senior))


class InternBuilder(EmployeeBuilder):
    """Preset: internship contract, laptop, no VPN, no admin, always a manager."""

    def __init__(self, first_name: str, last_name: str, email: str,
                 department: str, manager_id: int) -> None:
        super().__init__()
        (self.with_name(first_name, last_name)
             .with_email(email)
             .with_job(department, "Intern", 15000)
             .with_manager(manager_id)
             .with_equipment(laptop=True)
             .with_contract("internship"))


if __name__ == "__main__":
    dev = (
        EmployeeBuilder()
        .with_name("John", "Doe")
        .with_email("john.doe@company.com")
        .with_job("Engineering", "Senior Developer", 75000)
        .with_start_date("2024-01-15")
        .with_contact(phone="+33612345678")
        .with_equipment(laptop=True, parking=False)
        .with_access(vpn=True, admin=True)
        .with_office("Paris HQ")
        .build()
    )
    intern = (InternBuilder("Jane", "Smith", "jane.smith@company.com", "Marketing", 42)
              .with_start_date("2024-02-01")
              .with_office("Paris HQ")
              .build())
    print(dev)
    print(intern)
    print(DeveloperBuilder("John", "Doe", "john.doe@company.com").build())
