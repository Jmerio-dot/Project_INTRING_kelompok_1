const fs = require('fs');
let code = fs.readFileSync('server.js', 'utf8');

// 1. Add parseIssue helper
if (!code.includes('function parseIssue')) {
    code = code.replace("const wrap = fn => (req, res) => fn(req, res).catch(e => res.status(500).json({ error: e.message }));", 
`const wrap = fn => (req, res) => fn(req, res).catch(e => res.status(500).json({ error: e.message }));

function parseIssue(i) {
  if(!i) return i;
  try { if(typeof i.meaningful_objectives === 'string') i.meaningful_objectives = JSON.parse(i.meaningful_objectives); } catch(e){}
  try { if(typeof i.intelligence_experience === 'string') i.intelligence_experience = JSON.parse(i.intelligence_experience); } catch(e){}
  try { if(typeof i.intelligence_implementation === 'string') i.intelligence_implementation = JSON.parse(i.intelligence_implementation); } catch(e){}
  return i;
}`);
}

// 2. Parse issues in /api/projects/:id/transcript
code = code.replace('return { ...issue, attachments };', 'return parseIssue({ ...issue, attachments });');

// 3. Update POST /api/projects/:id/issues
const postBodyOld = 'const { title, description, type, status, priority, assignee_id, sprint_id, labels, story_points, due_date } = req.body;';
const postBodyNew = 'const { title, description, type, status, priority, assignee_id, sprint_id, labels, story_points, due_date, meaningful_objectives, intelligence_experience, intelligence_implementation } = req.body;';
code = code.replace(postBodyOld, postBodyNew);

const insertOld = 'const r = await db.run(`INSERT INTO issues (project_id,sprint_id,issue_key,title,description,type,status,priority,assignee_id,reporter_id,labels,story_points,due_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,\n    [req.params.id, sprint_id||null, key, title, description||\'\', type||\'task\', status||\'todo\', priority||\'medium\', assignee_id||null, req.user.id, labels||\'\', story_points||null, due_date||null, now, now]);';

const insertNew = 'const r = await db.run(`INSERT INTO issues (project_id,sprint_id,issue_key,title,description,type,status,priority,assignee_id,reporter_id,labels,story_points,due_date,meaningful_objectives,intelligence_experience,intelligence_implementation,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,\n    [req.params.id, sprint_id||null, key, title, description||\'\', type||\'task\', status||\'todo\', priority||\'medium\', assignee_id||null, req.user.id, labels||\'\', story_points||null, due_date||null, JSON.stringify(meaningful_objectives||{}), JSON.stringify(intelligence_experience||{}), JSON.stringify(intelligence_implementation||{}), now, now]);';

code = code.replace(insertOld, insertNew);

// 4. Update PUT /api/issues/:id (for completeness)
const putBodyOld = 'const { title, description, type, status, priority, assignee_id, sprint_id, labels, story_points, due_date } = req.body;';
// Already replaced postBodyOld, which matches putBodyOld, but replaceAll or second replacement
code = code.replace(putBodyOld, postBodyNew);

const updateOld = 'await db.run(\'UPDATE issues SET title=?,description=?,type=?,status=?,priority=?,assignee_id=?,sprint_id=?,labels=?,story_points=?,due_date=?,updated_at=? WHERE id=?\',\n    [title, description, type, status, priority, assignee_id||null, sprint_id||null, labels, story_points||null, due_date||null, now, req.params.id]);';

const updateNew = 'await db.run(\'UPDATE issues SET title=?,description=?,type=?,status=?,priority=?,assignee_id=?,sprint_id=?,labels=?,story_points=?,due_date=?,meaningful_objectives=?,intelligence_experience=?,intelligence_implementation=?,updated_at=? WHERE id=?\',\n    [title, description, type, status, priority, assignee_id||null, sprint_id||null, labels, story_points||null, due_date||null, JSON.stringify(meaningful_objectives||{}), JSON.stringify(intelligence_experience||{}), JSON.stringify(intelligence_implementation||{}), now, req.params.id]);';

code = code.replace(updateOld, updateNew);


// 5. Parse in GET endpoints
code = code.replace('res.json(await db.get(issueQ + \' WHERE i.id=?\', [r.lastID]));', 'res.json(parseIssue(await db.get(issueQ + \' WHERE i.id=?\', [r.lastID])));');
code = code.replace('const issue = await db.get(issueQ + \' WHERE i.id=?\', [req.params.id]);', 'const issue = parseIssue(await db.get(issueQ + \' WHERE i.id=?\', [req.params.id]));');
code = code.replace('res.json(await db.get(issueQ + \' WHERE i.id=?\', [req.params.id]));', 'res.json(parseIssue(await db.get(issueQ + \' WHERE i.id=?\', [req.params.id])));');
code = code.replace('issues.forEach(i => (board[i.status] || board.todo).push(i));', 'issues.forEach(i => (board[i.status] || board.todo).push(parseIssue(i)));');

fs.writeFileSync('server.js', code, 'utf8');
console.log('Patched server.js');
