from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.workout_logs.models import WorkoutLog
from src.workout_logs.schemas import WorkoutLogCreate, WorkoutLogUpdate
from src.exercise.models import Exercise
from src.exercise.service import ExerciseService
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload, joinedload
from datetime import date
from uuid import UUID
from typing import List

class WorkoutLogService:
    async def get_logs_all(self, session: AsyncSession):
        statement = select(WorkoutLog)\
            .join(WorkoutLog.exercise)\
            .options(selectinload(WorkoutLog.exercise))\
            .order_by(WorkoutLog.date_performed.desc(), 
                      Exercise.exercise_slug.asc())
        result = await session.execute(statement)

        return result.scalars().all()

    async def get_logs_by_day(self, query_date: date, session: AsyncSession):
        statement = select(WorkoutLog)\
            .join(WorkoutLog.exercise)\
            .options(selectinload(WorkoutLog.exercise))\
            .where(WorkoutLog.date_performed == query_date)\
            .order_by(Exercise.exercise_slug.asc())
        result = await session.execute(statement)

        return result.scalars().all()

    async def get_logs_by_exercise(self, exercise_slug: str, session: AsyncSession):
        statement = select(WorkoutLog)\
            .join(WorkoutLog.exercise)\
            .options(selectinload(WorkoutLog.exercise))\
            .where(Exercise.exercise_slug == exercise_slug)\
            .order_by(WorkoutLog.date_performed.desc())
        result = await session.execute(statement)

        return result.scalars().all()
    
    async def get_log_by_id(self, id: UUID, session: AsyncSession):
        statement = select(WorkoutLog)\
            .options(selectinload(WorkoutLog.exercise))\
            .where(WorkoutLog.wid == id)
        result = await session.execute(statement)

        return result.scalars().first()
    
    async def get_logs_by_user(self, user_id: UUID, session: AsyncSession):
        statement = select(WorkoutLog)\
            .join(WorkoutLog.exercise)\
            .options(selectinload(WorkoutLog.exercise))\
            .where(WorkoutLog.user_uid == user_id)\
            .order_by(WorkoutLog.date_performed.desc(),
                      Exercise.exercise_slug.asc())
        result = await session.execute(statement)

        return result.scalars().all()
    
    async def get_pr_log_by_ex(self, exercise_slug: str, uid: UUID, session: AsyncSession):
        statement = select(WorkoutLog)\
            .join(WorkoutLog.exercise)\
            .options(selectinload(WorkoutLog.exercise))\
            .where(WorkoutLog.user_uid == uid, Exercise.exercise_slug == exercise_slug)\
            .order_by(desc(WorkoutLog.weight), 
                      desc(WorkoutLog.date_performed))\
            .limit(1)
        
        result = await session.execute(statement)

        return result.scalars().first()

    async def create_log(self, log_data: WorkoutLogCreate, uid: UUID, session: AsyncSession):
        log_dict = log_data.model_dump()
        log_dict["user_uid"] = uid
        log_dict["exercise_eid"] = await ExerciseService.get_eid_from_slug(log_data.exercise_slug, session)
        log_dict.pop("exercise_slug")

        # construct WorkoutLog object
        new_log = WorkoutLog(**log_dict)

        session.add(new_log)
        await session.commit()
        await session.refresh(new_log)

        return new_log

    async def update_log(self, wid: UUID, log_data: WorkoutLogUpdate, session: AsyncSession):
        log = await self.get_log_by_id(wid, session)

        log_dict = log_data.model_dump()
        log_dict["exercise_eid"] = await ExerciseService.get_eid_from_slug(log_data.exercise_slug, session)
        log_dict.pop("exercise_slug")
        log_dict.pop("date_performed")
        
        for k, v in log_dict.items():
            setattr(log, k, v)
        await session.commit()
        await session.refresh(log)

        return log

    async def upsert_log(self, log_data: WorkoutLogUpdate, uid: UUID, session: AsyncSession):
        # This method is (currently) only used to upsert seed test data
        # Used in situations where it is unknown if row exists (no access to WID)
        log_dict = log_data.model_dump()
        log_dict["user_uid"] = uid

        # Check if row exists
        query = select(WorkoutLog).join(WorkoutLog.exercise)\
            .where(WorkoutLog.user_uid == log_dict["user_uid"], 
                   Exercise.exercise_slug == log_dict["exercise_slug"],
                   WorkoutLog.reps == log_dict["reps"],
                   WorkoutLog.weight == log_dict["weight"],
                   WorkoutLog.date_performed == log_dict["date_performed"])
        res = await session.execute(query)
        row = res.scalars().first()
        if not row:
            log_dict = log_data.model_dump()
            log_data_create = WorkoutLogCreate(**log_dict)
            new_row = await self.create_log(log_data_create, uid, session)
        else:
            new_row = await self.update_log(row.wid, log_data, session)

        return new_row

    async def delete_log(self, wid: UUID, session: AsyncSession):
        # Query if log ID exists
        log = await session.get(WorkoutLog, wid)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                    detail="Log not found.")
        await session.delete(log)
        await session.commit()

        return
    
    async def delete_logs_by_day(self, date: date, uid: UUID, session: AsyncSession):
        statement = select(WorkoutLog).where(WorkoutLog.date_performed == date,
                                             WorkoutLog.user_uid == uid)
        result = await session.execute(statement)
        logs = result.scalars().all()

        for log in logs:
            await session.delete(log)
        await session.commit()

        return
    
        # Old code for delete cascading workoutlog tags
        # log = await session.get(WorkoutLog, wid, options=[selectinload(WorkoutLog.tags)])
        # if not log:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        #                         detail="Log not found.")
        # log.tags.clear()
        # await session.flush()

        # await session.delete(log)
        # await session.commit()
        # return

    @classmethod
    async def delete_log_by_exercise_slug(cls, exercise_slug: str, session: AsyncSession):
        statement = select(WorkoutLog).join(WorkoutLog.exercise)\
            .where(Exercise.exercise_slug == exercise_slug)
        result = await session.execute(statement)
        logs = result.scalars().all()

        for log in logs:
            await session.delete(log)
        await session.commit()

        return

    @classmethod
    async def delete_log_by_user_id(cls, uid: UUID, session: AsyncSession):
        statement = select(WorkoutLog).where(WorkoutLog.user_uid == uid)
        result = await session.execute(statement)
        logs = result.scalars().all()

        for log in logs:
            await session.delete(log)
        await session.commit()

        return