
import React, { useEffect, useState } from "react";
import api from "./api";

export default function Admin() {
  const [users, setUsers] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/admin/users");
      setUsers(response.data.users);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function deleteUser(user) {
    const confirmed = window.confirm(
      `Permanently delete ${user.email} and all their tracker data? This cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await api.delete(`/admin/users/${user.id}`);
      setUsers(old => old.filter(item => item.id !== user.id));
    } catch (e) {
      setError(e.message);
    }
  }

  function toggleUser(id) {
    setExpanded(old => ({
      ...old,
      [id]: !old[id]
    }));
  }

  if (loading) {
    return <section className="panel">Loading administrator dashboard…</section>;
  }

  return (
    <>
      <div className="heading">
        <div>
          <p className="eyebrow">SYSTEM MANAGEMENT</p>
          <h1>Admin <i>dashboard</i></h1>
          <p className="muted">
            Registered accounts and their Ash Streak activity.
          </p>
        </div>

        <button className="secondary" onClick={load}>
          Refresh
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="metrics">
        <section className="panel metric">
          <small>REGISTERED USERS</small>
          <b>{users.length}</b>
        </section>

        <section className="panel metric">
          <small>ACTIVE ACCOUNTS</small>
          <b>{users.length}</b>
        </section>

        <section className="panel metric">
          <small>TOTAL ROUTINES</small>
          <b>
            {users.reduce((sum, user) => sum + user.routine_count, 0)}
          </b>
        </section>
      </div>

      <section className="panel">
        <h3>User accounts</h3>

        {!users.length && (
          <p className="muted">No registered users found.</p>
        )}

        {users.map(user => (
          <article className="admin-user" key={user.id}>
            <div className="admin-user-head">
              <div>
                <b>{user.email}</b>
                <small>
                  User ID: {user.id} · {user.timezone}
                </small>
                <small>
                  Joined: {
                    user.created_at
                      ? new Date(user.created_at).toLocaleString()
                      : "Unknown"
                  }
                </small>
              </div>

              <div className="admin-user-actions">
                <button
                  className="secondary"
                  onClick={() => toggleUser(user.id)}
                >
                  {expanded[user.id] ? "Hide details" : "View details"}
                </button>

                <button
                  className="danger"
                  onClick={() => deleteUser(user)}
                >
                  Delete user
                </button>
              </div>
            </div>

            <div className="admin-user-stats">
              <span>{user.routine_count} routines</span>
              <span>{user.completion_count} completions</span>
              <span>{user.note_count} notes</span>
            </div>

            {expanded[user.id] && (
              <div className="admin-user-details">
                <h4>Routine information</h4>

                {!user.routines.length && (
                  <p className="muted">No routines.</p>
                )}

                {user.routines.map(routine => (
                  <div className="admin-routine" key={routine.id}>
                    <div>
                      <b>{routine.name}</b>
                      <small>
                        {routine.category} ·{" "}
                        {routine.active ? "Active" : "Archived"}
                      </small>
                      {routine.description && (
                        <small>{routine.description}</small>
                      )}
                    </div>

                    {routine.category === "Workout" && (
                      <div className="admin-workout-days">
                        <b>Weekly workout plan</b>

                        {routine.workout_days.map(day => (
                          <div key={day.weekday}>
                            <strong>{day.day}</strong>
                            <ul>
                              {day.workouts.map((exercise, index) => (
                                <li key={index}>{exercise}</li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                <h4>Recent completion history</h4>

                {user.recent_completions.length ? (
                  <div className="admin-history">
                    {user.recent_completions.map((item, index) => (
                      <div key={index}>
                        <span>{item.date}</span>
                        <b>{item.routine}</b>
                        <small>
                          {item.completed ? "Completed" : "Not completed"}
                        </small>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="muted">No completion history.</p>
                )}

                <p className="admin-privacy">
                  Account password and password hash are never displayed.
                </p>
              </div>
            )}
          </article>
        ))}
      </section>
    </>
  );
}
