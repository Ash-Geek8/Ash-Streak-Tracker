
import React, { useEffect, useState } from "react";
import api from "./api";

const CATEGORIES = ["Food", "Prayer", "Skincare", "Workout"];

const DAYS = [
  "Monday", "Tuesday", "Wednesday", "Thursday",
  "Friday", "Saturday", "Sunday"
];

export default function Routines() {
  const [routines, setRoutines] = useState([]);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("Food");
  const [description, setDescription] = useState("");
  const [view, setView] = useState("active");
  const [editing, setEditing] = useState(null);
  const [planner, setPlanner] = useState(null);
  const [days, setDays] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const response = await api.get("/routines");
      setRoutines(response.data);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function addRoutine(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      await api.post("/routines", {
        name,
        category,
        description
      });

      setName("");
      setDescription("");
      setMessage("Routine added successfully.");
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function saveEdit(e) {
    e.preventDefault();
    setError("");

    try {
      await api.put(`/routines/${editing.id}`, {
        name: editing.name,
        category: editing.category,
        description: editing.description,
        target_per_week: editing.target_per_week
      });

      setEditing(null);
      setMessage("Routine updated.");
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function archiveRoutine(id) {
    if (!window.confirm("Archive this routine? Its history will be retained.")) {
      return;
    }

    try {
      await api.delete(`/routines/${id}`);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function restoreRoutine(id) {
    try {
      await api.put(`/routines/${id}`, { active: true });
      setMessage("Routine restored.");
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function permanentlyDelete(id) {
    if (!window.confirm(
      "Permanently delete this routine? Its completion history and workout plan will also be deleted. This cannot be undone."
    )) {
      return;
    }

    try {
      await api.delete(`/routines/${id}/permanent`);
      setMessage("Routine permanently deleted.");
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function moveRoutine(categoryName, visibleList, index, direction) {
    const target = index + direction;

    if (target < 0 || target >= visibleList.length) return;

    const reordered = [...visibleList];
    [reordered[index], reordered[target]] =
      [reordered[target], reordered[index]];

    try {
      await api.put("/routines/reorder", {
        routine_ids: reordered.map(r => r.id)
      });
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function openPlanner(routine) {
    setError("");
    setPlanner(routine);
    setBusy(true);

    try {
      const response = await api.get(
        `/routines/${routine.id}/workout-days`
      );

      setDays(
        response.data.days.map(day => ({
          ...day,
          text: day.workouts.join("\n")
        }))
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function updateDay(index, text) {
    setDays(old =>
      old.map((day, i) =>
        i === index ? { ...day, text } : day
      )
    );
  }

  async function savePlanner() {
    setBusy(true);
    setError("");
    setMessage("");

    try {
      await api.put(
        `/routines/${planner.id}/workout-days`,
        {
          days: days.map((day, index) => ({
            weekday: index,
            workouts: day.text
              .split("\n")
              .map(item => item.trim())
              .filter(Boolean)
          }))
        }
      );

      setMessage("Weekly workout plan saved.");
      setPlanner(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const visible = routines.filter(r =>
    view === "active" ? r.active : !r.active
  );

  return (
    <>
      <div className="heading">
        <div>
          <p className="eyebrow">BUILD YOUR SYSTEM</p>
          <h1>Manage <i>routines</i></h1>
          <p className="muted">
            Organise your daily habits and weekly training.
          </p>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}

      <section className="panel">
        <h3>Add a routine</h3>

        <form className="routineform" onSubmit={addRoutine}>
          <label>
            Routine name
            <input
              required
              maxLength={100}
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Morning workout"
            />
          </label>

          <label>
            Category
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
            >
              {CATEGORIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>

          <label>
            Description
            <input
              maxLength={250}
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
            />
          </label>

          <button className="primary">Add routine</button>
        </form>
      </section>

      <section className="panel">
        <div className="routine-tabs">
          <button
            className={view === "active" ? "tab active-tab" : "tab"}
            onClick={() => setView("active")}
          >
            Active ({routines.filter(r => r.active).length})
          </button>

          <button
            className={view === "archived" ? "tab active-tab" : "tab"}
            onClick={() => setView("archived")}
          >
            Archived ({routines.filter(r => !r.active).length})
          </button>
        </div>

        {CATEGORIES.map(categoryName => {
          const group = visible.filter(
            r => r.category === categoryName
          );

          if (!group.length) return null;

          return (
            <div className="routine-category" key={categoryName}>
              <h4>{categoryName}</h4>

              {group.map((routine, index) => (
                <div className="routine-row" key={routine.id}>
                  {editing?.id === routine.id ? (
                    <form className="routine-edit" onSubmit={saveEdit}>
                      <input
                        required
                        value={editing.name}
                        onChange={e =>
                          setEditing({ ...editing, name: e.target.value })
                        }
                      />

                      <select
                        value={editing.category}
                        onChange={e =>
                          setEditing({ ...editing, category: e.target.value })
                        }
                      >
                        {CATEGORIES.map(c => (
                          <option key={c}>{c}</option>
                        ))}
                      </select>

                      <input
                        value={editing.description}
                        onChange={e =>
                          setEditing({
                            ...editing,
                            description: e.target.value
                          })
                        }
                        placeholder="Description"
                      />

                      <div className="routine-actions">
                        <button className="primary">Save</button>
                        <button
                          type="button"
                          className="secondary"
                          onClick={() => setEditing(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <div className="routine-info">
                        <b>{routine.name}</b>
                        <small>{routine.description || "No description"}</small>
                        <small>
                          {routine.active ? "Active" : "Archived"}
                        </small>
                      </div>

                      <div className="routine-actions">
                        {routine.active && (
                          <>
                            <button
                              className="secondary"
                              title="Move up"
                              onClick={() =>
                                moveRoutine(categoryName, group, index, -1)
                              }
                            >
                              ↑
                            </button>

                            <button
                              className="secondary"
                              title="Move down"
                              onClick={() =>
                                moveRoutine(categoryName, group, index, 1)
                              }
                            >
                              ↓
                            </button>

                            <button
                              className="secondary"
                              onClick={() => setEditing({ ...routine })}
                            >
                              Edit
                            </button>

                            {routine.category === "Workout" && (
                              <button
                                className="secondary"
                                onClick={() => openPlanner(routine)}
                              >
                                Weekly plan
                              </button>
                            )}

                            <button
                              className="link"
                              onClick={() => archiveRoutine(routine.id)}
                            >
                              Archive
                            </button>
                          </>
                        )}

                        {!routine.active && (
                          <>
                            <button
                              className="primary"
                              onClick={() => restoreRoutine(routine.id)}
                            >
                              Restore
                            </button>

                            <button
                              className="danger"
                              onClick={() => permanentlyDelete(routine.id)}
                            >
                              Delete permanently
                            </button>
                          </>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          );
        })}

        {!visible.length && (
          <p className="muted">
            No {view} routines in this account.
          </p>
        )}
      </section>

      {planner && (
        <section className="panel workout-planner">
          <div className="sect">
            <div>
              <p className="eyebrow">MONDAY – SUNDAY</p>
              <h3>{planner.name} · Weekly workout planner</h3>
            </div>

            <button
              className="secondary"
              onClick={() => setPlanner(null)}
            >
              Close
            </button>
          </div>

          <p className="muted">
            Add one exercise per line. Include sets and reps if useful,
            for example: Push-ups – 4 sets × 12 reps.
          </p>

          {busy && <p className="muted">Loading…</p>}

          <div className="workout-days">
            {days.map((day, index) => (
              <div className="workout-day" key={day.weekday}>
                <label>
                  <b>{DAYS[index]}</b>
                  <textarea
                    rows={5}
                    value={day.text || ""}
                    onChange={e => updateDay(index, e.target.value)}
                    placeholder={
                      index === 6
                        ? "Rest / recovery"
                        : "Exercise 1\nExercise 2\nExercise 3"
                    }
                  />
                </label>
              </div>
            ))}
          </div>

          <div className="planner-footer">
            <button
              className="secondary"
              onClick={() => setPlanner(null)}
            >
              Cancel
            </button>

            <button
              className="primary"
              disabled={busy}
              onClick={savePlanner}
            >
              Save weekly plan
            </button>
          </div>
        </section>
      )}
    </>
  );
}
