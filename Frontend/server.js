const express = require('express');
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const multer = require('multer');
const { db, initSchema } = require('./db/database');

const app = express();
const PORT = 3000;
const JWT_SECRET = 'intring-secret-2026';

// ── Upload Setup ─────────────────────────────────────────────────────────────
const UPLOADS_DIR = path.join(__dirname, 'uploads');
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${Date.now()}-${Math.random().toString(36).slice(2)}${ext}`);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
});

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));
app.use('/uploads', express.static(UPLOADS_DIR));

// ── Auth Middleware ─────────────────────────────────────────────────────────
const auth = (req, res, next) => {
  const h = req.headers.authorization;
  if (!h?.startsWith('Bearer ')) return res.status(401).json({ error: 'Unauthorized' });
  try { req.user = jwt.verify(h.split(' ')[1], JWT_SECRET); next(); }
  catch { res.status(401).json({ error: 'Invalid token' }); }
};

const logActivity = (uid, pid, iid, action, detail) =>
  db.run('INSERT INTO activity_log (user_id,project_id,issue_id,action,detail,created_at) VALUES (?,?,?,?,?,?)',
    [uid, pid||null, iid||null, action, detail||'', new Date().toISOString()]).catch(()=>{});

const wrap = fn => (req, res) => fn(req, res).catch(e => res.status(500).json({ error: e.message }));

function parseIssue(i) {
  if(!i) return i;
  try { if(typeof i.meaningful_objectives === 'string') i.meaningful_objectives = JSON.parse(i.meaningful_objectives); } catch(e){}
  try { if(typeof i.intelligence_experience === 'string') i.intelligence_experience = JSON.parse(i.intelligence_experience); } catch(e){}
  try { if(typeof i.intelligence_implementation === 'string') i.intelligence_implementation = JSON.parse(i.intelligence_implementation); } catch(e){}
  return i;
}

// ── AUTH ────────────────────────────────────────────────────────────────────
app.post('/api/auth/login', wrap(async (req, res) => {
  const { email, password } = req.body;
  const user = await db.get('SELECT * FROM users WHERE email=?', [email]);
  if (!user || !bcrypt.compareSync(password, user.password_hash))
    return res.status(401).json({ error: 'Email atau kata sandi salah' });
  const token = jwt.sign({ id: user.id, email: user.email, name: user.name, role: user.role, avatar: user.avatar }, JWT_SECRET, { expiresIn: '7d' });
  const { password_hash, ...u } = user;
  res.json({ token, user: u });
}));

app.post('/api/auth/register', wrap(async (req, res) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password) return res.status(400).json({ error: 'Semua field wajib diisi' });
  if (await db.get('SELECT id FROM users WHERE email=?', [email])) return res.status(400).json({ error: 'Email sudah terdaftar' });
  const now = new Date().toISOString();
  const r = await db.run('INSERT INTO users (name,email,password_hash,role,avatar,created_at) VALUES (?,?,?,?,?,?)',
    [name, email, bcrypt.hashSync(password, 10), 'member', '👤', now]);
  const user = await db.get('SELECT id,name,email,role,avatar,created_at FROM users WHERE id=?', [r.lastID]);
  const token = jwt.sign({ id: user.id, email: user.email, name: user.name, role: user.role, avatar: user.avatar }, JWT_SECRET, { expiresIn: '7d' });
  res.json({ token, user });
}));

app.get('/api/auth/me', auth, wrap(async (req, res) => {
  res.json(await db.get('SELECT id,name,email,role,avatar,bio,location,website,profile_photo,created_at FROM users WHERE id=?', [req.user.id]));
}));

// ── PROFILE ─────────────────────────────────────────────────────────────────
app.put('/api/profile', auth, wrap(async (req, res) => {
  const { name, bio, location, website } = req.body;
  await db.run('UPDATE users SET name=?,bio=?,location=?,website=? WHERE id=?',
    [name, bio || '', location || '', website || '', req.user.id]);
  res.json(await db.get('SELECT id,name,email,role,avatar,bio,location,website,profile_photo,created_at FROM users WHERE id=?', [req.user.id]));
}));

app.post('/api/profile/photo', auth, upload.single('photo'), wrap(async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
  const photoUrl = `/uploads/${req.file.filename}`;
  await db.run('UPDATE users SET profile_photo=? WHERE id=?', [photoUrl, req.user.id]);
  res.json({ profile_photo: photoUrl });
}));

// ── USERS ───────────────────────────────────────────────────────────────────
app.get('/api/users', auth, wrap(async (req, res) => {
  res.json(await db.all('SELECT id,name,email,role,avatar FROM users ORDER BY name'));
}));

// ── PROJECTS ────────────────────────────────────────────────────────────────
app.get('/api/projects', auth, wrap(async (req, res) => {
  res.json(await db.all(`
    SELECT p.*, u.name as owner_name,
      (SELECT COUNT(*) FROM issues WHERE project_id=p.id) as issue_count,
      (SELECT COUNT(*) FROM issues WHERE project_id=p.id AND status!='done') as open_issues
    FROM projects p LEFT JOIN users u ON p.owner_id=u.id
    LEFT JOIN project_members pm ON pm.project_id=p.id
    WHERE p.owner_id=? OR pm.user_id=?
    GROUP BY p.id ORDER BY p.updated_at DESC
  `, [req.user.id, req.user.id]));
}));

app.post('/api/projects', auth, wrap(async (req, res) => {
  const { name, key, description, type } = req.body;
  if (!name || !key) return res.status(400).json({ error: 'Name and key are required' });
  const k = key.toUpperCase().replace(/[^A-Z0-9]/g,'');
  if (await db.get('SELECT id FROM projects WHERE key=?', [k])) return res.status(400).json({ error: 'Project key already used' });
  const now = new Date().toISOString();
  const r = await db.run('INSERT INTO projects (name,key,description,type,owner_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
    [name, k, description||'', type||'scrum', req.user.id, 'active', now, now]);
  await db.run('INSERT OR IGNORE INTO project_members (project_id,user_id,role) VALUES (?,?,?)', [r.lastID, req.user.id, 'admin']);
  logActivity(req.user.id, r.lastID, null, 'project_created', `Created project: ${name}`);
  res.json(await db.get('SELECT * FROM projects WHERE id=?', [r.lastID]));
}));

app.get('/api/projects/:id', auth, wrap(async (req, res) => {
  const p = await db.get('SELECT p.*,u.name as owner_name FROM projects p LEFT JOIN users u ON p.owner_id=u.id WHERE p.id=?', [req.params.id]);
  if (!p) return res.status(404).json({ error: 'Project not found' });
  res.json(p);
}));

app.put('/api/projects/:id', auth, wrap(async (req, res) => {
  const { name, description, status } = req.body;
  await db.run('UPDATE projects SET name=?,description=?,status=?,updated_at=? WHERE id=?', [name, description, status, new Date().toISOString(), req.params.id]);
  res.json(await db.get('SELECT * FROM projects WHERE id=?', [req.params.id]));
}));

app.post('/api/projects/:id/complete', auth, wrap(async (req, res) => {
  const pendingIssues = await db.get("SELECT COUNT(*) as c FROM issues WHERE project_id=? AND status!='done'", [req.params.id]);
  if (pendingIssues.c > 0) {
    return res.status(400).json({ error: `Terdapat ${pendingIssues.c} issue yang belum berstatus "Done". Silakan selesaikan semua issue terlebih dahulu.` });
  }
  await db.run("UPDATE projects SET status='done', updated_at=? WHERE id=?", [new Date().toISOString(), req.params.id]);
  res.json({ success: true });
}));

app.delete('/api/projects/:id', auth, wrap(async (req, res) => {
  // Delete activity_log first (no CASCADE defined on project_id FK)
  await db.run('DELETE FROM activity_log WHERE project_id=?', [req.params.id]);
  await db.run('DELETE FROM projects WHERE id=?', [req.params.id]);
  res.json({ success: true });
}));

// ── TRANSCRIPT ───────────────────────────────────────────────────────────────
app.get('/api/projects/:id/transcript', auth, wrap(async (req, res) => {
  const p = await db.get(`SELECT p.*,u.name as owner_name FROM projects p LEFT JOIN users u ON p.owner_id=u.id WHERE p.id=?`, [req.params.id]);
  if (!p) return res.status(404).json({ error: 'Project not found' });

  const issues = await db.all(`
    SELECT i.*,u.name as assignee_name,r.name as reporter_name,s.name as sprint_name
    FROM issues i
    LEFT JOIN users u ON i.assignee_id=u.id
    LEFT JOIN users r ON i.reporter_id=r.id
    LEFT JOIN sprints s ON i.sprint_id=s.id
    WHERE i.project_id=?
    ORDER BY i.created_at ASC
  `, [req.params.id]);

  // For each issue get attachments
  const issuesWithAttachments = await Promise.all(issues.map(async issue => {
    const attachments = await db.all(
      'SELECT a.*,u.name as uploader_name FROM attachments a JOIN users u ON a.user_id=u.id WHERE a.issue_id=? ORDER BY a.created_at ASC',
      [issue.id]
    );
    return parseIssue({ ...issue, attachments });
  }));

  res.json({ project: p, issues: issuesWithAttachments });
}));



app.get('/api/projects/:id/members', auth, wrap(async (req, res) => {
  res.json(await db.all('SELECT u.id,u.name,u.email,u.avatar,pm.role as project_role FROM project_members pm JOIN users u ON pm.user_id=u.id WHERE pm.project_id=?', [req.params.id]));
}));

app.post('/api/projects/:id/members', auth, wrap(async (req, res) => {
  const { user_id, role } = req.body;
  await db.run('INSERT OR IGNORE INTO project_members (project_id,user_id,role) VALUES (?,?,?)', [req.params.id, user_id, role||'member']);
  res.json({ success: true });
}));

app.delete('/api/projects/:id/members/:uid', auth, wrap(async (req, res) => {
  await db.run('DELETE FROM project_members WHERE project_id=? AND user_id=?', [req.params.id, req.params.uid]);
  res.json({ success: true });
}));

// ── SPRINTS ─────────────────────────────────────────────────────────────────
app.get('/api/projects/:id/sprints', auth, wrap(async (req, res) => {
  res.json(await db.all(`
    SELECT s.*,
      (SELECT COUNT(*) FROM issues WHERE sprint_id=s.id) as issue_count,
      (SELECT COUNT(*) FROM issues WHERE sprint_id=s.id AND status='done') as done_count
    FROM sprints s WHERE s.project_id=? ORDER BY s.created_at ASC
  `, [req.params.id]));
}));

app.post('/api/projects/:id/sprints', auth, wrap(async (req, res) => {
  const { name, goal, start_date, end_date } = req.body;
  const r = await db.run('INSERT INTO sprints (project_id,name,goal,status,start_date,end_date,created_at) VALUES (?,?,?,?,?,?,?)',
    [req.params.id, name, goal||'', 'planning', start_date||null, end_date||null, new Date().toISOString()]);
  res.json(await db.get('SELECT * FROM sprints WHERE id=?', [r.lastID]));
}));

app.put('/api/sprints/:id', auth, wrap(async (req, res) => {
  const { name, goal, status, start_date, end_date } = req.body;
  await db.run('UPDATE sprints SET name=?,goal=?,status=?,start_date=?,end_date=? WHERE id=?', [name, goal, status, start_date||null, end_date||null, req.params.id]);
  res.json(await db.get('SELECT * FROM sprints WHERE id=?', [req.params.id]));
}));

app.delete('/api/sprints/:id', auth, wrap(async (req, res) => {
  await db.run('UPDATE issues SET sprint_id=NULL WHERE sprint_id=?', [req.params.id]);
  await db.run('DELETE FROM sprints WHERE id=?', [req.params.id]);
  res.json({ success: true });
}));

// ── ISSUES ──────────────────────────────────────────────────────────────────
const issueQ = `SELECT i.*,u.name as assignee_name,u.avatar as assignee_avatar,r.name as reporter_name,s.name as sprint_name,p.name as project_name,p.key as project_key FROM issues i LEFT JOIN users u ON i.assignee_id=u.id LEFT JOIN users r ON i.reporter_id=r.id LEFT JOIN sprints s ON i.sprint_id=s.id LEFT JOIN projects p ON i.project_id=p.id`;

app.get('/api/projects/:id/issues', auth, wrap(async (req, res) => {
  const { sprint, status, assignee, type, backlog } = req.query;
  let q = issueQ + ' WHERE i.project_id=?';
  const p = [req.params.id];
  if (sprint)          { q += ' AND i.sprint_id=?'; p.push(sprint); }
  if (backlog==='true'){ q += ' AND i.sprint_id IS NULL'; }
  if (status)          { q += ' AND i.status=?'; p.push(status); }
  if (assignee)        { q += ' AND i.assignee_id=?'; p.push(assignee); }
  if (type)            { q += ' AND i.type=?'; p.push(type); }
  q += ' ORDER BY i.priority_order ASC, i.created_at DESC';
  res.json(await db.all(q, p));
}));

app.get('/api/projects/:id/board', auth, wrap(async (req, res) => {
  const { sprint_id } = req.query;
  const params = [req.params.id];
  let sc = '';
  if (sprint_id) { sc = ' AND i.sprint_id=?'; params.push(sprint_id); }
  else {
    const active = await db.get("SELECT id FROM sprints WHERE project_id=? AND status='active' LIMIT 1", [req.params.id]);
    if (active) { sc = ' AND i.sprint_id=?'; params.push(active.id); }
  }
  const issues = await db.all(issueQ + ` WHERE i.project_id=? ${sc} ORDER BY i.priority_order ASC`, params);
  const board = { todo:[], in_progress:[], in_review:[], done:[] };
  issues.forEach(i => (board[i.status] || board.todo).push(parseIssue(i)));
  res.json(board);
}));

app.post('/api/projects/:id/issues', auth, wrap(async (req, res) => {
  const { title, description, type, status, priority, assignee_id, sprint_id, labels, story_points, due_date, meaningful_objectives, intelligence_experience, intelligence_implementation } = req.body;
  if (!title) return res.status(400).json({ error: 'Title is required' });
  const now = new Date().toISOString();
  const cnt = await db.get('SELECT COUNT(*) as c FROM issues WHERE project_id=?', [req.params.id]);
  const proj = await db.get('SELECT key FROM projects WHERE id=?', [req.params.id]);
  const key = `${proj.key}-${cnt.c + 1}`;
  const r = await db.run(`INSERT INTO issues (project_id,sprint_id,issue_key,title,description,type,status,priority,assignee_id,reporter_id,labels,story_points,due_date,meaningful_objectives,intelligence_experience,intelligence_implementation,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    [req.params.id, sprint_id||null, key, title, description||'', type||'task', status||'todo', priority||'medium', assignee_id||null, req.user.id, labels||'', story_points||null, due_date||null, JSON.stringify(meaningful_objectives||{}), JSON.stringify(intelligence_experience||{}), JSON.stringify(intelligence_implementation||{}), now, now]);
  await db.run('UPDATE projects SET updated_at=? WHERE id=?', [now, req.params.id]);
  logActivity(req.user.id, req.params.id, r.lastID, 'issue_created', `Created: ${title}`);
  res.json(parseIssue(await db.get(issueQ + ' WHERE i.id=?', [r.lastID])));
}));

