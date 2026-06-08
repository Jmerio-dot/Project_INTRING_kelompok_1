import codecs

with codecs.open('dashboard.html', 'r', 'utf-8') as f:
    d = f.read()
with codecs.open('projects.html', 'r', 'utf-8') as f:
    p = f.read()

d_modal = d.split('<!-- CREATE PROJECT WIZARD MODAL -->')[1].split('<script src="app.js">')[0]
p_parts = p.split('CREATE PROJECT WIZARD MODAL')

if len(p_parts) > 1:
    p_after_modal = p_parts[1].split('<script src="app.js">')[1]
    last_comment = p_parts[0].rfind('<!--')
    p = p_parts[0][:last_comment] + '<!-- CREATE PROJECT WIZARD MODAL -->' + d_modal + '<script src="app.js">' + p_after_modal

d_js = d.split('Wizard State')[1].split('async function fetchDashboardData()')[0]
p_js_parts = p.split('WIZARD STATE')

if len(p_js_parts) > 1:
    p_after_js = p_js_parts[1].split('window.openWizard = openWizard;')[1]
    last_comment_js = p_js_parts[0].rfind('//')
    # wait, dashboard JS ends with createProject, we need to add the exposes
    exposes = '\n  window.openWizard = openWizard;\n' + p_after_js
    p = p_js_parts[0][:last_comment_js] + '// \u2500\u2500 Wizard State' + d_js + exposes

with codecs.open('projects.html', 'w', 'utf-8') as f:
    f.write(p)