<template>
    <div class="eme-app-page">

        <!-- Header -->
        <div class="eme-app-header">
            <div class="d-flex align-items-center gap-3">
                <span style="font-size:1.6rem;">📋</span>
                <h1 class="eme-app-title">Мої Проекти</h1>
                <span class="badge bg-blue-lt ms-1">{{ projects.length }}</span>
            </div>
            <div class="d-flex gap-2 flex-wrap align-items-center">
                <!-- Domain filters -->
                <div class="btn-group btn-group-sm">
                    <button v-for="d in domains" :key="d.key"
                        class="btn btn-sm"
                        :class="filterDomain === d.key ? 'btn-primary' : 'btn-ghost-secondary'"
                        @click="filterDomain = filterDomain === d.key ? null : d.key">
                        {{ d.label }}
                    </button>
                </div>
                <!-- Deadline sidebar toggle -->
                <button class="btn btn-sm"
                    :class="showSidebar ? 'btn-warning' : 'btn-ghost-warning'"
                    @click="showSidebar = !showSidebar"
                    title="Найближчі дедлайни">
                    🗓️ {{ upcomingDeadlines.length > 0 ? upcomingDeadlines.length : '' }}
                </button>
                <button class="btn btn-sm btn-primary" @click="openNewProject">+ Проект</button>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-cyan"></div>
        </div>

        <!-- Main layout: board + sidebar -->
        <div v-else class="kanban-wrapper">

            <!-- Kanban Board -->
            <div class="kanban-board">
                <div v-for="col in columns" :key="col.key" class="kanban-col"
                    :class="{ 'kanban-col--this-week': col.key === 'this_week' }">
                    <div class="kanban-col-header">
                        <span>{{ col.icon }} {{ col.label }}</span>
                        <span class="badge bg-secondary ms-2">{{ getColProjects(col.key).length }}</span>
                    </div>
                    <div class="kanban-col-body"
                        @dragover.prevent
                        @drop="onDrop($event, col.key)">


                        <div v-for="p in getColProjects(col.key)" :key="p?.id"
                            class="kanban-card"
                            :class="'border-' + priorityColor(p.priority)"
                            draggable="true"
                            @dragstart="onDragStart($event, p)">

                            <!-- Card Header: drag handle + title (clickable) + buttons -->
                            <div class="d-flex align-items-start justify-content-between mb-1">
                                <div class="d-flex align-items-start gap-1 flex-1 min-w-0"
                                     style="cursor:pointer"
                                     @click.stop="openProject(p)">
                                    <span class="drag-handle" @click.stop title="Перетягнути">⠿</span>
                                    <div class="kanban-card-title">
                                        <span>{{ p.emoji }}</span> {{ p.title }}
                                    </div>
                                </div>
                                <div class="d-flex gap-1 ms-1 flex-shrink-0">
                                    <button class="btn btn-icon btn-xs btn-ghost-secondary" @click.stop="openEdit(p)">✏️</button>
                                    <button class="btn btn-icon btn-xs btn-ghost-danger" @click.stop="deleteProject(p)">🗑</button>
                                </div>
                            </div>

                            <!-- Badges row -->
                            <div class="d-flex flex-wrap gap-1 mb-2">
                                <span class="badge badge-sm" :style="'background:' + domainColor(p.domain) + '22;color:' + domainColor(p.domain)">
                                    {{ domainLabel(p.domain) }}
                                </span>
                                <!-- Priority dropdown -->
                                <span class="badge badge-sm kanban-priority-badge"
                                    :class="'bg-' + priorityColor(p.priority) + '-lt'"
                                    @click.stop="cyclePriority(p)"
                                    title="Клікни щоб змінити пріоритет">
                                    {{ priorityLabel(p.priority) }} {{ priorityText(p.priority) }}
                                </span>
                                <span v-if="p.deadline" class="badge badge-sm"
                                    :class="deadlineBadgeClass(p.deadline)">
                                    📅 {{ formatDate(p.deadline) }}
                                    <span v-if="daysUntil(p.deadline) !== null && daysUntil(p.deadline) <= 7">
                                        ({{ daysUntil(p.deadline) === 0 ? 'сьогодні' : daysUntil(p.deadline) < 0 ? 'прострочено' : 'через ' + daysUntil(p.deadline) + 'д' }})
                                    </span>
                                </span>
                            </div>

                            <!-- Next action -->
                            <div v-if="p.next_action" class="kanban-next-action">
                                ⚡ {{ p.next_action }}
                            </div>

                            <!-- Action progress bar -->
                            <div v-if="p.actions && p.actions.length" class="mt-2">
                                <div class="kanban-progress-bar mb-1">
                                    <div class="kanban-progress-fill"
                                        :style="'width:' + actionProgress(p) + '%'"
                                        :class="actionProgress(p) === 100 ? 'kanban-progress-done' : ''">
                                    </div>
                                </div>
                                <div v-for="a in (p.actions || []).filter(x => x).slice(0, 3)" :key="a?.id"
                                    class="kanban-action-item"
                                    @click.stop="toggleAction(p, a)">
                                    <span>{{ a.is_done ? '✅' : '⬜' }}</span>
                                    <span :class="{ 'text-muted text-decoration-line-through': a.is_done }">{{ a.text }}</span>
                                </div>
                                <div v-if="p.actions.length > 3" class="text-muted mt-1" style="font-size:11px;">
                                    +{{ p.actions.length - 3 }} ще... ({{ doneCount(p) }}/{{ p.actions.length }} ✅)
                                </div>
                            </div>

                            <!-- Add action -->
                            <div v-if="addingActionFor === p?.id" class="mt-2 d-flex gap-1">
                                <input class="form-control form-control-sm"
                                    v-model="newActionText"
                                    placeholder="Нова дія..."
                                    ref="actionInput"
                                    @keyup.enter="saveAction(p)"
                                    @keyup.escape="addingActionFor = null">
                                <button class="btn btn-sm btn-primary" @click.stop="saveAction(p)">+</button>
                            </div>
                            <button v-else class="btn btn-xs btn-ghost-secondary mt-2 w-100 text-start"
                                @click.stop="startAddAction(p?.id)">
                                + дія
                            </button>
                        </div>

                        <div v-if="getColProjects(col.key).length === 0" class="kanban-empty">
                            Перетягни сюди
                        </div>
                    </div>
                </div>
            </div>

            <!-- Deadline Sidebar -->
            <div v-if="showSidebar" class="kanban-deadline-sidebar">
                <div class="deadline-sidebar-header">🗓️ Найближчі дедлайни</div>

                <div v-if="upcomingDeadlines.length === 0" class="deadline-empty">
                    Немає запланованих дедлайнів
                </div>

                <div v-for="p in upcomingDeadlines" :key="p?.id"
                    class="deadline-item"
                    :class="deadlineItemClass(p.deadline)"
                    @click="openEdit(p)">
                    <div class="deadline-item-title">
                        <span>{{ p.emoji }}</span> {{ p.title }}
                    </div>
                    <div class="deadline-item-date">
                        {{ formatDate(p.deadline) }}
                        <span class="deadline-days">{{ deadlineDaysLabel(p.deadline) }}</span>
                    </div>
                    <div v-if="p.next_action" class="deadline-item-action">
                        ⚡ {{ p.next_action }}
                    </div>
                </div>

                <!-- Overdue section -->
                <div v-if="overdueProjects.length" class="mt-3">
                    <div class="deadline-sidebar-header text-danger">⚠️ Прострочено</div>
                    <div v-for="p in overdueProjects" :key="'od-' + p?.id"
                        class="deadline-item deadline-item--overdue"
                        @click="openEdit(p)">
                        <div class="deadline-item-title">{{ p.emoji }} {{ p.title }}</div>
                        <div class="deadline-item-date text-danger">{{ formatDate(p.deadline) }}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal -->
        <div v-if="modal.show" class="eme-modal-overlay" @click.self="closeModal">
            <div class="eme-modal">
                <div class="eme-modal-header">
                    <strong>{{ modal.mode === 'new' ? '➕ Новий проект' : '✏️ Редагувати' }}</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="closeModal">✕</button>
                </div>
                <div class="eme-modal-body">
                    <div class="row g-2 mb-2">
                        <div class="col-2">
                            <label class="form-label">Emoji</label>
                            <input class="form-control" v-model="modal.form.emoji" maxlength="4">
                        </div>
                        <div class="col-10">
                            <label class="form-label">Назва *</label>
                            <input class="form-control" v-model="modal.form.title" placeholder="Назва проекту">
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Опис</label>
                        <textarea class="form-control" v-model="modal.form.description" rows="2"></textarea>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6">
                            <label class="form-label">Домен</label>
                            <select class="form-select" v-model="modal.form.domain">
                                <option v-for="d in domains" :key="d.key" :value="d.key">{{ d.label }}</option>
                            </select>
                        </div>
                        <div class="col-6">
                            <label class="form-label">Пріоритет</label>
                            <select class="form-select" v-model="modal.form.priority">
                                <option value="critical">🔴 Критичний</option>
                                <option value="high">🟡 Високий</option>
                                <option value="medium">🟢 Середній</option>
                                <option value="low">⚪ Низький</option>
                            </select>
                        </div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6">
                            <label class="form-label">Дедлайн</label>
                            <input type="date" class="form-control" v-model="modal.form.deadline">
                        </div>
                        <div class="col-6">
                            <label class="form-label">Колонка</label>
                            <select class="form-select" v-model="modal.form.status">
                                <option v-for="c in columns" :key="c.key" :value="c.key">{{ c.label }}</option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">⚡ Наступна дія</label>
                        <input class="form-control" v-model="modal.form.next_action" placeholder="Що зробити зараз?">
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <input type="checkbox" class="form-check-input" v-model="modal.form.is_public" id="pub_modal">
                        <label class="form-check-label" for="pub_modal">Публічний (видно в профілі)</label>
                    </div>

                    <!-- AI Helper (only on create) -->
                    <div v-if="modal.mode === 'new'" class="mt-3 p-3 rounded" style="background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.15);">
                        <div class="d-flex align-items-center gap-2 mb-2">
                            <input type="checkbox" class="form-check-input" v-model="modal.form.aiEnabled" id="ai_modal">
                            <label class="form-check-label fw-bold" for="ai_modal" style="color:#00e5ff;">🤖 AI Помічник — згенерувати ролі та дії</label>
                            <span v-if="modal.aiStatus" class="ms-auto badge" :style="modal.aiStatus === 'ok' ? 'background:#20c99733;color:#20c997' : 'background:#dc354533;color:#dc3545'">{{ modal.aiStatus }}</span>
                        </div>
                        <div v-if="modal.form.aiEnabled" class="d-flex align-items-center gap-2">
                            <label class="form-label mb-0 text-muted" style="font-size:12px;white-space:nowrap;">👥 К-сть людей:</label>
                            <input type="number" class="form-control form-control-sm" v-model.number="modal.form.aiTeamSize" min="1" max="100" style="max-width:80px;">
                            <span class="text-muted" style="font-size:11px;">AI погенерує ролі, дії, дедлайни</span>
                        </div>
                    </div>
                </div>
                <div class="eme-modal-footer">
                    <button class="btn btn-ghost-secondary" @click="closeModal">Скасувати</button>
                    <button class="btn btn-primary" @click="saveProject" :disabled="modal.saving">
                        <span v-if="modal.saving" class="spinner-border spinner-border-sm me-1"></span>
                        {{ modal.saving ? (modal.form.aiEnabled && modal.mode === 'new' ? '🤖 AI генерує...' : 'Збереження...') : (modal.mode === 'new' ? 'Створити' : 'Зберегти') }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
const PRIORITY_CYCLE = ['critical', 'high', 'medium', 'low'];

export default {
    props: ['user', 'auth'],
    emits: ['close'],
    data() {
        return {
            projects: [],
            loading: true,
            filterDomain: null,
            selectedProject: null,
            showSidebar: true,
            dragging: null,
            addingActionFor: null,
            newActionText: '',
            columns: [
                { key: 'this_week', icon: '🔥', label: 'Цього тижня' },
                { key: 'in_progress', icon: '🔧', label: 'В роботі' },
                { key: 'backlog', icon: '📦', label: 'Backlog' },
                { key: 'frozen', icon: '❄️', label: 'Заморожено' },
                { key: 'done', icon: '✅', label: 'Готово' },
            ],
            domains: [
                { key: 'life', label: '❤️ Особисте', color: '#ff4757' },
                { key: 'life', label: '❤️ Особисте', color: '#ff4757' },
                { key: 'business', label: '💼 Бізнес', color: '#ffa502' },
                { key: 'eme', label: '⚡ EME', color: '#00e5ff' },
                { key: 'tech', label: '🔧 Технічне', color: '#2ed573' },
                { key: 'community', label: '🤝 Спільнота', color: '#a29bfe' },
            ],
            modal: { show: false, mode: 'new', editId: null, saving: false, form: {} }
        };
    },
    computed: {
        activeProjects() {
            const safe = Array.isArray(this.projects) ? this.projects : [];
            return safe.filter(p => p && p.status !== 'done' && p.status !== 'frozen');
        },
        upcomingDeadlines() {
            const now = new Date();
            const in30 = new Date(now); in30.setDate(now.getDate() + 30);
            const safeActive = Array.isArray(this.activeProjects) ? this.activeProjects : [];
            return safeActive
                .filter(p => p && p.deadline && new Date(p.deadline) >= now && new Date(p.deadline) <= in30)
                .sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
        },
        overdueProjects() {
            const now = new Date(); now.setHours(0,0,0,0);
            return (this.activeProjects || [])
                .filter(p => p && p.deadline && new Date(p.deadline) < now)
                .sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
        }
    },
    async mounted() {
        await this.loadProjects();
    },
    methods: {
        emptyForm() {
            return {
                title: '', description: '', emoji: '📋', domain: 'eme',
                status: 'backlog', priority: 'medium', deadline: '',
                next_action: '', is_public: true,
                aiEnabled: false, aiTeamSize: 3,
            };
        },
        hdrs() { return { 'Content-Type': 'application/json', ...this.auth() }; },

        async loadProjects() {
            this.loading = true;
            try {
                const res = await fetch('/api/projects/', { headers: this.auth() });
                const data = await res.json();
                this.projects = data.results || data;
            } finally { this.loading = false; }
        },

        openProject(p) {
            window.location.href = '/p/' + p.id + '/';
        },

        // Sort: critical > high > medium > low, then by deadline
        getColProjects(status) {
            const safeProjects = Array.isArray(this.projects) ? this.projects : [];
            return safeProjects
                .filter(p => p && p.status === status && (!this.filterDomain || p.domain === this.filterDomain))
                .sort((a, b) => {
                    const po = PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority];
                    if (po !== 0) return po;
                    if (a.deadline && b.deadline) return new Date(a.deadline) - new Date(b.deadline);
                    if (a.deadline) return -1;
                    return 1;
                });
        },

        // Actions helpers
        doneCount(p) { return ((p && p.actions) || []).filter(a => a && a.is_done).length; },
        actionProgress(p) {
            if (!p || !p.actions || !p.actions.length) return 0;
            return Math.round((this.doneCount(p) / p.actions.length) * 100);
        },

        // Deadline helpers
        daysUntil(deadline) {
            if (!deadline) return null;
            const now = new Date(); now.setHours(0,0,0,0);
            const d = new Date(deadline); d.setHours(0,0,0,0);
            return Math.round((d - now) / 86400000);
        },
        deadlineBadgeClass(deadline) {
            const days = this.daysUntil(deadline);
            if (days === null) return '';
            if (days < 0) return 'bg-red text-white';
            if (days <= 3) return 'bg-red-lt text-red';
            if (days <= 7) return 'bg-yellow-lt text-yellow';
            return 'bg-blue-lt';
        },
        deadlineItemClass(deadline) {
            const days = this.daysUntil(deadline);
            if (days === null) return '';
            if (days <= 3) return 'deadline-item--urgent';
            if (days <= 14) return 'deadline-item--soon';
            return 'deadline-item--ok';
        },
        deadlineDaysLabel(deadline) {
            const days = this.daysUntil(deadline);
            if (days === null) return '';
            if (days === 0) return '← сьогодні!';
            if (days < 0) return `← ${Math.abs(days)}д тому`;
            if (days === 1) return '← завтра';
            return `← через ${days}д`;
        },

        // Priority cycling
        async cyclePriority(project) {
            const idx = PRIORITY_CYCLE.indexOf(project.priority);
            const newPriority = PRIORITY_CYCLE[(idx + 1) % PRIORITY_CYCLE.length];
            project.priority = newPriority;
            await fetch(`/api/projects/${project.id}/`, {
                method: 'PATCH', headers: this.hdrs(),
                body: JSON.stringify({ priority: newPriority })
            });
        },

        // Modal
        openNewProject() { this.modal = { show: true, mode: 'new', editId: null, saving: false, form: this.emptyForm() }; },
        openEdit(p) {
            this.modal = {
                show: true, mode: 'edit', editId: p.id, saving: false,
                form: { title: p.title, description: p.description, emoji: p.emoji, domain: p.domain, status: p.status, priority: p.priority, deadline: p.deadline || '', next_action: p.next_action, is_public: p.is_public }
            };
        },
        closeModal() { this.modal.show = false; },
        async saveProject() {
            if (!this.modal.form.title.trim()) return;
            this.modal.saving = true;
            try {
                const isNew = this.modal.mode === 'new';
                const url = isNew ? '/api/projects/' : `/api/projects/${this.modal.editId}/`;
                // Exclude AI-specific fields from the project payload
                const { aiEnabled, aiTeamSize, ...projectPayload } = this.modal.form;
                if (projectPayload.deadline === '') projectPayload.deadline = null;
                const res = await fetch(url, { method: isNew ? 'POST' : 'PATCH', headers: this.hdrs(), body: JSON.stringify(projectPayload) });
                const saved = await res.json();
                if (!res.ok) { 
                    alert('Save error: ' + JSON.stringify(saved));
                    console.error('Save error', saved); 
                    return; 
                }

                if (isNew && aiEnabled) {
                    // Call AI scaffold
                    try {
                        const aiRes = await fetch('/api/ai/scaffold/apply/', {
                            method: 'POST',
                            headers: this.hdrs(),
                            body: JSON.stringify({
                                module: 'projects',
                                provider: 'ollama',
                                model: 'llama3.2:3b',
                                context: {
                                    project_id: saved.id,
                                    title: saved.title,
                                    description: saved.description || '',
                                    domain: saved.domain || '',
                                    team_size: aiTeamSize || 1,
                                },
                            }),
                        });
                        if (!aiRes.ok) {
                            const errData = await aiRes.json();
                            alert('AI Schema Generation failed: ' + (errData.error || typeof errData === 'string' ? errData : JSON.stringify(errData)));
                        }
                    } catch (e) {
                        alert('AI scaffold request failed (Network error): ' + e.message);
                    }
                    // Navigate to the new project page with AI-generated content (or empty if failed)
                    window.location.href = '/p/' + saved.id + '/';
                    return;
                }

                if (isNew) { this.projects.unshift(saved); }
                else { const i = this.projects.findIndex(p => p?.id === this.modal.editId); if (i !== -1) this.projects.splice(i, 1, saved); }
                this.closeModal();
            } finally { this.modal.saving = false; }
        },
        async deleteProject(p) {
            if (!confirm(`Видалити "${p.title}"?`)) return;
            await fetch(`/api/projects/${p?.id}/`, { method: 'DELETE', headers: this.auth() });
            this.projects = this.projects.filter(x => x && x.id !== p?.id);
        },

        // Drag & drop
        onDragStart(e, project) { this.dragging = project; e.dataTransfer.effectAllowed = 'move'; },
        async onDrop(e, newStatus) {
            if (!this.dragging || this.dragging.status === newStatus) return;
            this.dragging.status = newStatus;
            const p = this.dragging;
            this.dragging = null;
            await fetch(`/api/projects/${p?.id}/status/`, { method: 'PATCH', headers: this.hdrs(), body: JSON.stringify({ status: newStatus }) });
        },

        // Actions
        startAddAction(projectId) { this.addingActionFor = projectId; this.newActionText = ''; },
        async saveAction(project) {
            if (!this.newActionText.trim()) return;
            const res = await fetch(`/api/projects/${project?.id}/actions/`, { method: 'POST', headers: this.hdrs(), body: JSON.stringify({ text: this.newActionText }) });
            const action = await res.json();
            if (!project.actions) project.actions = [];
            project.actions.push(action);
            this.addingActionFor = null;
            this.newActionText = '';
        },
        async toggleAction(project, action) {
            action.is_done = !action.is_done;
            await fetch(`/api/projects/actions/${action?.id}/`, { method: 'PATCH', headers: this.hdrs(), body: JSON.stringify({ is_done: action.is_done }) });
        },

        // Display helpers
        priorityColor(p) { return { critical: 'red', high: 'yellow', medium: 'green', low: 'secondary' }[p] || 'secondary'; },
        priorityLabel(p) { return { critical: '🔴', high: '🟡', medium: '🟢', low: '⚪' }[p] || p; },
        priorityText(p) { return { critical: 'Крит', high: 'Висок', medium: 'Серед', low: 'Низьк' }[p] || p; },
        domainColor(d) { return (this.domains.find(x => x.key === d) || {}).color || '#666'; },
        domainLabel(d) { return (this.domains.find(x => x.key === d) || {}).label || d; },
        formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'short' }); },
    }
};
</script>

