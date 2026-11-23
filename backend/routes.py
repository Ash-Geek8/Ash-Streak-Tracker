import json
from datetime import datetime
from flask import Blueprint,current_app,jsonify,request,Response,stream_with_context
from flask_login import current_user,login_user,logout_user,login_required
from .extensions import db
from .models import User,Routine,Completion,Note
from .timeutils import valid_timezone,local_today,week_bounds
from .notes_rag import rebuild_notes_index,answer_from_notes
api=Blueprint("api",__name__)
CATS={"Food","Prayer","Skincare","Workout"}
def error(msg,status=400): return jsonify({"error":msg}),status
def rjson(r):
    return {
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "description": r.description or "",
        "target_per_week": r.target_per_week,
        "active": r.active,
        "sort_order": r.sort_order
    }
def defaults(u):
    if Routine.query.filter_by(user_id=u.id).count()==0:
        for name,cat,desc in [("Breakfast / nutrition","Food","Follow planned meals"),("Lunch / nutrition","Food","Complete the main meal"),("Dinner / nutrition","Food","Complete evening meal"),("Daily prayers","Prayer","Track daily prayers"),("Morning skincare","Skincare","Morning routine"),("Night skincare","Skincare","Night routine"),("Workout / activity","Workout","Strength, cardio or recovery")]:
            db.session.add(Routine(user_id=u.id,name=name,category=cat,description=desc))
        db.session.commit()
def ujson(u):
    admin_email = (
        current_app.config.get("ADMIN_EMAIL") or ""
    ).strip().lower()

    return {
        "id": u.id,
        "email": u.email,
        "timezone": u.timezone,
        "today": local_today(u),
        "is_admin": bool(
            admin_email and u.email.lower() == admin_email
        )
    }
@api.post("/auth/register")
def register():
    if not current_app.config["ALLOW_REGISTRATION"]: return error("Registration is disabled.",403)
    d=request.get_json(silent=True) or {}; email=(d.get("email") or "").strip().lower(); pw=d.get("password") or ""; tz=d.get("timezone") or current_app.config["DEFAULT_TIMEZONE"]
    if "@" not in email: return error("Enter a valid email.")
    if len(pw)<10: return error("Password must be at least 10 characters.")
    if not valid_timezone(tz): return error("Choose a valid IANA timezone.")
    if User.query.filter_by(email=email).first(): return error("Account already exists.",409)
    u=User(email=email,timezone=tz); u.set_password(pw); db.session.add(u); db.session.commit(); defaults(u); login_user(u)
    return jsonify({"user":ujson(u)}),201
@api.post("/auth/login")
def login():
    d=request.get_json(silent=True) or {}; u=User.query.filter_by(email=(d.get("email") or "").strip().lower()).first()
    if not u or not u.check_password(d.get("password") or ""): return error("Invalid email or password.",401)
    login_user(u); defaults(u); return jsonify({"user":ujson(u)})
@api.post("/auth/logout")
@login_required
def logout(): logout_user(); return jsonify({"ok":True})
@api.get("/auth/me")
def me():
    if not current_user.is_authenticated: return jsonify({"user":None})
    defaults(current_user); return jsonify({"user":ujson(current_user)})
@api.get("/settings")
@login_required
def settings(): return jsonify(ujson(current_user))
@api.put("/settings")
@login_required
def save_settings():
    tz=(request.get_json(silent=True) or {}).get("timezone")
    if not valid_timezone(tz): return error("Invalid timezone.")
    current_user.timezone=tz; db.session.commit(); return jsonify(ujson(current_user))
@api.get("/routines")
@login_required
def routines():
    defaults(current_user)
    return jsonify([
        rjson(r)
        for r in Routine.query.filter_by(user_id=current_user.id)
        .order_by(
            Routine.category,
            Routine.sort_order,
            Routine.id
        ).all()
    ])
