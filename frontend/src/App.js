import React,{useEffect,useState}from'react';import{BrowserRouter,Routes,Route,NavLink,Navigate}from'react-router-dom';import{Activity,CalendarDays,CheckCircle2,Circle,ClipboardList,LogOut,NotebookPen,Settings,Sparkles,Target}from'lucide-react';import{Area,AreaChart,Bar,BarChart,CartesianGrid,Cell,Pie,PieChart,ResponsiveContainer,Tooltip,XAxis,YAxis}from'recharts';import api from'./api';
import Routines from "./Routines";
import Admin from "./Admin";

const cats=['Food','Prayer','Skincare','Workout'],today=()=>new Intl.DateTimeFormat('en-CA').format(new Date()),tz=()=>Intl.DateTimeFormat().resolvedOptions().timeZone||'Asia/Kolkata';
function Auth({done}){const[mode,M]=useState('login'),[email,E]=useState(''),[password,P]=useState(''),[zone,Z]=useState(tz()),[err,S]=useState('');async function submit(e){e.preventDefault();S('');try{let r=await api.post('/auth/'+mode,{email,password,timezone:zone});done(r.data.user)}catch(x){S(x.message)}}return <main className="auth"><section className="authbox"><div className="mark"><Activity/></div><p className="eyebrow">YOUR PRIVATE CONSISTENCY SPACE</p><h1>Ash <i>Streak</i></h1><p className="muted">Small actions. Honest progress. Every day.</p><form onSubmit={submit}><label>Email<input type="email" required value={email} onChange={e=>E(e.target.value)}/></label><label>Password<input type="password" minLength="10" required value={password} onChange={e=>P(e.target.value)}/></label>{mode==='register'&&<label>Timezone<input required value={zone} onChange={e=>Z(e.target.value)}/><small>Detected: {tz()}</small></label>}{err&&<p className="error">{err}</p>}<button className="primary"> {mode==='login'?'Sign in':'Create account'}</button></form><button className="link" onClick={()=>M(mode==='login'?'register':'login')}>{mode==='login'?'Create first account':'Back to sign in'}</button></section></main>}
function Layout({ user, logout, children }) {
  const links = [
    ["/", "Today"],
    ["/analytics", "Analytics"],
    ["/notes", "Notes"],
    ["/routines", "Routines"],
    ["/settings", "Settings"]
  ];

  if (user.is_admin) {
    links.push(["/admin", "Admin"]);
  }

  return (
    <div className="layout">
      <aside>
        <div className="brand">
          <div className="mark"><Activity /></div>
          <b>Ash Streak</b>
        </div>

        <nav>
          {links.map(([path, label]) => (
            <NavLink end={path === "/"} to={path} key={path}>
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="account">
          <small>{user.email}</small>
          <small>{user.timezone}</small>
          <button onClick={logout}>
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </aside>

      <main>
        <header>
          <span>
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric"
            })}
          </span>
          <em>● PRIVATE WORKSPACE</em>
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}
function Today(){const[d,D]=useState(today()),[items,I]=useState([]),[notes,N]=useState([]),[memo,M]=useState(''),[err,E]=useState('');async function load(){try{let[a,b]=await Promise.all([api.get(`/days/${d}/completions`),api.get('/notes',{params:{date:d}})]);I(a.data.routines);N(b.data)}catch(x){E(x.message)}}useEffect(()=>{load()},[d]);let done=items.filter(x=>x.completed).length,pct=items.length?Math.round(done/items.length*100):0;async function toggle(x){I(old=>old.map(y=>y.id===x.id?{...y,completed:!y.completed}:y));try{await api.put(`/days/${d}/completions/${x.id}`,{completed:!x.completed})}catch(e){E(e.message);load()}}async function save(e){e.preventDefault();if(memo.trim()){await api.post('/notes',{date:d,title:'Daily reflection',content:memo});M('');load()}}return <><div className="heading"><div><p className="eyebrow">DAILY EXECUTION</p><h1>Today's <i>streak</i></h1><p className="muted">Consistency over perfection. Mark what you complete.</p></div><input type="date" value={d} onChange={e=>D(e.target.value)}/></div><section className="hero"><div><small>DAILY COMPLETION</small><strong>{pct}%</strong><p>{done} of {items.length} routines completed</p></div><div className="ring" style={{'--p':pct*3.6+'deg'}}><b>{pct}%</b></div><div className="encourage"><Sparkles/><b>{pct===100?'You showed up for yourself.':pct>=50?'Good momentum. Keep going.':'Start with one small win.'}</b></div></section>{err&&<p className="error">{err}</p>}<div className="routinegrid">{cats.map(c=>{let group=items.filter(x=>x.category===c);return group.length?<section className="panel"><div className="sect"><h3>{c}</h3><small>{group.filter(x=>x.completed).length}/{group.length}</small></div>{group.map(x=><button className={'check '+(x.completed?'yes':'')} onClick={()=>toggle(x)}>{x.completed?<CheckCircle2/>:<Circle/>}<span><b>{x.name}</b><small>{x.description}</small></span></button>)}</section>:null})}</div><section className="panel"><h3>Daily reflection</h3><form onSubmit={save}><textarea rows="3" value={memo} onChange={e=>M(e.target.value)} placeholder="What went well today? What can improve tomorrow?"/><button className="primary">Save note</button></form>{notes.map(n=><p className="saved"><b>{n.title}</b><br/>{n.content}</p>)}</section></>}
function Analytics(){const[s,S]=useState(new Date(new Date().getFullYear(),new Date().getMonth(),1).toLocaleDateString('en-CA')),[e,E]=useState(today()),[cat,C]=useState(''),[rid,R]=useState(''),[rs,RS]=useState([]),[data,D]=useState({daily:[],weekly:[],categories:[],total_completed:0});useEffect(()=>{api.get('/routines').then(x=>RS(x.data))},[]);useEffect(()=>{api.get('/analytics',{params:{start:s,end:e,category:cat||undefined,routine_id:rid||undefined}}).then(x=>D(x.data))},[s,e,cat,rid]);return <><div className="heading"><div><p className="eyebrow">MEASURE WHAT MATTERS</p><h1>Your <i>analytics</i></h1><p className="muted">Weeks run Sunday to Saturday; Saturday is the week end.</p></div></div><section className="panel filters"><label>From<input type="date" value={s} onChange={x=>S(x.target.value)}/></label><label>To<input type="date" value={e} onChange={x=>E(x.target.value)}/></label><label>Category<select value={cat} onChange={x=>C(x.target.value)}><option value="">All</option>{cats.map(c=><option>{c}</option>)}</select></label><label>Routine<select value={rid} onChange={x=>R(x.target.value)}><option value="">All</option>{rs.map(r=><option value={r.id}>{r.name}</option>)}</select></label></section><div className="metrics"><Metric label="COMPLETIONS" value={data.total_completed}/><Metric label="ACTIVE DAYS" value={data.daily.length}/><Metric label="WEEKS TRACKED" value={data.weekly.length}/></div><div className="charts"><section className="panel"><h3>Daily progress</h3><div className="chart"><ResponsiveContainer><AreaChart data={data.daily}><CartesianGrid stroke="#203b4c" strokeDasharray="3 3"/><XAxis dataKey="date"/><YAxis allowDecimals={false}/><Tooltip/><Area dataKey="completed" stroke="#25c5b3" fill="#25c5b344"/></AreaChart></ResponsiveContainer></div></section><section className="panel"><h3>Category balance</h3><div className="chart"><ResponsiveContainer><PieChart><Pie data={data.categories} dataKey="completed" nameKey="category" innerRadius={45} outerRadius={85}>{data.categories.map((x,i)=><Cell fill={['#25c5b3','#5d8dee','#a78bfa','#f3b45d'][i%4]}/>)}</Pie><Tooltip/></PieChart></ResponsiveContainer></div></section><section className="panel fullchart"><h3>Weekly consistency · Sunday–Saturday</h3><div className="chart"><ResponsiveContainer><BarChart data={data.weekly}><CartesianGrid stroke="#203b4c" strokeDasharray="3 3"/><XAxis dataKey="week_start"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="completed" fill="#25c5b3" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></div>{data.weekly.map(w=><small>{w.week_start} to {w.week_end} · {w.completed} completed<br/></small>)}</section></div></>}
function Metric({label,value}){return <section className="panel metric"><small>{label}</small><b>{value}</b></section>}
function Routines(){const[rs,R]=useState([]),[name,N]=useState(''),[cat,C]=useState('Food'),[desc,D]=useState(''),[err,E]=useState('');async function load(){R((await api.get('/routines')).data)}useEffect(()=>{load()},[]);async function add(e){e.preventDefault();try{await api.post('/routines',{name,category:cat,description:desc});N('');D('');load()}catch(x){E(x.message)}}async function archive(id){if(window.confirm('Archive this routine? History remains.')){await api.delete('/routines/'+id);load()}}return <><div className="heading"><div><p className="eyebrow">BUILD YOUR SYSTEM</p><h1>Manage <i>routines</i></h1></div></div><section className="panel"><h3>Add a routine</h3><form className="routineform" onSubmit={add}><label>Name<input required value={name} onChange={e=>N(e.target.value)}/></label><label>Category<select value={cat} onChange={e=>C(e.target.value)}>{cats.map(c=><option>{c}</option>)}</select></label><label>Description<input value={desc} onChange={e=>D(e.target.value)}/></label><button className="primary">Add</button></form>{err&&<p className="error">{err}</p>}</section><section className="panel"><h3>Your routines</h3>{cats.map(c=><div className="admin"><h4>{c}</h4>{rs.filter(r=>r.category===c).map(r=><div><span><b>{r.name}</b><small>{r.description}</small></span><small>{r.active?'Active':'Archived'}</small>{r.active&&<button className="link" onClick={()=>archive(r.id)}>Archive</button>}</div>)}</div>)}</section></>}
function Notes(){const[ns,N]=useState([]),[q,Q]=useState(''),[a,A]=useState(''),[err,E]=useState(''),[busy,B]=useState(false);async function load(){N((await api.get('/notes')).data)}useEffect(()=>{load()},[]);async function ask(e){e.preventDefault();B(true);A('');E('');try{let r=await fetch('/api/stream/notes-assistant?q='+encodeURIComponent(q),{credentials:'include'});if(!r.ok)throw Error('Could not search notes');let reader=r.body.getReader(),decoder=new TextDecoder(),buf='';while(true){let{done,value}=await reader.read();if(done)break;buf+=decoder.decode(value);let parts=buf.split('\\n\\n');buf=parts.pop();for(let p of parts){let line=p.split('\\n').find(x=>x.startsWith('data: '));if(line){let ev=JSON.parse(line.slice(6));if(ev.delta)A(old=>old+ev.delta)}}}}catch(x){E(x.message)}finally{B(false)}}async function del(id){if(window.confirm('Delete this note?')){await api.delete('/notes/'+id);load()}}return <><div className="heading"><div><p className="eyebrow">YOUR PERSONAL KNOWLEDGE</p><h1>Notes & <i>reflections</i></h1><p className="muted">Search only saved notes. Tracker records are excluded from RAG.</p></div></div><section className="panel"><div className="sect"><h3>Ask your notes</h3><em>NOTES ONLY</em></div><form className="ask" onSubmit={ask}><input value={q} onChange={e=>Q(e.target.value)} placeholder="What did I write about my goals?" required/><button className="primary" disabled={busy}>{busy?'Searching…':'Ask'}</button></form>{err&&<p className="error">{err}</p>}{a&&<pre className="answer">{a}</pre>}</section><section className="panel"><h3>Saved notes · {ns.length}</h3>{ns.map(n=><article className="note"><div><b>{n.title}</b><small>{n.date}</small></div><p>{n.content}</p><button className="link" onClick={()=>del(n.id)}>Delete</button></article>)}</section></>}
function SettingsPage({user,setUser}){const[z,Z]=useState(user.timezone),[msg,M]=useState(''),[err,E]=useState('');async function save(e){e.preventDefault();try{let r=await api.put('/settings',{timezone:z});setUser(r.data);M('Timezone saved. The day changes at local midnight.')}catch(x){E(x.message)}}return <><div className="heading"><div><p className="eyebrow">ACCOUNT PREFERENCES</p><h1>Settings</h1></div></div><section className="panel settings"><h3>Timezone</h3><p className="muted">Browser detected: {tz()}</p><form onSubmit={save}><label>IANA timezone<input value={z} onChange={e=>Z(e.target.value)} required/></label><button className="primary">Save timezone</button></form>{msg&&<p className="success">{msg}</p>}{err&&<p className="error">{err}</p>}<hr/><b>History and week logic</b><p className="muted">The day rolls over at midnight in this timezone. Previous days are preserved. Weeks always run Sunday through Saturday.</p><hr/><b>Privacy</b><p className="muted">Private password-protected account. Disable registration after creating your account.</p></section></>}
function Inner(){const[u,U]=useState(null),[loading,L]=useState(true);useEffect(()=>{api.get('/auth/me').then(r=>U(r.data.user)).catch(()=>{}).finally(()=>L(false))},[]);async function logout(){await api.post('/auth/logout');U(null)}if(loading)return <div className="auth">Loading Ash Streak…</div>;if(!u)return <Auth done={U}/>;return <Layout user={u} logout={logout}><Routes>
  <Route path="/" element={<Today />} />
  <Route path="/analytics" element={<Analytics />} />
  <Route path="/notes" element={<Notes />} />
  <Route path="/routines" element={<Routines />} />
  <Route
    path="/settings"
    element={<SettingsPage user={u} setUser={U} />}
  />
  <Route
    path="/admin"
    element={
      u.is_admin
        ? <Admin />
        : <Navigate to="/" replace />
    }
  />
  <Route path="*" element={<Navigate to="/" replace />} />
</Routes></Layout>}
export default function App(){return <BrowserRouter><Inner/></BrowserRouter>}
