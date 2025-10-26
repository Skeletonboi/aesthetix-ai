from src.auth.models import User
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreate, UserUpdate
from src.auth.utils import generate_pwd_hash
from uuid import UUID
from fastapi.exceptions import HTTPException
from fastapi import status


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)

        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, uid: UUID, session: AsyncSession):
        statement = select(User).where(User.uid == uid)
        result = await session.execute(statement)

        return result.scalar_one_or_none()
    
    async def create_user(self, user_data: UserCreate, session: AsyncSession):
        user_dict = user_data.model_dump()
        new_user = User(**user_dict)
        new_user.password_hash = generate_pwd_hash(user_data.password)

        session.add(new_user)
        await session.commit()
        
        await session.refresh(new_user) # Why do I need this here but not in other table creates

        return new_user


    async def delete_user(self, uid: UUID, session: AsyncSession):
        user = await self.get_user_by_id(uid, session)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User for deletion not found.")

        # Remove associated workout logs (FKEY constraint)
        from src.workout_logs.service import WorkoutLogService
        _ = await WorkoutLogService.delete_log_by_user_id(user.uid, session)

        await session.delete(user)
        await session.commit()

        return
    
    async def update_user(self, uid: UUID, update_data: UserUpdate, session: AsyncSession):
        user = await self.get_user_by_id(uid, session)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="User for updating not found.")

        # Update user data
        update_dict = update_data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(user, k, v)
        
        await session.commit()
        await session.refresh(user)

        return user
