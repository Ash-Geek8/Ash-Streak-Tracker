import json

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func

from .extensions import db
from .models import User, Routine, WorkoutDay, Completion, Note

extra_api = Blueprint("extra_api", __name__)

WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]


def error(message, status=400):
    return jsonify({"error": message}), status


def is_admin():
    configured_email = (
        current_app.config.get("ADMIN_EMAIL") or ""
    ).strip().lower()

    return bool(
        configured_email
        and current_user.is_authenticated
        and current_user.email.lower() == configured_email
    )


def admin_required():
    if not is_admin():
        return error("Administrator access required.", 403)
    return None


def get_owned_routine(routine_id):
    return Routine.query.filter_by(
        id=routine_id,
        user_id=current_user.id
    ).first()


def workout_json(row):
    try:
        exercises = json.loads(row.workouts)
    except (TypeError, ValueError):
        exercises = []

    return {
        "weekday": row.weekday,
        "day": WEEKDAYS[row.weekday],
        "workouts": exercises
    }


# ---------------------------------------------------------
# ROUTINE ORDERING
# ---------------------------------------------------------

@extra_api.put("/routines/reorder")
@login_required
def reorder_routines():
    data = request.get_json(silent=True) or {}
    routine_ids = data.get("routine_ids")

    if not isinstance(routine_ids, list) or not routine_ids:
        return error("routine_ids must be a non-empty list.")

    if len(routine_ids) != len(set(routine_ids)):
        return error("Duplicate routine IDs are not allowed.")

    routines = Routine.query.filter(
        Routine.user_id == current_user.id,
        Routine.id.in_(routine_ids)
    ).all()

    if len(routines) != len(routine_ids):
        return error("One or more routines do not belong to your account.", 403)

    categories = {routine.category for routine in routines}
    if len(categories) != 1:
        return error("Reorder routines within one category at a time.")

    by_id = {routine.id: routine for routine in routines}

    for position, routine_id in enumerate(routine_ids):
        by_id[routine_id].sort_order = position

    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------
# PERMANENT ROUTINE DELETION
# Existing DELETE /routines/<id> remains archive-only.
# ---------------------------------------------------------

@extra_api.delete("/routines/<int:routine_id>/permanent")
@login_required
def permanently_delete_routine(routine_id):
    routine = get_owned_routine(routine_id)

    if not routine:
        return error("Routine not found.", 404)

    Completion.query.filter_by(
        user_id=current_user.id,
        routine_id=routine.id
    ).delete(synchronize_session=False)

    Note.query.filter_by(
        user_id=current_user.id,
        routine_id=routine.id
    ).update({"routine_id": None}, synchronize_session=False)

    WorkoutDay.query.filter_by(
        routine_id=routine.id
    ).delete(synchronize_session=False)

    db.session.delete(routine)
    db.session.commit()

    return jsonify({"ok": True, "deleted": True})


# ---------------------------------------------------------
# WORKOUT WEEKLY PLANNER
# Monday = 0, Sunday = 6
# ---------------------------------------------------------

@extra_api.get("/routines/<int:routine_id>/workout-days")
@login_required
def get_workout_days(routine_id):
    routine = get_owned_routine(routine_id)

    if not routine:
        return error("Routine not found.", 404)

    if routine.category != "Workout":
        return error("Weekly workout plans are only available for Workout routines.")

    saved = {
        row.weekday: workout_json(row)
        for row in WorkoutDay.query.filter_by(routine_id=routine.id).all()
    }

    days = []
    for weekday, day_name in enumerate(WEEKDAYS):
        days.append(saved.get(weekday, {
            "weekday": weekday,
            "day": day_name,
            "workouts": []
        }))

    return jsonify({
        "routine_id": routine.id,
        "routine_name": routine.name,
        "days": days
    })


