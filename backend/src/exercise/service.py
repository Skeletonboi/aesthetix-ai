from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.exercise.models import Exercise
from src.exercise.schemas import ExerciseCreate, ExerciseUpdate
from src.tags.models import Tag
from src.tags.service import TagService
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

class ExerciseService:
    async def get_all_exercises(self, session: AsyncSession):
        statement = select(Exercise).options(selectinload(Exercise.tags))\
            .order_by(Exercise.exercise_slug.desc())
        result = await session.execute(statement)
        
        return result.scalars().all()

    async def get_exercise_by_slug(self, exercise_slug: str, session: AsyncSession):
        statement = select(Exercise).options(selectinload(Exercise.tags))\
            .where(Exercise.exercise_slug == exercise_slug)
        result = await session.execute(statement)
        
        return result.scalars().first()
    
    async def get_exercise_by_id(self, eid: UUID, session: AsyncSession):
        statement = select(Exercise).options(selectinload(Exercise.tags))\
            .where(Exercise.eid == eid)
        result = await session.execute(statement)
        
        return result.scalars().first()
    
    async def get_exercises_by_tag_id(self, tid: UUID, session: AsyncSession):
        statement = select(Exercise).join(Exercise.tags)\
            .where(Tag.tid == tid)\
            .order_by(Exercise.exercise_name.desc())
        result = await session.execute(statement)

        return result.scalars().all()

    async def create_exercise(self, exercise_data: ExerciseCreate, session: AsyncSession):
        # Check if exercise already exists
        exercise = await self.get_exercise_by_slug(exercise_data.exercise_slug, session)
        if exercise:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Exercise already exists.")
        
        # Get Tag ORM objects to insert into Exercise ORM object
        tags = await TagService.get_tags_from_slugs(exercise_data.tag_slugs, session)
        
        exercise_data_dict = exercise_data.model_dump()
        exercise_data_dict.pop("tag_slugs")
        new_exercise = Exercise(**exercise_data_dict)
        new_exercise.tags = tags

        session.add(new_exercise)
        await session.commit()
        await session.refresh(new_exercise)

        return new_exercise
    
    async def update_exercise(self, update_data: ExerciseUpdate, session: AsyncSession):
        # Get exercise ORM object
        exercise = await self.get_exercise_by_slug(update_data.exercise_slug, session)
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Exercise does not exist.")
        
        # Get Tag ORM objects to insert into Exercise ORM object
        tags = await TagService.get_tags_from_slugs(update_data.tag_slugs, session)
        
        exercise_data_dict = update_data.model_dump()
        
        exercise_data_dict["tags"] = tags
        exercise_data_dict["exercise_slug"] = exercise_data_dict["new_slug"]
        exercise_data_dict.pop("new_slug")

        for k, v in exercise_data_dict.items():
            setattr(exercise, k, v)
        
        await session.commit()
        await session.refresh(exercise)

        return exercise
    
    async def delete_exercise(self, exercise_slug: str, session: AsyncSession):
        # Remove from exercise_tags
        statement = select(Exercise).options(selectinload(Exercise.tags))\
        .where(Exercise.exercise_slug == exercise_slug)
        res = await session.execute(statement)
        exercise = res.scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail="Exercise does not exist.")
        exercise.tags.clear()
        await session.flush()

        # Remove associated workout logs (mandatory due to FKEY)
        from src.workout_logs.service import WorkoutLogService
        _ = await WorkoutLogService.delete_log_by_exercise_slug(exercise.exercise_slug, session)

        await session.delete(exercise)
        await session.commit()
        return

    @classmethod
    async def get_eid_from_slug(cls, exercise_slug: str, session: AsyncSession):
        exercise_service = cls()
        exercise = await exercise_service.get_exercise_by_slug(exercise_slug, session)
        
        return exercise.eid