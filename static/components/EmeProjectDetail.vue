<template>
    <div class="pd-overlay" @click.self="$emit('close')">
        <div class="pd-panel">

            <!-- ── Header ─────────────────────────────────────────────────── -->
            <div class="pd-header">
                <div class="d-flex align-items-center gap-2 min-w-0">
                    <span style="font-size:1.6rem;flex-shrink:0">{{ project.emoji }}</span>
                    <div class="min-w-0">
                        <h1 class="pd-title">{{ project.title }}</h1>
                        <div class="d-flex gap-2 mt-1 flex-wrap">
                            <span class="badge" :style="'background:' + domainColor(project.domain) + '22;color:' + domainColor(project.domain)">
                                {{ domainLabel(project.domain) }}
                            </span>
                            <span class="badge" :class="'bg-' + priorityColor(project.priority) + '-lt'">
                                {{ priorityLabel(project.priority) }}
                            </span>
                            <span v-if="project.deadline" class="badge bg-red-lt">
                                📅 {{ formatDate(project.deadline) }}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="d-flex gap-2 flex-shrink-0">
                    <button class="btn btn-sm" :class="showAI ? 'btn-warning' : 'btn-ghost-warning'"
                        @click="showAI = !showAI" title="AI Планувальник">🤖 AI</button>
                    <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">← Назад</button>
                </div>
            </div>

            <!-- ── Body ──────────────────────────────────────────────────── -->
            <div class="pd-body">

                <!-- Left: Action Kanban + Team -->
                <div class="pd-main">

                    <!-- Action Kanban -->
                    <div class="pd-section-title">
                        📋 Дії
                        <button class="btn btn-xs btn-primary ms-2" @click="openNewAction">+ Дія</button>
                    </div>

                    <div v-if="loadingActions" class="text-center py-4">
                        <div class="spinner-border spinner-border-sm text-cyan"></div>
                    </div>

                    <div v-else class="action-kanban">
                        <div v-for="col in actionCols" :key="col.key" class="action-col">
                            <div class="action-col-header">
                                {{ col.icon }} {{ col.label }}
                                <span class="badge bg-secondary ms-1">{{ getColActions(col.key).length }}</span>
                            </div>
                            <div class="action-col-body"
                                @dragover.prevent
                                @drop="onActionDrop($event, col.key)">

                                <div v-for="a in getColActions(col.key)" :key="a?.id"
                                    class="action-card"
                                    :class="[
                                        'border-' + priorityColor(a.priority),
                                        { 'action-card--blocked': a.is_blocked }
                                    ]"
                                    draggable="true"
                                    @dragstart="draggingAction = a">

                                    <!-- Blocked indicator -->
                                    <div v-if="a.is_blocked" class="action-blocked-badge">
                                        🔒 Чекає: {{ a.depends_on_text }}
                                    </div>

                                    <div class="d-flex align-items-start justify-content-between gap-1">
                                        <div class="action-card-text">{{ a.text }}</div>
                                        <div class="d-flex gap-1 flex-shrink-0">
                                            <button class="btn btn-icon btn-xs btn-ghost-secondary"
                                                @click.stop="openEditAction(a)">✏️</button>
                                            <button class="btn btn-icon btn-xs btn-ghost-danger"
                                                @click.stop="deleteAction(a)">🗑</button>
                                        </div>
                                    </div>

                                    <div class="d-flex flex-wrap gap-1 mt-1">
                                        <span class="badge badge-sm" :class="'bg-' + priorityColor(a.priority) + '-lt'">
                                            {{ priorityLabel(a.priority) }}
                                        </span>
                                        <span v-if="a.deadline" class="badge badge-sm bg-red-lt">
                                            📅 {{ formatDate(a.deadline) }}
                                        </span>
                                        <span v-if="a.assignee_role" class="badge badge-sm bg-blue-lt">
                                            {{ a.assignee_role }}
                                        </span>
                                    </div>
                                </div>

                                <div v-if="getColActions(col.key).length === 0" class="action-empty">
                                    Перетягни сюди
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Team / Roles -->
                    <div class="pd-section-title mt-4">
                        👥 Команда
                        <button class="btn btn-xs btn-ghost-secondary ms-2" @click="showRoleModal = true">+ Роль</button>
                        <button class="btn btn-xs btn-ghost-secondary ms-1" @click="showMemberModal = true">+ Учасник</button>
                    </div>

                    <div v-if="roles.length === 0 && members.length === 0" class="text-muted small py-2">
                        Додай ролі і запроси учасників
                    </div>

                    <!-- Roles chips -->
                    <div class="d-flex flex-wrap gap-2 mb-3">
                        <div v-for="r in roles" :key="r?.id" class="role-chip">
                            {{ r.emoji }} <strong>{{ r.name }}</strong>
                            <span class="badge bg-secondary-lt ms-1">{{ r.members_count }}</span>
                            <button class="btn-close btn-close-sm ms-1" @click="deleteRole(r)"></button>
                        </div>
                    </div>

                    <!-- Members list -->
                    <div class="members-list">
                        <div v-for="m in members" :key="m?.id" class="member-row">
                            <div class="member-avatar">{{ (m.display_name || m.username || '?')[0].toUpperCase() }}</div>
                            <div class="member-info">
                                <strong>@{{ m.username }}</strong>
                                <span v-if="m.role_name" class="member-role">{{ m.role_emoji }} {{ m.role_name }}</span>
                                <span v-else class="member-role text-muted">Учасник</span>
                            </div>
                            <div class="d-flex gap-1 ms-auto">
                                <select class="form-select form-select-sm" style="width:140px"
                                    :value="m.role"
                                    @change="changeMemberRole(m, $event.target.value)">
                                    <option value="">— Роль —</option>
                                    <option v-for="r in roles" :key="r?.id" :value="r?.id">{{ r.emoji }} {{ r.name }}</option>
                                </select>
                                <button class="btn btn-xs btn-ghost-danger" @click="deleteMember(m)">✕</button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right: AI Panel -->
                <div v-if="showAI" class="pd-ai-panel">
                    <div class="ai-header">🤖 AI Планувальник</div>
                    <div class="ai-status" :class="aiOnline ? 'text-success' : 'text-muted'">
                        {{ aiOnline ? '● Ollama онлайн — ' + aiModel : '○ Ollama офлайн' }}
                    </div>

                    <div class="ai-prompt-area">
                        <textarea class="form-control form-control-sm"
                            v-model="aiPrompt"
                            rows="3"
                            placeholder="Опиши що потрібно зробити, або залиш пусто для авто-аналізу..."></textarea>
                        <button class="btn btn-sm btn-warning w-100 mt-2"
                            @click="runAIPlan"
                            :disabled="aiLoading || !aiOnline">
                            <span v-if="aiLoading" class="spinner-border spinner-border-sm me-1"></span>
                            {{ aiLoading ? 'Генерую...' : '🤖 Згенерувати план' }}
                        </button>
                    </div>

                    <div v-if="aiError" class="alert alert-danger py-2 small mt-2">{{ aiError }}</div>

                    <!-- AI Result -->
                    <div v-if="aiPlan" class="ai-result">
                        <div class="ai-result-section">
                            <strong>👥 Ролі:</strong>
                            <div v-for="(r, i) in aiPlan.roles" :key="i" class="ai-result-item">
                                {{ r.emoji }} {{ r.name }}
                                <small class="text-muted d-block">{{ r.description }}</small>
                            </div>
                        </div>
                        <div class="ai-result-section mt-2">
                            <strong>📋 Дії:</strong>
                            <div v-for="(a, i) in aiPlan.actions" :key="i" class="ai-result-item">
                                <span class="badge badge-sm me-1" :class="'bg-' + priorityColor(a.priority) + '-lt'">{{ priorityLabel(a.priority) }}</span>
                                {{ a.text }}
                                <small v-if="a.role_name" class="text-muted"> — {{ a.role_name }}</small>
                            </div>
                        </div>
                        <button class="btn btn-sm btn-success w-100 mt-2" @click="applyAIPlan">
                            ✅ Застосувати план
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- ── Action Modal ───────────────────────────────────────────────── -->
        <div v-if="actionModal.show" class="eme-modal-overlay" @click.self="actionModal.show = false">
            <div class="eme-modal">
                <div class="eme-modal-header">
                    <strong>{{ actionModal.mode === 'new' ? '➕ Нова дія' : '✏️ Редагувати дію' }}</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="actionModal.show = false">✕</button>
                </div>
                <div class="eme-modal-body">
                    <div class="mb-2">
                        <label class="form-label">Текст дії *</label>
                        <input class="form-control" v-model="actionModal.form.text" placeholder="Що зробити?">
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6">
                            <label class="form-label">Пріоритет</label>
                            <select class="form-select" v-model="actionModal.form.priority">
                                <option value="critical">🔴 Критичний</option>
                                <option value="high">🟡 Високий</option>
                                <option value="medium">🟢 Середній</option>
                                <option value="low">⚪ Низький</option>
                            </select>
                        </div>
                        <div class="col-6">
                            <label class="form-label">Статус</label>
                            <select class="form-select" v-model="actionModal.form.status">
                                <option value="todo">📋 Задача</option>
                                <option value="doing">🔧 Виконується</option>
                                <option value="done">✅ Готово</option>
                            </select>
                        </div>
                    </div>
                    <div class="row g-2 mb-2">
                        <div class="col-6">
                            <label class="form-label">Дедлайн</label>
                            <input type="date" class="form-control" v-model="actionModal.form.deadline">
                        </div>
                        <div class="col-6">
                            <label class="form-label">Виконавець</label>
                            <select class="form-select" v-model="actionModal.form.assignee">
                                <option :value="null">— Без виконавця —</option>
                                <option v-for="m in members" :key="m?.id" :value="m?.id">
                                    {{ m.role_emoji || '👤' }} {{ m.username }}{{ m.role_name ? ' (' + m.role_name + ')' : '' }}
                                </option>
                            </select>
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">🔒 Залежить від (виконати після)</label>
                        <select class="form-select" v-model="actionModal.form.depends_on">
                            <option :value="null">— Незалежна —</option>
                            <option v-for="a in otherActions" :key="a?.id" :value="a?.id">
                                {{ (a.text || '').slice(0, 50) }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="eme-modal-footer">
                    <button class="btn btn-ghost-secondary" @click="actionModal.show = false">Скасувати</button>
                    <button class="btn btn-primary" @click="saveAction" :disabled="actionModal.saving">
                        <span v-if="actionModal.saving" class="spinner-border spinner-border-sm me-1"></span>
                        {{ actionModal.mode === 'new' ? 'Створити' : 'Зберегти' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- ── Role Modal ─────────────────────────────────────────────────── -->
        <div v-if="showRoleModal" class="eme-modal-overlay" @click.self="showRoleModal = false">
            <div class="eme-modal" style="max-width:380px">
                <div class="eme-modal-header">
                    <strong>➕ Нова роль</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showRoleModal = false">✕</button>
                </div>
                <div class="eme-modal-body">
                    <div class="row g-2 mb-2">
                        <div class="col-3">
                            <label class="form-label">Emoji</label>
                            <input class="form-control" v-model="roleForm.emoji" maxlength="4">
                        </div>
                        <div class="col-9">
                            <label class="form-label">Назва ролі *</label>
                            <input class="form-control" v-model="roleForm.name" placeholder="напр. Шашличник">
                        </div>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Опис (не обов'язково)</label>
                        <input class="form-control" v-model="roleForm.description" placeholder="Що робить ця роль?">
                    </div>
                </div>
                <div class="eme-modal-footer">
                    <button class="btn btn-ghost-secondary" @click="showRoleModal = false">Скасувати</button>
                    <button class="btn btn-primary" @click="saveRole">Створити роль</button>
                </div>
            </div>
        </div>

        <!-- ── Member Modal ───────────────────────────────────────────────── -->
        <div v-if="showMemberModal" class="eme-modal-overlay" @click.self="showMemberModal = false">
            <div class="eme-modal" style="max-width:380px">
                <div class="eme-modal-header">
                    <strong>➕ Додати учасника</strong>
                    <button class="btn btn-xs btn-ghost-secondary" @click="showMemberModal = false">✕</button>
                </div>
                <div class="eme-modal-body">
                    <div class="mb-2">
                        <label class="form-label">User ID</label>
                        <input class="form-control" v-model.number="memberForm.user" type="number" placeholder="ID юзера з EME мережі">
                        <div class="form-hint">Можна знайти у профілі учасника</div>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Роль</label>
                        <select class="form-select" v-model="memberForm.role">
                            <option :value="null">— Без ролі (Учасник) —</option>
                            <option v-for="r in roles" :key="r?.id" :value="r?.id">{{ r.emoji }} {{ r.name }}</option>
                        </select>
                    </div>
                </div>
                <div class="eme-modal-footer">
                    <button class="btn btn-ghost-secondary" @click="showMemberModal = false">Скасувати</button>
                    <button class="btn btn-primary" @click="saveMember">Додати</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

export default {
    props: ['project', 'auth'],
    emits: ['close'],
    data() {
        return {
            actions: [],
            roles: [],
            members: [],
            loadingActions: true,
            draggingAction: null,
            showAI: false,
            aiOnline: false,
            aiModel: '',
            aiPrompt: '',
            aiLoading: false,
            aiPlan: null,
            aiError: '',
            showRoleModal: false,
            showMemberModal: false,
            roleForm: { name: '', emoji: '👤', description: '' },
            memberForm: { user: null, role: null },
            actionModal: {
                show: false, mode: 'new', editId: null, saving: false,
                form: { text: '', priority: 'medium', status: 'todo', deadline: '', assignee: null, depends_on: null }
            },
            actionCols: [
                { key: 'todo', icon: '📋', label: 'Задачі' },
                { key: 'doing', icon: '🔧', label: 'Виконується' },
                { key: 'done', icon: '✅', label: 'Готово' },
            ],
            domains: [
                { key: 'life', label: '❤️ Особисте', color: '#ff4757' },
                { key: 'business', label: '💼 Бізнес', color: '#ffa502' },
                { key: 'eme', label: '⚡ EME', color: '#00e5ff' },
                { key: 'tech', label: '🔧 Технічне', color: '#2ed573' },
                { key: 'community', label: '🤝 Спільнота', color: '#a29bfe' },
            ],
        };
    },
    computed: {
        otherActions() {
            const safe = Array.isArray(this.actions) ? this.actions : [];
            if (!this.actionModal.editId) return safe;
            return safe.filter(a => a && a.id !== this.actionModal.editId);
        }
    },
    async mounted() {
        await Promise.all([
            this.loadActions(),
            this.loadRoles(),
            this.loadMembers(),
        ]);
        this.checkAI();
    },
    methods: {
        hdrs() { return { 'Content-Type': 'application/json', ...this.auth() }; },
        pid() { return this.project?.id || 0; },

        // ── Data loading ──────────────────────────────────────────────────
        async loadActions() {
            this.loadingActions = true;
            try {
                const res = await fetch(`/api/projects/${this.pid()}/actions/`, { headers: this.auth() });
                const data = await res.json();
                this.actions = Array.isArray(data) ? data : [];
            } finally { this.loadingActions = false; }
        },
        async loadRoles() {
            const res = await fetch(`/api/projects/${this.pid()}/roles/`, { headers: this.auth() });
            const data = await res.json();
            this.roles = Array.isArray(data) ? data : [];
        },
        async loadMembers() {
            const res = await fetch(`/api/projects/${this.pid()}/members/`, { headers: this.auth() });
            const data = await res.json();
            this.members = Array.isArray(data) ? data : [];
        },

        // ── Action Kanban ─────────────────────────────────────────────────
        getColActions(status) {
            const safeActions = Array.isArray(this.actions) ? this.actions : [];
            return safeActions
                .filter(a => a.status === status)
                .sort((a, b) => {
                    const pa = PRIORITY_ORDER[a.priority] ?? 9;
                    const pb = PRIORITY_ORDER[b.priority] ?? 9;
                    return pa - pb;
                });
        },
        async onActionDrop(e, newStatus) {
            if (!this.draggingAction || this.draggingAction.status === newStatus) return;
            const a = this.draggingAction;
            this.draggingAction = null;
            const res = await fetch(`/api/projects/actions/${a?.id}/status/`, {
                method: 'PATCH', headers: this.hdrs(),
                body: JSON.stringify({ status: newStatus })
            });
            if (res.ok) {
                const updated = await res.json();
                const idx = this.actions.findIndex(x => x && x.id === a?.id);
                if (idx !== -1) this.actions.splice(idx, 1, updated);
            } else {
                const err = await res.json();
                alert(err.error || 'Помилка');
            }
        },

        // ── Action CRUD ───────────────────────────────────────────────────
        openNewAction() {
            this.actionModal = {
                show: true, mode: 'new', editId: null, saving: false,
                form: { text: '', priority: 'medium', status: 'todo', deadline: '', assignee: null, depends_on: null }
            };
        },
        openEditAction(a) {
            this.actionModal = {
                show: true, mode: 'edit', editId: a?.id, saving: false,
                form: { text: a.text, priority: a.priority, status: a.status,
                        deadline: a.deadline || '', assignee: a.assignee || null,
                        depends_on: a.depends_on || null }
            };
        },
        async saveAction() {
            if (!this.actionModal.form.text.trim()) return;
            this.actionModal.saving = true;
            try {
                const isNew = this.actionModal.mode === 'new';
                const url = isNew ? `/api/projects/${this.pid()}/actions/` : `/api/projects/actions/${this.actionModal.editId}/`;
                const res = await fetch(url, {
                    method: isNew ? 'POST' : 'PATCH',
                    headers: this.hdrs(),
                    body: JSON.stringify(this.actionModal.form)
                });
                const saved = await res.json();
                if (isNew) { this.actions.push(saved); }
                else {
                    const idx = this.actions.findIndex(a => a && a.id === this.actionModal.editId);
                    if (idx !== -1) this.actions.splice(idx, 1, saved);
                }
                this.actionModal.show = false;
            } finally { this.actionModal.saving = false; }
        },
        async deleteAction(a) {
            if (!confirm(`Видалити дію "${a.text}"?`)) return;
            await fetch(`/api/projects/actions/${a?.id}/`, { method: 'DELETE', headers: this.auth() });
            this.actions = (this.actions || []).filter(x => x && x.id !== a?.id);
        },

        // ── Roles ─────────────────────────────────────────────────────────
        async saveRole() {
            if (!this.roleForm.name.trim()) return;
            const res = await fetch(`/api/projects/${this.pid()}/roles/`, {
                method: 'POST', headers: this.hdrs(), body: JSON.stringify(this.roleForm)
            });
            const saved = await res.json();
            this.roles.push(saved);
            this.roleForm = { name: '', emoji: '👤', description: '' };
            this.showRoleModal = false;
        },
        async deleteRole(r) {
            if (!confirm(`Видалити роль "${r.name}"?`)) return;
            await fetch(`/api/projects/roles/${r?.id}/`, { method: 'DELETE', headers: this.auth() });
            this.roles = (this.roles || []).filter(x => x && x.id !== r?.id);
        },

        // ── Members ───────────────────────────────────────────────────────
        async saveMember() {
            if (!this.memberForm.user) return;
            const res = await fetch(`/api/projects/${this.pid()}/members/`, {
                method: 'POST', headers: this.hdrs(), body: JSON.stringify(this.memberForm)
            });
            const saved = await res.json();
            this.members.push(saved);
            this.memberForm = { user: null, role: null };
            this.showMemberModal = false;
        },
        async changeMemberRole(member, roleId) {
            const res = await fetch(`/api/projects/members/${member.id}/`, {
                method: 'PATCH', headers: this.hdrs(),
                body: JSON.stringify({ role: roleId || null })
            });
            const updated = await res.json();
            const idx = this.members.findIndex(m => m && m.id === member?.id);
            if (idx !== -1) this.members.splice(idx, 1, updated);
        },
        async deleteMember(m) {
            if (!confirm(`Видалити @${m.username} з проекту?`)) return;
            await fetch(`/api/projects/members/${m?.id}/`, { method: 'DELETE', headers: this.auth() });
            this.members = (this.members || []).filter(x => x && x.id !== m?.id);
        },

        // ── AI ────────────────────────────────────────────────────────────
        async checkAI() {
            try {
                const res = await fetch('/api/projects/ai/models/', { headers: this.auth() });
                const data = await res.json();
                this.aiOnline = data.online;
                this.aiModel = data.models[0] || 'llama3';
            } catch { this.aiOnline = false; }
        },
        async runAIPlan() {
            this.aiLoading = true;
            this.aiError = '';
            this.aiPlan = null;
            try {
                const res = await fetch('/api/projects/ai/plan/', {
                    method: 'POST', headers: this.hdrs(),
                    body: JSON.stringify({
                        project_id: this.pid(),
                        prompt: this.aiPrompt,
                        model: this.aiModel
                    })
                });
                const data = await res.json();
                if (res.ok) { this.aiPlan = data.plan; }
                else { this.aiError = data.error || 'Помилка AI'; }
            } catch (e) {
                this.aiError = 'Мережева помилка';
            } finally { this.aiLoading = false; }
        },
        async applyAIPlan() {
            if (!this.aiPlan) return;
            // 1. Create roles from plan
            const roleMap = {};
            for (const r of (this.aiPlan.roles || [])) {
                const res = await fetch(`/api/projects/${this.pid()}/roles/`, {
                    method: 'POST', headers: this.hdrs(), body: JSON.stringify(r)
                });
                if (res.ok) {
                    const saved = await res.json();
                    this.roles.push(saved);
                    roleMap[r.name] = saved.id;
                }
            }
            // 2. Create actions from plan
            const createdActions = [];
            for (const a of (this.aiPlan.actions || [])) {
                const body = {
                    text: a.text,
                    priority: a.priority || 'medium',
                    status: 'todo',
                    depends_on: a.depends_on_index != null ? (createdActions[a.depends_on_index]?.id ?? null) : null
                };
                const res = await fetch(`/api/projects/${this.pid()}/actions/`, {
                    method: 'POST', headers: this.hdrs(), body: JSON.stringify(body)
                });
                if (res.ok) {
                    const saved = await res.json();
                    this.actions.push(saved);
                    createdActions.push(saved);
                } else { createdActions.push(null); }
            }
            this.aiPlan = null;
            alert('План застосовано!');
        },

        // ── Display helpers ───────────────────────────────────────────────
        priorityColor(p) { return { critical: 'red', high: 'yellow', medium: 'green', low: 'secondary' }[p] || 'secondary'; },
        priorityLabel(p) { return { critical: '🔴 Крит', high: '🟡 Висок', medium: '🟢 Серед', low: '⚪ Низьк' }[p] || p; },
        domainColor(d) { return (this.domains.find(x => x.key === d) || {}).color || '#666'; },
        domainLabel(d) { return (this.domains.find(x => x.key === d) || {}).label || d; },
        formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString('uk-UA', { day: 'numeric', month: 'short' }); },
    }
};
</script>

<style scoped>
/* Overlay */
.pd-overlay { position:fixed; inset:0; background:rgba(0,0,0,.65); z-index:1100; display:flex; align-items:stretch; justify-content:flex-end; }
.pd-panel { width:100%; max-width:1100px; background:var(--tblr-card-bg); display:flex; flex-direction:column; overflow:hidden; box-shadow:-8px 0 40px rgba(0,0,0,.4); }

/* Header */
.pd-header { display:flex; align-items:center; justify-content:space-between; padding:14px 20px; border-bottom:1px solid var(--tblr-border-color); gap:12px; flex-shrink:0; }
.pd-title { font-size:1.3rem; font-weight:800; margin:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* Body */
.pd-body { display:flex; gap:0; flex:1; overflow:hidden; }
.pd-main { flex:1; overflow-y:auto; padding:16px 20px; }
.pd-section-title { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--tblr-secondary); margin-bottom:10px; display:flex; align-items:center; }

/* Action Kanban */
.action-kanban { display:flex; gap:10px; align-items:flex-start; min-height:220px; }
.action-col { flex:1; min-width:0; display:flex; flex-direction:column; gap:8px; }
.action-col-header { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.4px; color:var(--tblr-secondary); padding:4px 2px; display:flex; align-items:center; }
.action-col-body { flex:1; min-height:100px; background:rgba(255,255,255,.02); border:1px dashed var(--tblr-border-color); border-radius:10px; padding:8px; display:flex; flex-direction:column; gap:8px; }
.action-card { background:var(--tblr-card-bg); border-radius:8px; padding:10px; border-left:3px solid; cursor:grab; transition:box-shadow .15s,transform .1s; }
.action-card:hover { box-shadow:0 3px 14px rgba(0,0,0,.25); transform:translateY(-1px); }
.action-card--blocked { opacity:.6; cursor:not-allowed; }
.action-card-text { font-size:13px; font-weight:600; line-height:1.3; }
.action-blocked-badge { font-size:10px; color:var(--tblr-danger); background:rgba(220,53,69,.1); border-radius:4px; padding:2px 6px; margin-bottom:4px; }
.action-empty { text-align:center; color:var(--tblr-secondary); font-size:11px; padding:16px 0; opacity:.4; }

/* Borders */
.border-red { border-left-color:#dc3545 !important; }
.border-yellow { border-left-color:#ffc107 !important; }
.border-green { border-left-color:#20c997 !important; }
.border-secondary { border-left-color:#6c757d !important; }

/* Roles */
.role-chip { display:inline-flex; align-items:center; gap:4px; background:rgba(255,255,255,.06); border:1px solid var(--tblr-border-color); border-radius:20px; padding:4px 10px; font-size:12px; }

/* Members */
.members-list { display:flex; flex-direction:column; gap:8px; }
.member-row { display:flex; align-items:center; gap:10px; background:rgba(255,255,255,.03); border-radius:8px; padding:8px 12px; }
.member-avatar { width:32px; height:32px; border-radius:50%; background:var(--eme-grad,linear-gradient(135deg,#00e5ff,#6c00ff)); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px; flex-shrink:0; }
.member-info { display:flex; flex-direction:column; min-width:0; }
.member-role { font-size:11px; color:var(--tblr-secondary); margin-top:1px; }

/* AI Panel */
.pd-ai-panel { width:260px; flex-shrink:0; border-left:1px solid var(--tblr-border-color); padding:14px; display:flex; flex-direction:column; gap:10px; overflow-y:auto; background:rgba(255,200,50,.03); }
.ai-header { font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; }
.ai-status { font-size:10px; }
.ai-prompt-area { display:flex; flex-direction:column; gap:6px; }
.ai-result { background:rgba(255,255,255,.04); border:1px solid var(--tblr-border-color); border-radius:8px; padding:10px; }
.ai-result-section { font-size:12px; }
.ai-result-item { margin-top:4px; font-size:11px; line-height:1.4; }

/* Modals */
.eme-modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:1200; display:flex; align-items:center; justify-content:center; padding:16px; }
.eme-modal { background:var(--tblr-card-bg); border:1px solid var(--tblr-border-color); border-radius:16px; width:100%; max-width:520px; max-height:90vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,.5); }
.eme-modal-header { display:flex; justify-content:space-between; align-items:center; padding:14px 20px; border-bottom:1px solid var(--tblr-border-color); }
.eme-modal-body { padding:14px 20px; }
.eme-modal-footer { display:flex; justify-content:flex-end; gap:8px; padding:12px 20px; border-top:1px solid var(--tblr-border-color); }
</style>
