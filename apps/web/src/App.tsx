import { FormEvent, useEffect, useState } from "react";
import { request, Task } from "./api";

const tokenKey = "aegis.access_token";

export function App() {
  const [token, setToken] = useState(localStorage.getItem(tokenKey));
  const [mode, setMode] = useState<"login" | "register">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [error, setError] = useState("");

  async function loadTasks() {
    if (!token) return;
    setTasks(await request<Task[]>("/tasks", { headers: { Authorization: `Bearer ${token}` } }));
  }

  useEffect(() => {
    loadTasks().catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load tasks"));
  }, [token]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const response = await request<{ access_token: string }>(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem(tokenKey, response.access_token);
      setToken(response.access_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to authenticate");
    }
  }

  async function addTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    try {
      await request<Task>("/tasks", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title: title.trim(), due_at: dueAt ? new Date(dueAt).toISOString() : null }),
      });
      setTitle("");
      setDueAt("");
      await loadTasks();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create task");
    }
  }

  if (!token) {
    return (
      <main className="shell narrow">
        <p className="eyebrow">AEGIS</p>
        <h1>Keep the next useful action from getting lost.</h1>
        <p className="muted">Create your account or sign in. Your session is stored locally in this browser.</p>
        <form onSubmit={signIn} className="card stack">
          <label>Email<input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" required minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          <button type="submit">{mode === "register" ? "Create account" : "Sign in"}</button>
        </form>
        <button className="link-button" onClick={() => setMode(mode === "register" ? "login" : "register")}>
          {mode === "register" ? "Already have an account? Sign in" : "Need an account? Create one"}
        </button>
        {error && <p className="error">{error}</p>}
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="header"><div><p className="eyebrow">AEGIS / TODAY</p><h1>Your commitments, calmly organized.</h1></div><button className="secondary" onClick={() => { localStorage.removeItem(tokenKey); setToken(null); }}>Sign out</button></header>
      <section className="card">
        <h2>Quick capture</h2>
        <form onSubmit={addTask} className="capture">
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="What needs follow-through?" aria-label="Task title" />
          <input type="datetime-local" value={dueAt} onChange={(event) => setDueAt(event.target.value)} aria-label="Due date and time" />
          <button type="submit">Add task</button>
        </form>
      </section>
      <section className="card"><div className="section-title"><h2>Tasks</h2><span>{tasks.filter((task) => task.status === "open").length} open</span></div>
        {tasks.length === 0 ? <p className="muted">Nothing captured yet.</p> : <ul>{tasks.map((task) => <li key={task.id}><span className={task.status === "completed" ? "done" : ""}>{task.title}</span><small>{task.due_at ? new Date(task.due_at).toLocaleString() : "No deadline"}</small></li>)}</ul>}
      </section>
      {error && <p className="error">{error}</p>}
    </main>
  );
}
