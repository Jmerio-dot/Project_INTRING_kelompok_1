const fs = require('fs');
let html = fs.readFileSync('transcript.html', 'utf8');

const s = html.indexOf('              ${indicators.map(v => `<tr>');
const s_end = html.indexOf('issues.forEach(issue => {', s);

if (s !== -1 && s_end !== -1) {
    // Check if it's the right block
    const block = html.substring(s, s_end + 25);
    console.log("Found block:", block);
    
    if(block.includes('<td>${esc(v.col1)}</td>')) {
        const replacement = `              \${indicators.map(v => \`<tr>
                <td>\${esc(v.col1)}</td>
                <td>\${esc(v.col2||'')}</td>
                <td>\${esc(v.col3||'')}</td>
              </tr>\`).join('')}
            </tbody>
          </table>
        </div>\`;
      }
      html += \`
        <div class="tr-row" style="margin-top:0.5rem;"><span class="tr-label">User Outcomes :</span><span class="tr-value"><b>Tujuan:</b> \${esc(outcomes.obj||'—')}<br><b>Cara:</b> \${esc(outcomes.how||'—')}<br><b>Ukuran:</b> \${esc(outcomes.measure||'—')}</span></div>
        <div class="tr-row" style="margin-top:0.5rem;"><span class="tr-label">Model Properties :</span><span class="tr-value"><b>Spesifikasi:</b> \${esc(modelProps.obj||'—')}<br><b>Cara:</b> \${esc(modelProps.how||'—')}<br><b>Ukuran:</b> \${esc(modelProps.measure||'—')}</span></div>
      </div>
    \`;

    // ISSUES
    html += \`<div class="tr-section"><div class="tr-section-title">Issues (\${issues.length})</div>\`;
    if (!issues.length) {
      html += \`<div class="tr-no-issues">Tidak ada issue dalam proyek ini.</div>\`;
    } else {
      issues.forEach(issue => {`;

        html = html.substring(0, s) + replacement + html.substring(s_end + 25); 
        fs.writeFileSync('transcript.html', html, 'utf8');
        console.log('Fixed transcript.html');
    } else {
        console.log('Block did not match expectations');
    }
} else {
    console.log('Could not find slice boundaries!');
}
