from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

security = HTTPBearer(
    scheme_name="BearerAuth"
)


def get_current_user(
    token=Depends(security),
    db: Session = Depends(get_db)
):

    payload = decode_access_token(token.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token subject"
        )

    user = db.query(User).filter(
        User.id == int(user_id),
        User.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User is inactive"
        )

    return user
