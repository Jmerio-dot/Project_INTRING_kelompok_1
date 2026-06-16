// ── sidebar.js — enhanced sidebar renderer ────────────────────────────────

function isSidebarCollapsed() {
  return localStorage.getItem('ie_sidebar_collapsed') === 'true';
}

function setSidebarCollapsed(val) {
  localStorage.setItem('ie_sidebar_collapsed', String(val));
}

async function renderSidebar(activePage, activePid) {
  const user = getUser();
  const sid = document.getElementById('sidebar');
  if (!sid) return;

  const collapsed = isSidebarCollapsed();
  if (collapsed) {
    sid.classList.add('collapsed');
    document.querySelector('.app-main')?.classList.add('sidebar-collapsed');
  }

  sid.innerHTML = `
    <!-- Brand -->
    <div class="sb-brand">
      <a href="/dashboard.html" class="sb-logo" title="IntRing PM">
        <div class="sb-logo-icon" style="background:transparent; padding:0; width:36px; height:36px;">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" style="width:100%;height:100%;"><path d="M20,80 L80,20 M20,20 L80,80 M10,50 L90,50 M50,10 L50,90" stroke="#0077b6" stroke-width="5"/></svg>
        </div>
        <span class="sb-logo-text">IntRing PM</span>
      </a>
      <button class="sb-toggle" id="sidebar-toggle" title="Toggle sidebar" onclick="toggleSidebar()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- Search Bar -->
    <div class="sb-search-wrap">
      <div class="sb-search">
        <span class="sb-search-icon"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M16.65 16.65A7.5 7.5 0 111.5 10.5a7.5 7.5 0 0115.15 6.15z"/></svg></span>
        <input class="sb-search-input" placeholder="Cari..." oninput="sidebarSearch(this.value)" />
      </div>
    </div>

    <!-- Main Nav -->
    <div class="sb-section">
      <div class="sb-section-label">Menu Utama</div>
      <a href="/dashboard.html" class="sb-link ${activePage === 'dashboard' ? 'active' : ''}" title="Dashboard">
        <span class="sb-link-icon"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg></span>
        <span class="sb-link-text">Dashboard</span>
      </a>
      <a href="/projects.html" class="sb-link ${activePage === 'projects' ? 'active' : ''}" title="Semua Proyek">
        <span class="sb-link-icon"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/></svg></span>
        <span class="sb-link-text">Semua Proyek</span>
      </a>
      <a href="/laporan.html" class="sb-link ${activePage === 'laporan' ? 'active' : ''}" title="Laporan">
        <span class="sb-link-icon"><svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg></span>
        <span class="sb-link-text">Laporan</span>
      </a>
    </div>

    <!-- Projects Section -->
    <div class="sb-section sb-projects-section" style="flex:1;overflow:hidden;display:flex;flex-direction:column;">
      <div class="sb-section-label" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Proyek Saya</span>
        <button class="sb-add-btn" onclick="document.getElementById('new-project-modal')&&(document.getElementById('new-project-modal').style.display='flex')" title="Proyek Baru">+</button>
      </div>
      <div id="sidebar-projects" style="overflow-y:auto;flex:1;padding-bottom:0.5rem;">
        <div class="sb-loading">Memuat...</div>
      </div>
    </div>

    <!-- User Footer -->
    <div class="sb-footer">
      <a href="/profile.html" class="sb-user" title="Profil Saya" style="text-decoration:none;">
        <div class="sb-avatar">${user?.profile_photo_url ? `<img src="${user.profile_photo_url}" style="width:100%;height:100%;object-fit:cover;" />` : (user?.avatar || '<svg width="100%" height="100%" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/></svg>')}</div>
        <div class="sb-user-info">
          <div class="sb-user-name">${user?.name?.split(' ')[0] || 'User'}</div>
          <div class="sb-user-role">Lihat Profil</div>
        </div>
      </a>
    </div>
  `;

  await loadSidebarProjects(activePid);
}

function toggleSidebar() {
  const sid = document.getElementById('sidebar');
  const main = document.querySelector('.app-main');
  const collapsed = !isSidebarCollapsed();
  setSidebarCollapsed(collapsed);
  if (collapsed) {
    sid.classList.add('collapsed');
    main?.classList.add('sidebar-collapsed');
  } else {
    sid.classList.remove('collapsed');
    main?.classList.remove('sidebar-collapsed');
  }
}

function sidebarSearch(q) {
  const items = document.querySelectorAll('#sidebar-projects .sb-proj-item');
  const val = q.toLowerCase().trim();
  items.forEach(el => {
    const text = el.textContent.toLowerCase();
    el.style.display = (!val || text.includes(val)) ? '' : 'none';
  });
}

async function loadSidebarProjects(activePid) {
  const el = document.getElementById('sidebar-projects');
  if (!el) return;
  try {
    const projects = await apiFetch('/projects');
    if (!projects.length) {
      el.innerHTML = '<div class="sb-empty">Belum ada proyek</div>';
      return;
    }
    el.innerHTML = projects.map(p => `
      <div class="sb-proj-item ${activePid == p.id ? 'active' : ''}" data-pid="${p.id}">
        <div class="sb-proj-header" onclick="toggleProjectMenu(${p.id})">
          <span class="sb-proj-key">${p.key.substring(0, 3)}</span>
          <span class="sb-proj-name">${p.name}</span>
          <span class="sb-proj-chevron" id="chevron-${p.id}">›</span>
        </div>
        <div class="sb-proj-menu" id="proj-menu-${p.id}" style="display:${activePid == p.id ? 'flex' : 'none'};">
          <a href="/board.html?pid=${p.id}" class="sb-proj-link">🗂️ Board</a>
          <a href="/backlog.html?pid=${p.id}" class="sb-proj-link">📋 Backlog</a>
          <a href="/transcript.html?pid=${p.id}" class="sb-proj-link">📄 Transcript</a>
        </div>
      </div>
    `).join('');

    // Rotate active chevron
    if (activePid) {
      const ch = document.getElementById(`chevron-${activePid}`);
      if (ch) ch.style.transform = 'rotate(90deg)';
    }
  } catch (e) {
    console.error('Sidebar projects load error:', e.message);
    el.innerHTML = '<div class="sb-empty sb-empty-error">Gagal memuat</div>';
  }
}

function toggleProjectMenu(pid) {
  const menu = document.getElementById(`proj-menu-${pid}`);
  const chevron = document.getElementById(`chevron-${pid}`);
  if (!menu) return;
  const isOpen = menu.style.display === 'flex';
  // Close all
  document.querySelectorAll('.sb-proj-menu').forEach(m => m.style.display = 'none');
  document.querySelectorAll('.sb-proj-chevron').forEach(c => c.style.transform = '');
  if (!isOpen) {
    menu.style.display = 'flex';
    if (chevron) chevron.style.transform = 'rotate(90deg)';
  }
}