app.get('/api/issues/:id', auth, wrap(async (req, res) => {
  const issue = parseIssue(await db.get(issueQ + ' WHERE i.id=?', [req.params.id]));
  if (!issue) return res.status(404).json({ error: 'Issue not found' });
  res.json(issue);
}));

app.put('/api/issues/:id', auth, wrap(async (req, res) => {
  const { title, description, type, status, priority, assignee_id, sprint_id, labels, story_points, due_date, meaningful_objectives, intelligence_experience, intelligence_implementation } = req.body;
  const now = new Date().toISOString();
  const old = await db.get('SELECT * FROM issues WHERE id=?', [req.params.id]);
  await db.run('UPDATE issues SET title=?,description=?,type=?,status=?,priority=?,assignee_id=?,sprint_id=?,labels=?,story_points=?,due_date=?,meaningful_objectives=?,intelligence_experience=?,intelligence_implementation=?,updated_at=? WHERE id=?',
    [title, description, type, status, priority, assignee_id||null, sprint_id||null, labels, story_points||null, due_date||null, JSON.stringify(meaningful_objectives||{}), JSON.stringify(intelligence_experience||{}), JSON.stringify(intelligence_implementation||{}), now, req.params.id]);
  if (old?.status !== status) logActivity(req.user.id, old?.project_id, req.params.id, 'status_changed', `${old?.status} → ${status}`);
  res.json(parseIssue(await db.get(issueQ + ' WHERE i.id=?', [req.params.id])));
}));

