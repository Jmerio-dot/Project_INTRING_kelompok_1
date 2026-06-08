const bcrypt = require('bcryptjs');
const { db, initSchema } = require('./database');

async function seed() {
  await initSchema();
  console.log('🌱 Seeding database...');

  const now = new Date().toISOString();

  // Clear tables
  await db.run('DELETE FROM activity_log');
  await db.run('DELETE FROM comments');
  await db.run('DELETE FROM issues');
  await db.run('DELETE FROM sprints');
  await db.run('DELETE FROM project_members');
  await db.run('DELETE FROM projects');
  await db.run('DELETE FROM users');

  // Users
  const users = [
    { name: 'Muhammad Fadhil Ramadhan', email: 'fadhil@intring.ai', password: 'demo123', role: 'admin', avatar: '👨‍💼' },
    { name: 'Agnar Raka Baskara',       email: 'agnar@intring.ai',  password: 'demo123', role: 'admin', avatar: '👨‍🔬' },
    { name: 'Satria Putra',             email: 'satria@intring.ai', password: 'demo123', role: 'member', avatar: '👨‍💻' },
    { name: 'Gusty',                    email: 'gusty@intring.ai',  password: 'demo123', role: 'member', avatar: '🧑‍🚀' },
    { name: 'Demo User',                email: 'demo@intring.ai',   password: 'demo123', role: 'member', avatar: '🙂' },
  ];

  const userIds = {};
  for (const u of users) {
    const hash = bcrypt.hashSync(u.password, 10);
    const r = await db.run('INSERT INTO users (name, email, password_hash, role, avatar, created_at) VALUES (?,?,?,?,?,?)', [u.name, u.email, hash, u.role, u.avatar, now]);
    userIds[u.email] = r.lastID;
  }

  const adminId = userIds['fadhil@intring.ai'], agnarId = userIds['agnar@intring.ai'];
  const satriaId = userIds['satria@intring.ai'], gustyId = userIds['gusty@intring.ai'], demoId = userIds['demo@intring.ai'];

  // Projects
  const p1 = await db.run('INSERT INTO projects (name,key,description,type,owner_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
    ['AI Platform v2','AIP','Next-generation AI platform rebuild with microservices architecture.','scrum',adminId,'active',now,now]);
  const p2 = await db.run('INSERT INTO projects (name,key,description,type,owner_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
    ['Neural Security Suite','NSS','AI-powered security monitoring and threat detection system.','kanban',agnarId,'active',now,now]);
  const p3 = await db.run('INSERT INTO projects (name,key,description,type,owner_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)',
    ['Data Engineering Hub','DEH','Centralized data pipeline and ETL management platform.','scrum',demoId,'active',now,now]);

  const pid1 = p1.lastID, pid2 = p2.lastID, pid3 = p3.lastID;

  // Members
  const members = [
    [pid1,adminId,'admin'],[pid1,agnarId,'member'],[pid1,satriaId,'member'],[pid1,demoId,'member'],
    [pid2,agnarId,'admin'],[pid2,adminId,'member'],[pid2,gustyId,'member'],[pid2,demoId,'member'],
    [pid3,demoId,'admin'],[pid3,satriaId,'member'],[pid3,gustyId,'member'],
  ];
  for (const [p,u,r] of members) await db.run('INSERT OR IGNORE INTO project_members (project_id,user_id,role) VALUES (?,?,?)',[p,u,r]);

  // Sprints
  const s1 = await db.run('INSERT INTO sprints (project_id,name,goal,status,start_date,end_date,created_at) VALUES (?,?,?,?,?,?,?)',
    [pid1,'Sprint 1 – Foundation','Set up base infrastructure and CI/CD pipeline','done','2026-04-01','2026-04-14',now]);
  const s2 = await db.run('INSERT INTO sprints (project_id,name,goal,status,start_date,end_date,created_at) VALUES (?,?,?,?,?,?,?)',
    [pid1,'Sprint 2 – Core Features','Implement authentication, project CRUD, and board','active','2026-04-15','2026-04-28',now]);
  const s3 = await db.run('INSERT INTO sprints (project_id,name,goal,status,start_date,end_date,created_at) VALUES (?,?,?,?,?,?,?)',
    [pid1,'Sprint 3 – Analytics','Build reporting dashboard and analytics module','planning','2026-04-29','2026-05-12',now]);
  const s4 = await db.run('INSERT INTO sprints (project_id,name,goal,status,start_date,end_date,created_at) VALUES (?,?,?,?,?,?,?)',
    [pid3,'Sprint 1 – Pipeline Setup','Configure ingestion pipelines and data warehouse','active','2026-04-20','2026-05-04',now]);

  const s1id=s1.lastID, s2id=s2.lastID, s3id=s3.lastID, s4id=s4.lastID;

  async function mkIssue(pid,sid,key,title,desc,type,status,priority,assignee,reporter,labels,sp,due) {
    const r = await db.run(`INSERT INTO issues (project_id,sprint_id,issue_key,title,description,type,status,priority,assignee_id,reporter_id,labels,story_points,due_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
      [pid,sid,key,title,desc,type,status,priority,assignee,reporter,labels,sp,due,now,now]);
    return r.lastID;
  }

  const i3 = await mkIssue(pid1,s1id,'AIP-1','Setup Docker & Kubernetes cluster','Configure K8s cluster on AWS EKS with auto-scaling.','task','done','high',satriaId,adminId,'infra,devops',5,'2026-04-05');
  await mkIssue(pid1,s1id,'AIP-2','Configure CI/CD with GitHub Actions','Setup automated testing and deployment pipelines.','task','done','high',agnarId,adminId,'devops',3,'2026-04-10');
  const i4 = await mkIssue(pid1,s2id,'AIP-3','Implement JWT Authentication','Build login/register endpoints with JWT token management.','story','done','critical',adminId,adminId,'backend,auth',8,'2026-04-18');
  const i5 = await mkIssue(pid1,s2id,'AIP-4','Build Project Management API','CRUD endpoints for projects, members, and settings.','story','in_progress','high',agnarId,adminId,'backend,api',13,'2026-04-25');
  await mkIssue(pid1,s2id,'AIP-5','Kanban Board drag-and-drop UI','Interactive board with drag-and-drop issue cards.','story','in_progress','high',satriaId,adminId,'frontend,ui',8,'2026-04-26');
  await mkIssue(pid1,s2id,'AIP-6','Issue Detail Page','Full issue view with comments, edit, and history.','task','in_review','medium',demoId,adminId,'frontend',5,'2026-04-27');
  await mkIssue(pid1,s2id,'AIP-7','Fix sprint filtering bug','Issues not filtered correctly by sprint on backlog.','bug','todo','high',agnarId,satriaId,'bug,backend',2,'2026-04-28');
  await mkIssue(pid1,s3id,'AIP-8','Analytics Dashboard','Build charts for velocity, burndown, and throughput.','epic','todo','medium',adminId,adminId,'analytics,frontend',21,'2026-05-10');
  await mkIssue(pid1,null,'AIP-9','User notification system','Email and in-app notifications for issue updates.','story','todo','low',null,adminId,'notifications',8,null);
  await mkIssue(pid1,null,'AIP-10','Mobile responsive optimization','Ensure all pages are mobile-friendly.','task','todo','low',null,satriaId,'ui,mobile',3,null);

  await mkIssue(pid2,null,'NSS-1','Threat detection model training','Train ML model on labeled security event dataset.','story','done','critical',agnarId,agnarId,'ml,security',13,'2026-04-20');
  await mkIssue(pid2,null,'NSS-2','Real-time log ingestion pipeline','Stream security logs via Kafka to processing engine.','task','in_progress','high',gustyId,agnarId,'backend,kafka',8,'2026-05-05');
  await mkIssue(pid2,null,'NSS-3','Alert dashboard UI','Display real-time security alerts with severity levels.','story','in_progress','high',demoId,agnarId,'frontend',8,'2026-05-06');
  await mkIssue(pid2,null,'NSS-4','False positive rate reduction','Tune model thresholds to reduce false positives by 30%.','task','in_review','medium',agnarId,agnarId,'ml,research',5,'2026-05-08');
  await mkIssue(pid2,null,'NSS-5','API rate limiting middleware','Add rate limiting to prevent DDoS attacks on API.','task','todo','high',gustyId,agnarId,'backend,security',3,'2026-05-10');
  await mkIssue(pid2,null,'NSS-6','Penetration testing report','Conduct full pen test and document vulnerabilities.','task','todo','medium',null,agnarId,'security,testing',5,'2026-05-15');

  await mkIssue(pid3,s4id,'DEH-1','Airflow DAG setup','Configure Apache Airflow for pipeline orchestration.','task','done','high',satriaId,demoId,'infra,airflow',5,'2026-04-25');
  await mkIssue(pid3,s4id,'DEH-2','PostgreSQL data warehouse schema','Design and implement DWH schema for analytics.','story','in_progress','high',gustyId,demoId,'database',8,'2026-05-03');
  await mkIssue(pid3,s4id,'DEH-3','ETL for user events','Build ETL pipeline for user clickstream data.','story','in_progress','medium',satriaId,demoId,'etl,python',5,'2026-05-04');
  await mkIssue(pid3,s4id,'DEH-4','Data quality monitoring','Implement data quality checks and alerting.','task','todo','medium',null,demoId,'monitoring',3,'2026-05-10');
  await mkIssue(pid3,null,'DEH-5','Spark cluster optimization','Tune Spark jobs for better performance and cost.','task','todo','low',null,demoId,'spark,optimization',5,null);

  // Comments
  const comments = [
    [i5, adminId,  'Starting work on the project endpoints today. Will handle member management in the same PR.'],
    [i5, agnarId,  'Looks good. Make sure we add proper validation for the project key field (unique, uppercase).'],
    [i5, satriaId, 'Should we also add pagination for the project list endpoint?'],
    [i5, adminId,  'Good point @Satria, adding cursor-based pagination. Will update the API spec.'],
    [i4, adminId,  'JWT auth is live. Using 7-day expiry with refresh token support.'],
    [i4, agnarId,  'Remember to add rate limiting on the /auth/login endpoint.'],
  ];
  for (const [iid, uid, content] of comments) {
    await db.run('INSERT INTO comments (issue_id,user_id,content,created_at) VALUES (?,?,?,?)', [iid, uid, content, now]);
  }

  // Activity
  const activities = [
    [adminId,  pid1, i4, 'status_changed', 'Changed status from in_progress to done'],
    [agnarId,  pid1, i5, 'assigned',       'Assigned to Agnar Raka Baskara'],
    [satriaId, pid1, null,'sprint_created', 'Sprint 2 – Core Features started'],
    [demoId,   pid3, null,'project_created','Created project: Data Engineering Hub'],
    [agnarId,  pid2, null,'issue_created',  'Created NSS-4: False positive rate reduction'],
  ];
  for (const [uid, pid, iid, action, detail] of activities) {
    await db.run('INSERT INTO activity_log (user_id,project_id,issue_id,action,detail,created_at) VALUES (?,?,?,?,?,?)', [uid, pid, iid, action, detail, now]);
  }

  console.log('✅ Database seeded successfully!');
  console.log('\nDemo accounts (password: demo123):');
  users.forEach(u => console.log(` - ${u.email}`));
  process.exit(0);
}

seed().catch(e => { console.error('Seed failed:', e); process.exit(1); });