@api.post("/routines")
@login_required
def add_routine():
    d=request.get_json(silent=True) or {}; name=(d.get("name") or "").strip(); cat=d.get("category")
    if not name or cat not in CATS: return error("Routine name and valid category are required.")
    last_order = db.session.query(
        db.func.max(Routine.sort_order)
    ).filter_by(
        user_id=current_user.id,
        category=cat
    ).scalar()

    r = Routine(
        user_id=current_user.id,
        name=name[:100],
        category=cat,
        description=(d.get("description") or "")[:250],
        target_per_week=max(1, min(7, int(d.get("target_per_week", 7)))),
        sort_order=(last_order if last_order is not None else -1) + 1
    )
    db.session.add(r); db.session.commit(); return jsonify(rjson(r)),201
@api.put("/routines/<int:rid>")
@login_required
def edit_routine(rid):
    r=Routine.query.filter_by(id=rid,user_id=current_user.id).first_or_404(); d=request.get_json(silent=True) or {}
    if d.get("name"): r.name=d["name"].strip()[:100]
    if d.get("category") in CATS: r.category=d["category"]
    if "description" in d: r.description=(d["description"] or "")[:250]
    if "active" in d: r.active=bool(d["active"])
    if "target_per_week" in d: r.target_per_week=max(1,min(7,int(d["target_per_week"])))
    db.session.commit(); return jsonify(rjson(r))
@api.delete("/routines/<int:rid>")
@login_required
def archive_routine(rid):
    r=Routine.query.filter_by(id=rid,user_id=current_user.id).first_or_404(); r.active=False; db.session.commit()
    return jsonify({"ok":True,"archived":True})
@api.get("/days/<date>/completions")
@login_required
def day(date):
    try: datetime.strptime(date,"%Y-%m-%d")
    except ValueError: return error("Date must use YYYY-MM-DD.")
    rs=Routine.query.filter_by(user_id=current_user.id,active=True).all()
    cs=Completion.query.filter_by(user_id=current_user.id,local_date=date).all(); done={c.routine_id:c.completed for c in cs}
    return jsonify({"date":date,"routines":[{**rjson(r),"completed":done.get(r.id,False)} for r in rs]})
@api.put("/days/<date>/completions/<int:rid>")
@login_required
def completion(date,rid):
    try: datetime.strptime(date,"%Y-%m-%d")
    except ValueError: return error("Date must use YYYY-MM-DD.")
    r=Routine.query.filter_by(id=rid,user_id=current_user.id).first_or_404(); d=request.get_json(silent=True) or {}
    c=Completion.query.filter_by(user_id=current_user.id,routine_id=r.id,local_date=date).first()
    if c is None: c=Completion(user_id=current_user.id,routine_id=r.id,local_date=date); db.session.add(c)
    c.completed=bool(d.get("completed",False)); db.session.commit()
    return jsonify({"routine_id":r.id,"date":date,"completed":c.completed})
def njson(n): return {"id":n.id,"date":n.local_date,"routine_id":n.routine_id,"title":n.title,"content":n.content,"updated_at":n.updated_at.isoformat() if n.updated_at else None}
@api.get("/notes")
@login_required
def notes():
    q=Note.query.filter_by(user_id=current_user.id)
    if request.args.get("date"): q=q.filter_by(local_date=request.args["date"])
    if request.args.get("routine_id",type=int): q=q.filter_by(routine_id=request.args.get("routine_id",type=int))
    return jsonify([njson(n) for n in q.order_by(Note.local_date.desc(),Note.updated_at.desc()).limit(250).all()])
@api.post("/notes")
@login_required
def add_note():
    d=request.get_json(silent=True) or {}; date=d.get("date") or local_today(current_user); content=(d.get("content") or "").strip()
    try: datetime.strptime(date,"%Y-%m-%d")
    except ValueError: return error("Date must use YYYY-MM-DD.")
    if not content: return error("Note content cannot be empty.")
    rid=d.get("routine_id")
    if rid and not Routine.query.filter_by(id=rid,user_id=current_user.id).first(): return error("Routine not found.")
    n=Note(user_id=current_user.id,local_date=date,routine_id=rid,title=(d.get("title") or "Daily note")[:160],content=content[:12000])
    db.session.add(n); db.session.commit(); rebuild_notes_index(current_user.id,Note.query.filter_by(user_id=current_user.id).all())
    return jsonify(njson(n)),201