app.patch('/api/issues/:id/status', auth, wrap(async (req, res) => {
  const { status } = req.body;
  const old = await db.get('SELECT * FROM issues WHERE id=?', [req.params.id]);
  await db.run('UPDATE issues SET status=?,updated_at=? WHERE id=?', [status, new Date().toISOString(), req.params.id]);
  logActivity(req.user.id, old?.project_id, req.params.id, 'status_changed', `${old?.status} → ${status}`);
  res.json({ success: true });
}));

app.delete('/api/issues/:id', auth, wrap(async (req, res) => {
  await db.run('DELETE FROM issues WHERE id=?', [req.params.id]);
  res.json({ success: true });
}));

// ── COMMENTS ────────────────────────────────────────────────────────────────
app.get('/api/issues/:id/comments', auth, wrap(async (req, res) => {
  res.json(await db.all('SELECT c.*,u.name as user_name,u.avatar as user_avatar FROM comments c JOIN users u ON c.user_id=u.id WHERE c.issue_id=? ORDER BY c.created_at ASC', [req.params.id]));
}));

app.post('/api/issues/:id/comments', auth, wrap(async (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'Content required' });
  const r = await db.run('INSERT INTO comments (issue_id,user_id,content,created_at) VALUES (?,?,?,?)', [req.params.id, req.user.id, content, new Date().toISOString()]);
  res.json(await db.get('SELECT c.*,u.name as user_name,u.avatar as user_avatar FROM comments c JOIN users u ON c.user_id=u.id WHERE c.id=?', [r.lastID]));
}));

