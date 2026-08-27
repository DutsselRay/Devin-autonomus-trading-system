from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from aoic_kernel.models import CampaignStatus, GrowthCampaign


class CMOGrowth:
    """Growth campaign registry and lifecycle."""

    def __init__(self) -> None:
        self._campaigns: dict[str, GrowthCampaign] = {}

    def create(
        self,
        name: str,
        channel: str,
        audience: str,
        budget: float,
        start_date: datetime,
        campaign_id: Optional[str] = None,
    ) -> GrowthCampaign:
        if budget < 0:
            raise ValueError("budget must be non-negative")
        campaign = GrowthCampaign(
            campaign_id=campaign_id or f"CAM-{uuid4().hex[:8].upper()}",
            name=name,
            channel=channel,
            audience=audience,
            budget=budget,
            start_date=start_date,
            created_at=datetime.now(timezone.utc),
        )
        self._campaigns[campaign.campaign_id] = campaign
        return campaign

    def get(self, campaign_id: str) -> GrowthCampaign:
        if campaign_id not in self._campaigns:
            raise KeyError(campaign_id)
        return self._campaigns[campaign_id]

    def list_campaigns(self) -> list[GrowthCampaign]:
        return list(self._campaigns.values())

    def review(self, campaign_id: str, evidence: list[str]) -> GrowthCampaign:
        campaign = self.get(campaign_id)
        if campaign.status != CampaignStatus.DRAFT:
            raise ValueError("only DRAFT campaigns can be reviewed")
        if not evidence:
            raise ValueError("review requires evidence")
        campaign.status = CampaignStatus.REVIEWED
        campaign.evidence.extend(evidence)
        self._campaigns[campaign_id] = campaign
        return campaign

    def start(self, campaign_id: str) -> GrowthCampaign:
        campaign = self.get(campaign_id)
        if campaign.status != CampaignStatus.REVIEWED:
            raise ValueError("campaign must be REVIEWED before start")
        campaign.status = CampaignStatus.RUNNING
        self._campaigns[campaign_id] = campaign
        return campaign

    def pause(self, campaign_id: str, reason: str) -> GrowthCampaign:
        campaign = self.get(campaign_id)
        if campaign.status != CampaignStatus.RUNNING:
            raise ValueError("only RUNNING campaigns can be paused")
        campaign.status = CampaignStatus.PAUSED
        campaign.evidence.append(f"paused: {reason}")
        self._campaigns[campaign_id] = campaign
        return campaign

    def complete(self, campaign_id: str) -> GrowthCampaign:
        campaign = self.get(campaign_id)
        if campaign.status not in (CampaignStatus.RUNNING, CampaignStatus.PAUSED):
            raise ValueError("campaign must be RUNNING or PAUSED to complete")
        campaign.status = CampaignStatus.COMPLETED
        campaign.end_date = datetime.now(timezone.utc)
        self._campaigns[campaign_id] = campaign
        return campaign

    def add_lead(self, campaign_id: str, lead_id: str) -> GrowthCampaign:
        campaign = self.get(campaign_id)
        if campaign.status not in (CampaignStatus.RUNNING, CampaignStatus.PAUSED):
            raise ValueError("campaign must be active to add leads")
        campaign.leads.append(lead_id)
        self._campaigns[campaign_id] = campaign
        return campaign