@api.put("/notes/<int:nid>")
@login_required
def edit_note(nid):
    n=Note.query.filter_by(id=nid,user_id=current_user.id).first_or_404(); d=request.get_json(silent=True) or {}
    if "title" in d: n.title=(d["title"] or "Daily note")[:160]
    if "content" in d and d["content"].strip(): n.content=d["content"].strip()[:12000]
    if "date" in d:
        try: datetime.strptime(d["date"],"%Y-%m-%d")
        except ValueError: return error("Date must use YYYY-MM-DD.")
        n.local_date=d["date"]
    db.session.commit(); rebuild_notes_index(current_user.id,Note.query.filter_by(user_id=current_user.id).all())
    return jsonify(njson(n))
@api.delete("/notes/<int:nid>")
@login_required
def delete_note(nid):
    n=Note.query.filter_by(id=nid,user_id=current_user.id).first_or_404(); db.session.delete(n); db.session.commit()
    rebuild_notes_index(current_user.id,Note.query.filter_by(user_id=current_user.id).all()); return jsonify({"ok":True})
@api.post("/notes/rebuild-index")
@login_required
def rebuild_index():
    return jsonify(rebuild_notes_index(current_user.id,Note.query.filter_by(user_id=current_user.id).all()))
@api.get("/analytics")
@login_required
def analytics():
    start=request.args.get("start"); end=request.args.get("end"); rid=request.args.get("routine_id",type=int); cat=request.args.get("category")
    if not start or not end:
        today=datetime.strptime(local_today(current_user),"%Y-%m-%d").date(); start=today.replace(day=1).isoformat(); end=today.isoformat()
    try: datetime.strptime(start,"%Y-%m-%d"); datetime.strptime(end,"%Y-%m-%d")
    except ValueError: return error("Dates must use YYYY-MM-DD.")
    q=db.session.query(Completion,Routine).join(Routine,Completion.routine_id==Routine.id).filter(Completion.user_id==current_user.id,Completion.local_date>=start,Completion.local_date<=end,Completion.completed.is_(True))
    if rid: q=q.filter(Routine.id==rid)
    if cat: q=q.filter(Routine.category==cat)
    daily={}; cats={}; weekly={}
    rows=q.all()
    for c,r in rows:
        daily[c.local_date]=daily.get(c.local_date,0)+1; cats[r.category]=cats.get(r.category,0)+1
        sun,sat=week_bounds(c.local_date); weekly[sun.isoformat()]=weekly.get(sun.isoformat(),0)+1
    return jsonify({"start":start,"end":end,"daily":[{"date":k,"completed":v} for k,v in sorted(daily.items())],
      "categories":[{"category":k,"completed":v} for k,v in sorted(cats.items())],
      "weekly":[{"week_start":k,"week_end":week_bounds(k)[1].isoformat(),"completed":v} for k,v in sorted(weekly.items())],"total_completed":len(rows)})
@api.get("/stream/notes-assistant")
@login_required
def notes_stream():
    question=(request.args.get("q") or "").strip()
    if not question: return error("A question is required.")
    def generate():
        yield "event: run_started\ndata: "+json.dumps({"type":"RUN_STARTED"})+"\n\n"
        yield "event: text_message_start\ndata: "+json.dumps({"type":"TEXT_MESSAGE_START","messageId":"notes-answer"})+"\n\n"
        answer=answer_from_notes(current_user.id,question)
        for i in range(0,len(answer),90):
            yield "event: text_message_content\ndata: "+json.dumps({"type":"TEXT_MESSAGE_CONTENT","messageId":"notes-answer","delta":answer[i:i+90]})+"\n\n"
        yield "event: text_message_end\ndata: "+json.dumps({"type":"TEXT_MESSAGE_END","messageId":"notes-answer"})+"\n\n"
        yield "event: run_finished\ndata: "+json.dumps({"type":"RUN_FINISHED"})+"\n\n"
    return Response(stream_with_context(generate()),mimetype="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