app.delete('/api/comments/:id', auth, wrap(async (req, res) => {
  await db.run('DELETE FROM comments WHERE id=? AND user_id=?', [req.params.id, req.user.id]);
  res.json({ success: true });
}));

// ── ATTACHMENTS ─────────────────────────────────────────────────────────────
app.get('/api/issues/:id/attachments', auth, wrap(async (req, res) => {
  res.json(await db.all(
    'SELECT a.*,u.name as uploader_name,u.avatar as uploader_avatar FROM attachments a JOIN users u ON a.user_id=u.id WHERE a.issue_id=? ORDER BY a.created_at DESC',
    [req.params.id]
  ));
}));

app.post('/api/issues/:id/attachments', auth, upload.single('file'), wrap(async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
  const now = new Date().toISOString();
  const r = await db.run(
    'INSERT INTO attachments (issue_id,user_id,filename,original_name,mimetype,size,created_at) VALUES (?,?,?,?,?,?,?)',
    [req.params.id, req.user.id, req.file.filename, req.file.originalname, req.file.mimetype, req.file.size, now]
  );
  const issue = await db.get('SELECT project_id FROM issues WHERE id=?', [req.params.id]);
  logActivity(req.user.id, issue?.project_id, req.params.id, 'file_attached', `Attached: ${req.file.originalname}`);
  res.json(await db.get('SELECT a.*,u.name as uploader_name FROM attachments a JOIN users u ON a.user_id=u.id WHERE a.id=?', [r.lastID]));
}));

