const fs = require('fs');
let html = fs.readFileSync('transcript.html', 'utf8');

// The corrupted block was produced because I mistakenly matched `<t      issues.forEach`
// Let's use simple string slicing to completely replace lines from `<t      issues.forEach` down to the first valid `<div class="tr-issue">`
const s = html.indexOf('<t      issues.forEach');
// Find the end of the corrupted block which includes `+= \`<div style="margin-top:0.5rem;border-top:1px dashed #c8e6fa;padding-top:0.5rem;">\`;`
// and then the second valid `<div class="tr-issue">`
const e = html.indexOf('          html += `\n            <div class="tr-issue">\n              <div class="tr-issue-title">', s);

if (s !== -1 && e !== -1) {
    const replacement = `      issues.forEach(issue => {
        const attachsHTML = (issue.attachments||[]).map(a =>
          \`<a class="tr-file-link" href="\${esc(a.file_url)}" target="_blank">📄 \${esc(a.original_name)} (\${fmtBytes(a.size)})</a>\`
        ).join('');
        
        const mo = issue.meaningful_objectives || {};
        const exp = issue.intelligence_experience || {};
        const imp = issue.intelligence_implementation || {};
        
        function renderTable(title, headers, rows) {
          if (!rows || !rows.length) return '';
          return \`<div class="tr-row" style="margin-top:0.5rem; display:block;">
            <div class="tr-label" style="margin-bottom:0.5rem; color:var(--ocean); font-weight:bold;">\${title} :</div>
            <table class="tr-table">
              <thead><tr>\${headers.map(h => \`<th>\${esc(h)}</th>\`).join('')}</tr></thead>
              <tbody>
                \${rows.map(r => \`<tr>
                  <td>\${esc(r.col1||'')}</td>
                  \${headers.length > 1 ? \`<td>\${esc(r.col2||'')}</td>\` : ''}
                  \${headers.length > 2 ? \`<td>\${esc(r.col3||'')}</td>\` : ''}
                </tr>\`).join('')}
              </tbody>
            </table>
          </div>\`;
        }

        let intelHTML = '';

        // 1. Meaningful Objectives (Issue)
        if (mo.organizational || mo.user_outcomes || mo.model_properties || (mo.leading_indicators && mo.leading_indicators.length)) {
          intelHTML += \`<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">\`;
          intelHTML += \`<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Meaningful Objectives</div>\`;
          if (mo.organizational) {
            intelHTML += \`<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">Organizational :</span><span class="tr-value"><b>Tujuan:</b> \${esc(mo.organizational.obj||'—')}<br><b>Cara:</b> \${esc(mo.organizational.how||'—')}<br><b>Ukuran:</b> \${esc(mo.organizational.measure||'—')}</span></div>\`;
          }
          if (mo.user_outcomes) {
            intelHTML += \`<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">User Outcomes :</span><span class="tr-value"><b>Tujuan:</b> \${esc(mo.user_outcomes.obj||'—')}<br><b>Cara:</b> \${esc(mo.user_outcomes.how||'—')}<br><b>Ukuran:</b> \${esc(mo.user_outcomes.measure||'—')}</span></div>\`;
          }
          if (mo.model_properties) {
            intelHTML += \`<div class="tr-row" style="margin-top:0.25rem;"><span class="tr-label" style="min-width:140px;">Model Properties :</span><span class="tr-value"><b>Spesifikasi:</b> \${esc(mo.model_properties.obj||'—')}<br><b>Cara:</b> \${esc(mo.model_properties.how||'—')}<br><b>Ukuran:</b> \${esc(mo.model_properties.measure||'—')}</span></div>\`;
          }
          intelHTML += renderTable('Leading Indicators', ['FITUR', 'SISTEM KITA', 'KOMPETITOR'], mo.leading_indicators);
          intelHTML += \`</div>\`;
        }

        // 2. Intelligence Experiences
        if (exp.presentation || (exp.functions && exp.functions.length) || (exp.error_mitigation && exp.error_mitigation.length) || (exp.data_collection && exp.data_collection.length)) {
          intelHTML += \`<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">\`;
          intelHTML += \`<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Intelligence Experiences</div>\`;
          
          if (exp.presentation) {
            intelHTML += \`<div class="tr-row" style="margin-top:0.25rem; display:block;"><span class="tr-label">Presentation :</span><div class="tr-value" style="margin-top:0.2rem; padding-left:0.5rem; border-left:2px solid #555;"><b>Automate:</b> \${exp.presentation.automate?'Ya':'Tidak'}<br><b>Prompt:</b> \${exp.presentation.prompt?'Ya':'Tidak'}<br><b>Organisation:</b> \${exp.presentation.organisation?'Ya':'Tidak'}<br><b>Annotate:</b> \${exp.presentation.annotate?'Ya':'Tidak'}<br><b>Deskripsi:</b> \${esc(exp.presentation.desc||'—')}</div></div>\`;
          }
          intelHTML += renderTable('Functions / Nama Fungsi', ['NAMA FUNGSI', 'DESKRIPSI'], exp.functions);
          intelHTML += renderTable('Error Mitigation', ['NAMA ERROR', 'STRATEGI MITIGASI'], exp.error_mitigation);
          intelHTML += renderTable('Data Collection', ['NAMA DATA', 'RENCANA PENGUMPULAN'], exp.data_collection);
          intelHTML += \`</div>\`;
        }

        // 3. Intelligence Implementation
        if ((imp.business_process && imp.business_process.length) || (imp.technology && imp.technology.length)) {
          intelHTML += \`<div style="margin-top:0.75rem;border-top:1px dashed #4a5a6a;padding-top:0.5rem;">\`;
          intelHTML += \`<div style="font-size:11pt;font-weight:700;color:#7aacc8;margin-bottom:0.5rem;text-transform:uppercase;">Intelligence Implementation</div>\`;
          intelHTML += renderTable('Business Process', ['NAMA PROSES', 'DESKRIPSI PROSES'], imp.business_process);
          intelHTML += renderTable('Technology', ['NAMA PROSES', 'TECH STACK'], imp.technology);
          intelHTML += \`</div>\`;
        }

`;
    
    html = html.substring(0, s) + replacement + html.substring(e);
    fs.writeFileSync('transcript.html', html, 'utf8');
    console.log('Fixed transcript.html using string slicing');
} else {
    console.log('Could not find slice boundaries!', s, e);
}
