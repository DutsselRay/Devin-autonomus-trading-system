from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from aoic_kernel.models import Vendor, VendorStatus


class VendorRegister:
    """CPO vendor register with purpose, spend, renewal, alternatives and exit plan."""

    def __init__(self) -> None:
        self._vendors: dict[str, Vendor] = {}

    def register(
        self,
        name: str,
        purpose: str,
        owner: str,
        renewal_date: datetime,
        alternatives: list[str],
        data_classification: str = "internal",
        subprocessors: Optional[list[str]] = None,
        sla: str = "",
        exit_plan: str = "",
        rights: str = "",
        vendor_id: Optional[str] = None,
    ) -> Vendor:
        if not purpose or not owner:
            raise ValueError("purpose and owner are required")
        if not exit_plan:
            raise ValueError("exit plan is required")
        vendor = Vendor(
            vendor_id=vendor_id or f"VENDOR-{uuid4().hex[:8].upper()}",
            name=name,
            purpose=purpose,
            owner=owner,
            renewal_date=renewal_date,
            alternatives=alternatives,
            data_classification=data_classification,
            subprocessors=subprocessors or [],
            sla=sla,
            exit_plan=exit_plan,
            rights=rights,
            registered_at=datetime.now(timezone.utc),
        )
        self._vendors[vendor.vendor_id] = vendor
        return vendor

    def get(self, vendor_id: str) -> Vendor:
        if vendor_id not in self._vendors:
            raise KeyError(vendor_id)
        return self._vendors[vendor_id]

    def list_vendors(self) -> list[Vendor]:
        return list(self._vendors.values())

    def add_spend(self, vendor_id: str, amount: float) -> Vendor:
        if amount < 0:
            raise ValueError("spend must be non-negative")
        vendor = self.get(vendor_id)
        vendor.spend += amount
        self._vendors[vendor_id] = vendor
        return vendor

    def review(self, vendor_id: str) -> Vendor:
        vendor = self.get(vendor_id)
        vendor.status = VendorStatus.UNDER_REVIEW
        self._vendors[vendor_id] = vendor
        return vendor

    def exit(self, vendor_id: str, replacement_vendor_id: str) -> Vendor:
        vendor = self.get(vendor_id)
        if replacement_vendor_id not in self._vendors:
            raise ValueError("replacement vendor must be registered")
        if replacement_vendor_id not in vendor.alternatives:
            raise ValueError("replacement vendor must be listed as alternative")
        vendor.status = VendorStatus.EXITED
        self._vendors[vendor_id] = vendor
        return vendor