app.delete('/api/attachments/:id', auth, wrap(async (req, res) => {
  const att = await db.get('SELECT * FROM attachments WHERE id=?', [req.params.id]);
  if (!att) return res.status(404).json({ error: 'Not found' });
  // Delete file from disk
  const filePath = path.join(UPLOADS_DIR, att.filename);
  if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  await db.run('DELETE FROM attachments WHERE id=?', [req.params.id]);
  res.json({ success: true });
}));

// ── DASHBOARD ───────────────────────────────────────────────────────────────
app.get('/api/dashboard', auth, wrap(async (req, res) => {
  const uid = req.user.id;
  const [tp, am, ip, ct] = await Promise.all([
    db.get('SELECT COUNT(*) as c FROM projects p LEFT JOIN project_members pm ON pm.project_id=p.id WHERE p.owner_id=? OR pm.user_id=?', [uid,uid]),
    db.get("SELECT COUNT(*) as c FROM issues WHERE assignee_id=? AND status!='done'", [uid]),
    db.get("SELECT COUNT(*) as c FROM issues WHERE assignee_id=? AND status='in_progress'", [uid]),
    db.get("SELECT COUNT(*) as c FROM issues WHERE assignee_id=? AND status='done' AND date(updated_at)=date('now')", [uid]),
  ]);
  const myIssues = await db.all(`SELECT i.*,p.name as project_name,p.key as project_key FROM issues i JOIN projects p ON i.project_id=p.id WHERE i.assignee_id=? AND i.status!='done' ORDER BY i.updated_at DESC LIMIT 8`, [uid]);
  const recentProjects = await db.all(`SELECT p.*,(SELECT COUNT(*) FROM issues WHERE project_id=p.id AND status!='done') as open_issues FROM projects p LEFT JOIN project_members pm ON pm.project_id=p.id WHERE p.owner_id=? OR pm.user_id=? GROUP BY p.id ORDER BY p.updated_at DESC LIMIT 6`, [uid,uid]);
  const recentActivity = await db.all('SELECT a.*,u.name as user_name,u.avatar as user_avatar FROM activity_log a JOIN users u ON a.user_id=u.id ORDER BY a.created_at DESC LIMIT 10');
  res.json({ totalProjects: tp.c, assignedToMe: am.c, inProgress: ip.c, completedToday: ct.c, myIssues, recentProjects, recentActivity });
}));

// ── START ───────────────────────────────────────────────────────────────────
async function start() {
  await initSchema();
  // Migrate: add profile columns if missing
  const cols = await db.all("PRAGMA table_info(users)");
  const colNames = cols.map(c => c.name);
  if (!colNames.includes('bio')) await db.run("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''").catch(()=>{});
  if (!colNames.includes('location')) await db.run("ALTER TABLE users ADD COLUMN location TEXT DEFAULT ''").catch(()=>{});
  if (!colNames.includes('website')) await db.run("ALTER TABLE users ADD COLUMN website TEXT DEFAULT ''").catch(()=>{});
  if (!colNames.includes('profile_photo')) await db.run("ALTER TABLE users ADD COLUMN profile_photo TEXT DEFAULT ''").catch(()=>{});
  app.listen(PORT, () => {
    console.log(`\n🚀 Intelligence Engineering PM`);
    console.log(`   http://localhost:${PORT}`);
    console.log(`   Login: demo@intring.ai / demo123\n`);
  });
}

start().catch(console.error);
