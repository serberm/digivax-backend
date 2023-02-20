from typing import Optional
from models.org import Orgs
from common.exceptions import (
    ResourceConflictError,
    ResourceNotFound,
    AuthenticationError,
)

def create_org(name: str, link: str, owner_user_id: int, agree_at, verified, timezone) -> Orgs:
    
    if Orgs.get_org_by_link(link):
        raise ResourceConflictError("org link already exist")

    return Orgs.create(
        name=name,
        link=link,
        owner_user_id=owner_user_id,
        agree_at=agree_at,
        verified=verified,
        timezone=timezone
    )
