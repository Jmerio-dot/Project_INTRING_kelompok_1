
(async () => {
  if (!requireAuth()) return;

  const pid = new URLSearchParams(location.search).get('pid');
  if (!pid) return (location.href = '/projects.html');

  // ── Zoom ──────────────────────────────────────────────────────────────────
  let zoomPct = 75;
  function applyZoom() {
    const p = document.getElementById('paper-page');
    p.style.transform = `scale(${zoomPct / 100})`;
    document.getElementById('zoom-label').textContent = `${zoomPct}%`;
    // adjust container height so scrollbar works
    const naturalH = p.scrollHeight;
    document.getElementById('paper-container').style.minHeight = `${naturalH * zoomPct / 100 + 48}px`;
  }
  window.changeZoom = (delta) => {
    zoomPct = Math.min(150, Math.max(30, zoomPct + delta));
    applyZoom();
  };

  // ── Helpers ───────────────────────────────────────────────────────────────
  function fmtDate(str) {
    if (!str) return '–';
    return new Date(str).toLocaleDateString('id-ID', { day:'numeric', month:'long', year:'numeric' });
  }
  function fmtBytes(b) {
    if (!b) return '';
    if (b < 1024) return `${b} B`;
    if (b < 1024*1024) return `${(b/1024).toFixed(1)} KB`;
    return `${(b/1024/1024).toFixed(1)} MB`;
  }
  function esc(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
  function arr(v) { return Array.isArray(v) ? v : (typeof v === 'string' ? v.split('\n').filter(Boolean) : []); }

  // ── Load Data ─────────────────────────────────────────────────────────────
  let transcriptData = null;
  try {
    transcriptData = await apiFetch(`/projects/${pid}/transcript`);
  } catch(e) {
    document.getElementById('loading-state').innerHTML =
      `<div class="empty-state"><div class="empty-state-icon">⚠️</div><p>Gagal memuat transcript: ${e.message}</p></div>`;
    return;
  }

  const { project, issues } = transcriptData;

  // Parse project meta (stored as JSON in description field)
  let meta = null;
  try { meta = JSON.parse(project.description); } catch {}
  const desc    = meta?.description || project.description || '–';
  const obj     = meta?.objectives  || {};
  const impl    = meta?.implementation || {};
  const plan    = meta?.planning || {};

  // ── Update topbar ─────────────────────────────────────────────────────────
  document.getElementById('breadcrumb').textContent = `Projects / ${project.name}`;
  document.getElementById('page-title').textContent = `Transcript – ${project.name}`;
  document.title = `Transcript – ${project.name}`;

  await renderSidebar('projects');

  // ── Project Info Card ─────────────────────────────────────────────────────
  const totalFiles = issues.reduce((acc,i) => acc + (i.attachments?.length||0), 0);
  document.getElementById('proj-info-rows').innerHTML = `
    <div class="info-row"><span class="info-key">Nama</span><span class="info-val">${esc(project.name)}</span></div>
    <div class="info-row"><span class="info-key">Key</span><span class="info-val">${esc(project.key)}</span></div>
    <div class="info-row"><span class="info-key">Tipe</span><span class="info-val">${esc(project.type)}</span></div>
    <div class="info-row"><span class="info-key">Status</span><span class="info-val">${esc(project.status)}</span></div>
    <div class="info-row"><span class="info-key">Owner</span><span class="info-val">${esc(project.owner_name||'–')}</span></div>
    <div class="info-row"><span class="info-key">Mulai</span><span class="info-val">${fmtDate(plan.startDate)}</span></div>
    <div class="info-row"><span class="info-key">Selesai</span><span class="info-val">${fmtDate(plan.endDate)}</span></div>
  `;

  // ── Stats ──────────────────────────────────────────────────────────────────
  const doneCount   = issues.filter(i=>i.status==='done').length;
  const openCount   = issues.filter(i=>i.status!=='done').length;
  document.getElementById('stat-chips').innerHTML = `
    <span class="stat-chip">${issues.length} Issues</span>
    <span class="stat-chip green">${doneCount} Done</span>
    <span class="stat-chip amber">${openCount} Open</span>
    <span class="stat-chip">${totalFiles} File</span>
  `;
  const byType = {};
  issues.forEach(i => { byType[i.type] = (byType[i.type]||0)+1; });
  document.getElementById('issue-breakdown').innerHTML = Object.entries(byType)
    .map(([t,c]) => `<div style="display:flex;justify-content:space-between;padding:0.2rem 0;border-bottom:1px solid #f0f5fb;">
      <span>${{task:'✅ Task',story:'📗 Story',bug:'🐛 Bug',epic:'⚡ Epic'}[t]||t}</span>
      <strong style="color:var(--ocean);">${c}</strong>
    </div>`).join('') || '<span style="color:var(--muted);font-size:0.78rem;">Tidak ada issue.</span>';

  // ── Build Paper HTML ──────────────────────────────────────────────────────
  function buildPaperHTML() {
    const orgObj     = obj.organizational || {};
    const indicators = arr(obj.leading_indicators);
    const outcomes   = obj.user_outcomes || {};
    const modelProps = obj.model_properties || {};
    const supervisors= arr(plan.supervisors);
    const now = new Date().toLocaleDateString('id-ID',{day:'numeric',month:'long',year:'numeric'});

    let html = `
      <div class="tr-main-title">TRANSKRIP PROJECT<br>"${esc(project.name)}"</div>
      <div style="font-size:9pt;color:#666;margin-bottom:1rem;">Digenerate: ${now}</div>

      <!-- PLANNING -->
      <div class="tr-section">
        <div class="tr-section-title">Planning</div>
        <div class="tr-row"><span class="tr-label">Start Date :</span><span class="tr-value">${esc(plan.startDate||'—')}</span></div>
        <div class="tr-row"><span class="tr-label">End Date :</span><span class="tr-value">${esc(plan.endDate||'—')}</span></div>
    `;
    if (supervisors.length) {
      html += `<div class="tr-row"><span class="tr-label">Supervisor :</span><span class="tr-value">`;
      html += supervisors.map((s,i) => (i===0 ? esc(s) : `</span></div><div class="tr-row"><span class="tr-label"></span><span class="tr-value">• ${esc(s)}`)).join('');
      html += `</span></div>`;
    } else {
      html += `<div class="tr-row"><span class="tr-label">Supervisor :</span><span class="tr-value">—</span></div>`;
    }
    html += `
        <div class="tr-row"><span class="tr-label">Deployment :</span><span class="tr-value">${esc(plan.deployment||'—')}</span></div>
        <div class="tr-row"><span class="tr-label">Maintenance :</span><span class="tr-value">${esc(plan.maintenance||'—')}</span></div>
        <div class="tr-row"><span class="tr-label">Operations :</span><span class="tr-value">${esc(plan.operations||'—')}</span></div>
      </div>

      <!-- OBJECTIVES -->
      <div class="tr-section">
        <div class="tr-section-title">Objectives</div>
        <div class="tr-row"><span class="tr-label">Organizational :</span><span class="tr-value"><b>Tujuan:</b> ${esc(orgObj.obj||'—')}<br><b>Cara:</b> ${esc(orgObj.how||'—')}<br><b>Ukuran:</b> ${esc(orgObj.measure||'—')}</span></div>
    `;
      if (indicators.length) {
        html += `<div class="tr-row" style="margin-top:0.5rem; display:block;">
          <div class="tr-label" style="margin-bottom:0.5rem;">Leading Indicator :</div>
          <table class="tr-table">
            <thead>
              <tr>
                <th>FITUR</th>
                <th>SISTEM KITA</th>
                <th>KOMPETITOR</th>
              </tr>
            </thead>
            <tbody>
              ${indicators.map(v => `<tr>
                <td>${esc(v.col1)}</td>
                <td>${esc(v.col2||'')}</td>
                <td>${esc(v.col3||'')}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>`;
      }
      html += `
        <div class="tr-row" style="margin-top:0.5rem;"><span class="tr-label">User Outcomes :</span><span class="tr-value"><b>Tujuan:</b> ${esc(outcomes.obj||'—')}<br><b>Cara:</b> ${esc(outcomes.how||'—')}<br><b>Ukuran:</b> ${esc(outcomes.measure||'—')}</span></div>
        <div class="tr-row" style="margin-top:0.5rem;"><span class="tr-label">Model Properties :</span><span class="tr-value"><b>Spesifikasi:</b> ${esc(modelProps.obj||'—')}<br><b>Cara:</b> ${esc(modelProps.how||'—')}<br><b>Ukuran:</b> ${esc(modelProps.measure||'—')}</span></div>
      </div>
    `;

    // ISSUES
    html += `<div class="tr-section"><div class="tr-section-title">Issues (${issues.length})</div>`;
    if (!issues.length) {
      html += `<div class="tr-no-issues">Tidak ada issue dalam proyek ini.</div>`;
    } else {
      issues.forEach(issue => {
        const attachsHTML = (issue.attachments||[]).map(a =>
          `<a class="tr-file-link" href="${esc(a.file_url)}" target="_blank">📄 ${esc(a.original_name)} (${fmtBytes(a.size)})</a>`
        ).join('');
        
        const mo = issue.meaningful_objectives || {};
        const exp = issue.intelligence_experience || {};
        const imp = issue.intelligence_implementation || {};
        
        function renderTable(title, headers, rows) {
          if (!rows || !rows.length) return '';
          return `<div class="tr-row" style="margin-top:0.5rem; display:block;">
            <div class="tr-label" style="margin-bottom:0.5rem; color:var(--ocean); font-weight:bold;">${title} :</div>
            <table class="tr-table">
              <thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead>
              <tbody>
                ${rows.map(r => `<tr>
                  <td>${esc(r.col1||'')}</td>
                  ${headers.length > 1 ? `<td>${esc(r.col2||'')}</td>` : ''}
                  ${headers.length > 2 ? `<td>${esc(r.col3||'')}</td>` : ''}
                </tr>`).join('')}
              </tbody>
            </table>
          </div>`;
        }

        let intelHTML = '';

        // 1. Meaningful Objectives (Issue)
        if (mo.organizational || mo.user_outcomes || mo.model_properties || (mo.leading_indicators && mo.leading_indicators.length)) {
          intelHTML += `<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">`;
          intelHTML += `<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Meaningful Objectives</div>`;
          if (mo.organizational) {
            intelHTML += `<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">Organizational :</span><span class="tr-value"><b>Tujuan:</b> ${esc(mo.organizational.obj||'—')}<br><b>Cara:</b> ${esc(mo.organizational.how||'—')}<br><b>Ukuran:</b> ${esc(mo.organizational.measure||'—')}</span></div>`;
          }
          if (mo.user_outcomes) {
            intelHTML += `<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">User Outcomes :</span><span class="tr-value"><b>Tujuan:</b> ${esc(mo.user_outcomes.obj||'—')}<br><b>Cara:</b> ${esc(mo.user_outcomes.how||'—')}<br><b>Ukuran:</b> ${esc(mo.user_outcomes.measure||'—')}</span></div>`;
          }
          if (mo.model_properties) {
            intelHTML += `<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">Model Properties :</span><span class="tr-value"><b>Spesifikasi:</b> ${esc(mo.model_properties.obj||'—')}<br><b>Cara:</b> ${esc(mo.model_properties.how||'—')}<br><b>Ukuran:</b> ${esc(mo.model_properties.measure||'—')}</span></div>`;
          }
          intelHTML += renderTable('Leading Indicators', ['FITUR', 'SISTEM KITA', 'KOMPETITOR'], mo.leading_indicators);
          intelHTML += `</div>`;
        }

        // 2. Intelligence Experiences
        if (exp.presentation || (exp.functions && exp.functions.length) || (exp.error_mitigation && exp.error_mitigation.length) || (exp.data_collection && exp.data_collection.length)) {
          intelHTML += `<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">`;
          intelHTML += `<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Intelligence Experiences</div>`;
          
          if (exp.presentation) {
            intelHTML += `<div class="tr-row" style="margin-top:0.25rem; display:block;"><span class="tr-label">Presentation :</span><div class="tr-value" style="margin-top:0.2rem; padding-left:0.5rem; border-left:2px solid #555;"><b>Automate:</b> ${exp.presentation.automate?'Ya':'Tidak'}<br><b>Prompt:</b> ${exp.presentation.prompt?'Ya':'Tidak'}<br><b>Organisation:</b> ${exp.presentation.organisation?'Ya':'Tidak'}<br><b>Annotate:</b> ${exp.presentation.annotate?'Ya':'Tidak'}<br><b>Deskripsi:</b> ${esc(exp.presentation.desc||'—')}</div></div>`;
          }
          intelHTML += renderTable('Functions / Nama Fungsi', ['NAMA FUNGSI', 'DESKRIPSI'], exp.functions);
          intelHTML += renderTable('Error Mitigation', ['NAMA ERROR', 'STRATEGI MITIGASI'], exp.error_mitigation);
          intelHTML += renderTable('Data Collection', ['NAMA DATA', 'RENCANA PENGUMPULAN'], exp.data_collection);
          intelHTML += `</div>`;
        }

        // 3. Intelligence Implementation
        if ((imp.business_process && imp.business_process.length) || (imp.technology && imp.technology.length)) {
          intelHTML += `<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">`;
          intelHTML += `<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Intelligence Implementation</div>`;
          intelHTML += renderTable('Business Process', ['NAMA PROSES', 'DESKRIPSI PROSES'], imp.business_process);
          intelHTML += renderTable('Technology', ['NAMA PROSES', 'TECH STACK'], imp.technology);
          intelHTML += `</div>`;
        }

          html += `
            <div class="tr-issue">
              <div class="tr-issue-title">"${esc(issue.issue_key)}" — ${esc(issue.title)}</div>
              <div class="tr-row" style="margin-bottom:0.25rem;">
                <span class="tr-label" style="min-width:120px;">Status :</span>
                <span class="tr-value">${esc(issue.status?.replace(/_/g,' ')||'–')}</span>
              </div>
              <div class="tr-row" style="margin-bottom:0.25rem;">
                <span class="tr-label" style="min-width:120px;">Priority :</span>
                <span class="tr-value">${esc(issue.priority||'–')}</span>
              </div>
              <div class="tr-row" style="margin-bottom:0.25rem;">
                <span class="tr-label" style="min-width:120px;">Assignee :</span>
                <span class="tr-value">${esc(issue.assignee_name||'Unassigned')}</span>
              </div>
              ${issue.description ? `<div class="tr-issue-desc">Description : ${esc(issue.description)}</div>` : ''}
              ${intelHTML}
              ${attachsHTML ? `<div style="margin-top:0.5rem;"><span style="color:#8aaccc;font-size:10pt;">File Lampiran :</span><br>${attachsHTML}</div>` : ''}
            </div>
          `;
      });
    }
    html += `</div>`;

    html += `
      <div class="tr-watermark">Intelligence Engineering PM · ${project.key}</div>
      <div class="tr-page-num">— 1 —</div>
    `;
    return html;
  }

  document.getElementById('paper-page').innerHTML = buildPaperHTML();
  applyZoom();

  // ── Show content ──────────────────────────────────────────────────────────
  document.getElementById('loading-state').style.display = 'none';
  document.getElementById('main-content').style.display = 'block';

  // ── Build plain-text transcript ───────────────────────────────────────────
  function buildPlainText() {
    const orgObj     = obj.organizational || {};
    const indicators = arr(obj.leading_indicators);
    const outcomes   = obj.user_outcomes || {};
    const modelProps = obj.model_properties || {};
    const supervisors= arr(plan.supervisors);
    const now = new Date().toLocaleDateString('id-ID',{day:'numeric',month:'long',year:'numeric'});

    let t = '';
    t += `TRANSKRIP PROJECT "${project.name}"\n`;
    t += `Digenerate: ${now}\n`;
    t += `${'='.repeat(60)}\n\n`;

    t += `PLANNING\n${'-'.repeat(40)}\n`;
    t += `Start Date         : ${plan.startDate||'—'}\n`;
    t += `End Date           : ${plan.endDate||'—'}\n`;
    t += `Supervisor         :\n${supervisors.map(s=>`  - ${s}`).join('\n')||'  —'}\n`;
    t += `Deployment         : ${plan.deployment||'—'}\n`;
    t += `Maintenance        : ${plan.maintenance||'—'}\n`;
    t += `Operations         : ${plan.operations||'—'}\n\n`;

    t += `OBJECTIVES\n${'-'.repeat(40)}\n`;
    t += `Organizational     :\n  Tujuan: ${orgObj.obj||'—'}\n  Cara: ${orgObj.how||'—'}\n  Ukuran: ${orgObj.measure||'—'}\n`;
    t += `Leading Indicators :\n${indicators.map(v=>`  - ${v.col1} (Kita: ${v.col2}, Komp: ${v.col3})`).join('\n')||'  —'}\n`;
    t += `User Outcomes      :\n  Tujuan: ${outcomes.obj||'—'}\n  Cara: ${outcomes.how||'—'}\n  Ukuran: ${outcomes.measure||'—'}\n`;
    t += `Model Properties   :\n  Spesifikasi: ${modelProps.obj||'—'}\n  Cara: ${modelProps.how||'—'}\n  Ukuran: ${modelProps.measure||'—'}\n\n`;

    t += `ISSUES (${issues.length})\n${'-'.repeat(40)}\n`;
    if (!issues.length) {
      t += 'Tidak ada issue.\n';
    } else {
      issues.forEach((issue, idx) => {
        t += `\n[${idx+1}] "${issue.issue_key}" — ${issue.title}\n`;
        t += `    Status   : ${(issue.status||'').replace(/_/g,' ')}\n`;
        t += `    Priority : ${issue.priority||'–'}\n`;
        t += `    Type     : ${issue.type||'–'}\n`;
        t += `    Assignee : ${issue.assignee_name||'Unassigned'}\n`;
        if (issue.description) t += `    Desc     : ${issue.description}\n`;
        if (issue.attachments?.length) {
          t += `    Files :\n`;
          issue.attachments.forEach(a => {
            t += `      - ${a.original_name} (${fmtBytes(a.size)}) → /uploads/${a.filename}\n`;
          });
        }
      });
    }
    t += `\n${'='.repeat(60)}\n`;
    t += `Intelligence Engineering PM · ${project.key}\n`;
    return t;
  }

  // ── Download ──────────────────────────────────────────────────────────────
  window.doDownload = async function() {
    const type = document.querySelector('input[name="dl-type"]:checked')?.value;
    const btn  = document.getElementById('btn-dl');
    btn.disabled = true;
    btn.textContent = 'Memproses...';

    // Inject temporary print styles
    const printStyle = document.createElement('style');
    printStyle.innerHTML = `
      #paper-page { width: 100% !important; min-height: auto !important; padding: 0 !important; box-shadow: none !important; background: #ffffff !important; color: #000000 !important; margin: 0 !important; transform: none !important; }
      .tr-row { display: block !important; margin-bottom: 12px !important; }
      .tr-label { display: block !important; font-weight: bold !important; color: #444 !important; margin-bottom: 4px !important; font-style: normal !important; }
      .tr-value { display: block !important; color: #000 !important; line-height: 1.6 !important; }
      .tr-value br { display: block !important; content: "" !important; margin-bottom: 4px !important; }
      .tr-value b, .tr-value strong { color: #222 !important; }
      .tr-main-title { color: #000 !important; letter-spacing: 0 !important; border-bottom: 2px solid #000 !important; padding-bottom: 10px !important; margin-bottom: 20px !important; }
      .tr-section-title { color: #111 !important; border-bottom: 1px solid #ccc !important; letter-spacing: 0 !important; padding-bottom: 5px !important; margin-bottom: 10px !important; margin-top: 25px !important; }
      .tr-issue { border: 1px solid #ccc !important; padding: 15px !important; margin-bottom: 15px !important; page-break-inside: avoid !important; }
      .tr-issue-title { color: #0056b3 !important; font-size: 13pt !important; margin-bottom: 8px !important; }
      .tr-issue-desc { color: #222 !important; }
      .tr-file-link { color: #0056b3 !important; text-decoration: none !important; }
      .tr-no-issues { color: #555 !important; }
      .tr-watermark { display: none !important; }
      .tr-table { color: #000 !important; }
      .tr-table th { border: 1px solid #ccc !important; background: #2c3e50 !important; color: #fff !important; }
      .tr-table td { border: 1px solid #ccc !important; color: #000 !important; }
    `;
    document.head.appendChild(printStyle);

    try {
      const safeName = project.name.replace(/[^a-zA-Z0-9_-]/g, '_');
      const element = document.getElementById('paper-page');
      
      const opt = {
        margin:       15,
        filename:     `transcript_${safeName}.pdf`,
        image:        { type: 'jpeg', quality: 1.0 },
        html2canvas:  { scale: 2, useCORS: true, letterRendering: false },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };

      if (type === 'pdf') {
        if (typeof html2pdf === 'undefined') throw new Error('Library PDF belum dimuat. Coba refresh halaman.');
        await html2pdf().set(opt).from(element).save();
        showToast('PDF berhasil didownload!');
      } else {
        if (typeof JSZip === 'undefined' || typeof html2pdf === 'undefined') {
          throw new Error('JSZip atau PDF library belum dimuat.');
        }
        const zip = new JSZip();
        
        // Generate PDF as Blob
        const pdfBlob = await html2pdf().set(opt).from(element).outputPdf('blob');
        zip.file(`transcript_${safeName}.pdf`, pdfBlob);

        const allAtts = [];
        issues.forEach(issue => {
          (issue.attachments||[]).forEach(a => allAtts.push({ ...a, issueKey: issue.issue_key }));
        });

        if (allAtts.length) {
          const folder = zip.folder('uploads');
          const token = localStorage.getItem('ie_token');
          await Promise.all(allAtts.map(async (a) => {
            try {
              const res = await fetch(a.file_url, { headers: token ? { Authorization: "Bearer " + token } : {} });
              if (!res.ok) throw new Error("HTTP " + res.status);
              const blob = await res.blob();
              const arrBuf = await blob.arrayBuffer();
              folder.file(a.issueKey + "_" + a.original_name, arrBuf);
            } catch(e) { console.warn('Could not fetch', a.original_name, e.message); }
          }));
        }

        const content = await zip.generateAsync({ type: 'blob', compression: 'DEFLATE' });
        triggerDownload(content, `transcript_${safeName}.zip`);
        showToast(`ZIP berhasil didownload! (${allAtts.length} file)`);
      }
    } catch(e) {
      showToast('Gagal download: ' + e.message, 'error');
    } finally {
      document.head.removeChild(printStyle);
      btn.disabled = false;
      btn.innerHTML = '&#11015;&#65039; Download Sekarang';
    }
  };

  function triggerDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 1000);
  }

})();