@extra_api.put("/routines/<int:routine_id>/workout-days")
@login_required
def save_workout_days(routine_id):
    routine = get_owned_routine(routine_id)

    if not routine:
        return error("Routine not found.", 404)

    if routine.category != "Workout":
        return error("Weekly workout plans are only available for Workout routines.")

    data = request.get_json(silent=True) or {}
    days = data.get("days")

    if not isinstance(days, list):
        return error("days must be a list.")

    parsed = {}

    for item in days:
        if not isinstance(item, dict):
            return error("Each day must be an object.")

        weekday = item.get("weekday")
        exercises = item.get("workouts", [])

        if not isinstance(weekday, int) or weekday < 0 or weekday > 6:
            return error("Weekday must be between 0 (Monday) and 6 (Sunday).")

        if weekday in parsed:
            return error("Each weekday can only appear once.")

        if not isinstance(exercises, list):
            return error("workouts must be a list.")

        cleaned = []
        for exercise in exercises:
            if not isinstance(exercise, str):
                return error("Each workout must be text.")

            exercise = exercise.strip()
            if exercise:
                if len(exercise) > 160:
                    return error("Each workout must be 160 characters or fewer.")
                cleaned.append(exercise)

        if len(cleaned) > 30:
            return error("A day can contain at most 30 workout items.")

        parsed[weekday] = cleaned

    try:
        for weekday in range(7):
            row = WorkoutDay.query.filter_by(
                routine_id=routine.id,
                weekday=weekday
            ).first()

            exercises = parsed.get(weekday, [])

            if row is None:
                row = WorkoutDay(
                    routine_id=routine.id,
                    weekday=weekday,
                    workouts=json.dumps(exercises)
                )
                db.session.add(row)
            else:
                row.workouts = json.dumps(exercises)

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({"ok": True, "days_saved": 7})


# ---------------------------------------------------------
# ADMIN DASHBOARD
# Never return password_hash or plaintext passwords.
# ---------------------------------------------------------

@extra_api.get("/admin/users")
@login_required
def admin_users():
    denied = admin_required()
    if denied:
        return denied

    users = User.query.order_by(User.created_at.desc()).all()
    result = []

    for user in users:
        routines = Routine.query.filter_by(
            user_id=user.id
        ).order_by(
            Routine.category,
            Routine.sort_order,
            Routine.id
        ).all()

        routine_data = []

        for routine in routines:
            workout_rows = WorkoutDay.query.filter_by(
                routine_id=routine.id
            ).order_by(WorkoutDay.weekday).all()

            routine_data.append({
                "id": routine.id,
                "name": routine.name,
                "category": routine.category,
                "description": routine.description or "",
                "active": routine.active,
                "target_per_week": routine.target_per_week,
                "sort_order": routine.sort_order,
                "workout_days": [
                    workout_json(row) for row in workout_rows
                ]
            })

        completion_count = Completion.query.filter_by(
            user_id=user.id,
            completed=True
        ).count()

        recent_completions = (
            db.session.query(Completion, Routine.name)
            .join(Routine, Completion.routine_id == Routine.id)
            .filter(Completion.user_id == user.id)
            .order_by(Completion.local_date.desc())
            .limit(30)
            .all()
        )

        note_count = Note.query.filter_by(user_id=user.id).count()

        result.append({
            "id": user.id,
            "email": user.email,
            "timezone": user.timezone,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at else None
            ),
            "routine_count": len(routines),
            "completion_count": completion_count,
            "note_count": note_count,
            "routines": routine_data,
            "recent_completions": [
                {
                    "date": completion.local_date,
                    "routine": routine_name,
                    "completed": completion.completed
                }
                for completion, routine_name in recent_completions
            ]
        })

    return jsonify({
        "users": result,
        "total_users": len(result)
    })


@extra_api.delete("/admin/users/<int:user_id>")
@login_required
def admin_delete_user(user_id):
    denied = admin_required()
    if denied:
        return denied

    if user_id == current_user.id:
        return error("You cannot delete your own administrator account.", 400)

    user = db.session.get(User, user_id)

    if not user:
        return error("User not found.", 404)

    routines = Routine.query.filter_by(user_id=user.id).all()
    routine_ids = [routine.id for routine in routines]

    if routine_ids:
        WorkoutDay.query.filter(
            WorkoutDay.routine_id.in_(routine_ids)
        ).delete(synchronize_session=False)

    Completion.query.filter_by(
        user_id=user.id
    ).delete(synchronize_session=False)

    Note.query.filter_by(
        user_id=user.id
    ).delete(synchronize_session=False)

    Routine.query.filter_by(
        user_id=user.id
    ).delete(synchronize_session=False)

    db.session.delete(user)
    db.session.commit()

    # Chroma is only a derived notes index. Remove this user's collection too.
    try:
        import os
        import chromadb

        client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_DIR", "instance/chroma")
        )
        collection_name = f"user_notes_{user_id}"

        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    except Exception:
        current_app.logger.exception(
            "Could not remove notes index for deleted user %s", user_id
        )

    return jsonify({"ok": True, "deleted_user_id": user_id})