<style scoped>
/* Layout */
.eme-app-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; padding-bottom:14px; border-bottom:1px solid var(--tblr-border-color); flex-wrap:wrap; gap:10px; }
.eme-app-title { font-size:1.4rem; font-weight:800; background:var(--eme-grad,linear-gradient(135deg,#00e5ff,#6c00ff)); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; margin:0; }

.kanban-wrapper { display:flex; gap:14px; align-items:flex-start; overflow-x:auto; min-height:calc(100vh - 180px); }
.kanban-board { display:flex; gap:14px; overflow-x:auto; padding-bottom:16px; align-items:flex-start; flex:1; min-width:0; }

/* Columns */
.kanban-col { flex:0 0 265px; display:flex; flex-direction:column; gap:10px; }
.kanban-col-header { display:flex; align-items:center; font-weight:700; font-size:12px; text-transform:uppercase; letter-spacing:.5px; color:var(--tblr-secondary); padding:6px 4px; }
.kanban-col-body { flex:1; display:flex; flex-direction:column; gap:10px; background:rgba(255,255,255,.02); border:1px dashed var(--tblr-border-color); border-radius:12px; padding:10px; min-height:120px; transition:background .15s; }
.kanban-col-body:has(.kanban-card[draggable]:hover) { background:rgba(0,229,255,.03); }

/* This-week column highlight */
.kanban-col--this-week > .kanban-col-header { color:#ff6b35; }
.kanban-col--this-week > .kanban-col-body { border-color:#ff6b3544; background:rgba(255,107,53,.03); }

/* Cards */
.kanban-card { background:var(--tblr-card-bg); border-radius:10px; padding:12px; border-left:3px solid; cursor:grab; transition:box-shadow .15s,transform .15s; }
.kanban-card:hover { box-shadow:0 4px 18px rgba(0,0,0,.28); transform:translateY(-1px); }
.kanban-card:active { cursor:grabbing; }
.kanban-card-title { font-weight:700; font-size:13px; line-height:1.3; }
.drag-handle { color:var(--tblr-secondary); opacity:.4; cursor:grab; font-size:14px; flex-shrink:0; user-select:none; }
.drag-handle:hover { opacity:.8; }

.kanban-next-action { font-size:11px; color:var(--eme-accent,#00e5ff); background:rgba(0,229,255,.07); border-radius:6px; padding:4px 8px; margin-top:4px; }
.kanban-action-item { display:flex; align-items:flex-start; gap:6px; font-size:11px; padding:2px 4px; cursor:pointer; border-radius:4px; transition:background .12s; }
.kanban-action-item:hover { background:rgba(255,255,255,.06); }
.kanban-empty { text-align:center; color:var(--tblr-secondary); font-size:12px; padding:20px 0; opacity:.4; }

/* Priority badge click */
.kanban-priority-badge { cursor:pointer; user-select:none; transition:opacity .15s; }
.kanban-priority-badge:hover { opacity:.8; }

/* Progress bar */
.kanban-progress-bar { height:4px; background:rgba(255,255,255,.1); border-radius:2px; overflow:hidden; }
.kanban-progress-fill { height:100%; background:var(--eme-accent,#00e5ff); border-radius:2px; transition:width .3s; }
.kanban-progress-done { background:#20c997; }

/* Border priorities */
.border-red { border-left-color:#dc3545 !important; }
.border-yellow { border-left-color:#ffc107 !important; }
.border-green { border-left-color:#20c997 !important; }
.border-secondary { border-left-color:#6c757d !important; }

/* Deadline Sidebar */
.kanban-deadline-sidebar { flex:0 0 220px; background:var(--tblr-card-bg); border:1px solid var(--tblr-border-color); border-radius:12px; padding:12px; display:flex; flex-direction:column; gap:6px; max-height:calc(100vh - 180px); overflow-y:auto; }
.deadline-sidebar-header { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--tblr-secondary); padding-bottom:6px; border-bottom:1px solid var(--tblr-border-color); margin-bottom:4px; }
.deadline-empty { font-size:12px; color:var(--tblr-secondary); opacity:.5; text-align:center; padding:16px 0; }

.deadline-item { padding:8px 10px; border-radius:8px; cursor:pointer; border-left:3px solid transparent; transition:opacity .15s; }
.deadline-item:hover { opacity:.85; }
.deadline-item-title { font-size:12px; font-weight:700; line-height:1.3; }
.deadline-item-date { font-size:10px; margin-top:2px; opacity:.7; }
.deadline-item-action { font-size:10px; margin-top:3px; color:var(--eme-accent,#00e5ff); opacity:.8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.deadline-days { font-weight:700; margin-left:4px; }

/* Deadline urgency colors */
.deadline-item--urgent { background:rgba(220,53,69,.1); border-left-color:#dc3545; }
.deadline-item--soon { background:rgba(255,193,7,.08); border-left-color:#ffc107; }
.deadline-item--ok { background:rgba(32,201,151,.06); border-left-color:#20c997; }
.deadline-item--overdue { background:rgba(220,53,69,.15); border-left-color:#dc3545; }

/* Modal */
.eme-modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:1050; display:flex; align-items:center; justify-content:center; padding:16px; }
.eme-modal { background:var(--tblr-card-bg); border:1px solid var(--tblr-border-color); border-radius:16px; width:100%; max-width:520px; max-height:90vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,.5); }
.eme-modal-header { display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--tblr-border-color); }
.eme-modal-body { padding:16px 20px; }
.eme-modal-footer { display:flex; justify-content:flex-end; gap:8px; padding:12px 20px; border-top:1px solid var(--tblr-border-color); }
</style>
