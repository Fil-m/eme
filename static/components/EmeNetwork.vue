<template>
    <div class="eme-app-page">
        <div class="eme-app-header">
            <h1 class="eme-app-title">Мережа</h1>
            <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
        </div>

        <!-- Network tabs -->
        <ul class="nav nav-tabs mb-4">
            <li class="nav-item">
                <a class="nav-link" :class="{active: networkTab==='users'}" href="#"
                    @click.prevent="networkTab='users'">🌐 Учасники</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" :class="{active: networkTab==='chat'}" href="#"
                    @click.prevent="networkTab='chat'; loadChatRooms()">💬 Чат</a>
            </li>
        </ul>

        <!-- TAB: Users -->
        <div v-if="networkTab==='users'">
            <div class="mb-3 d-flex justify-content-between align-items-center">
                <input type="text" class="form-control" style="max-width:300px;" v-model="networkSearch"
                    placeholder="🔍 Пошук учасників...">
                <button class="btn btn-sm btn-ghost-info" @click="fetchNetworkUsers" :disabled="loading">
                    <i class="ti ti-refresh" :class="{'ti-spin': loading}"></i> Оновити
                </button>
            </div>

            <!-- External Discovery Section -->
            <div v-if="externalNodes.length" class="mb-4">
                <div class="subheader mb-2 text-info">📡 Знайдено в локальній мережі (Mesh)</div>
                <div class="row g-2">
                    <div v-for="node in externalNodes" :key="node.ip" class="col-md-4">
                        <div class="card bg-info-lt border-info-subtle shadow-none" style="cursor: pointer;" @click="visitExternalNode(node)">
                            <div class="card-body p-2 d-flex align-items-center gap-2">
                                <div class="avatar avatar-xs bg-info text-white">📡</div>
                                <div class="text-truncate">
                                    <div class="fw-bold small">{{ node.name }}</div>
                                    <div class="text-muted" style="font-size: 10px;">{{ node.ip }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="filteredNetworkUsers.length" class="row g-3">
                <div class="col-md-6 col-lg-4" v-for="u in filteredNetworkUsers" :key="u.id">
                    <div class="card card-hover shadow-sm border-0">
                        <div class="card-body p-3">
                            <div class="d-flex align-items-center gap-3">
                                <div class="avatar avatar-md avatar-rounded border overflow-hidden position-relative"
                                    :style="u.avatar ? 'background-image: url(' + u.avatar + ')' : ''">
                                    <span v-if="!u.avatar">{{ (u.username || 'U')[0].toUpperCase() }}</span>
                                    <span v-if="u.is_online"
                                        class="badge bg-success border-2 border-white p-1 position-absolute bottom-0 end-0"
                                        title="Online"></span>
                                </div>
                                <div class="flex-fill">
                                    <div class="fw-bold text-truncate">{{ u.first_name || u.username }}</div>
                                    <div class="text-muted small">@{{ u.username }}</div>
                                    <div class="mt-1">
                                        <span class="badge bg-blue-lt">Lvl {{ u.level }}</span>
                                        <span class="badge bg-cyan-lt ms-1">{{ u.points }} XP</span>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-3 d-flex gap-2">
                                <button class="btn btn-sm btn-outline-primary w-100"
                                    @click="$emit('visit-user', u)">Профіль</button>
                                <button class="btn btn-sm btn-outline-secondary w-100"
                                    @click="startDM(u)">💬 Написати</button>
                            </div>
                        </div>
                        <div class="card-footer bg-transparent py-1 text-center small text-muted border-0"
                            style="font-size: 10px;">
                            {{ u.is_online ? 'Зараз в мережі' : u.last_seen ? 'Останній раз: ' + new Date(u.last_seen).toLocaleString() : 'невідомо' }}
                        </div>
                    </div>
                </div>
            </div>
            <div v-else class="module-placeholder py-5">
                <div style="font-size:3rem;">🔍</div>
                <div class="mt-2 fw-bold">Нікого не знайдено</div>
                <div class="text-muted mt-1">Спробуйте інший запит або зачекайте на нових учасників</div>
            </div>
        </div>

        <!-- TAB: Chat -->
        <div v-if="networkTab==='chat'">
            <div class="row g-3">
                <!-- Chat Rooms List -->
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header"><strong>💬 Чати</strong></div>
                        <div class="list-group list-group-flush" style="max-height: 500px; overflow-y: auto;">
                            <a v-for="room in chatRooms" :key="room.id" href="#"
                                class="list-group-item list-group-item-action"
                                :class="{'active': activeChatRoom && activeChatRoom.id === room.id}"
                                @click.prevent="openChat(room)">
                                <div class="d-flex align-items-center gap-2">
                                    <div class="avatar avatar-xs avatar-rounded"
                                        :style="getChatPartner(room).avatar ? 'background-image: url(' + getChatPartner(room).avatar + ')' : ''">
                                        <span v-if="!getChatPartner(room).avatar">{{ (getChatPartner(room).username || 'U')[0].toUpperCase() }}</span>
                                    </div>
                                    <div class="text-truncate">{{ getChatPartner(room).first_name || getChatPartner(room).username }}</div>
                                </div>
                            </a>
                            <div v-if="!chatRooms.length" class="p-3 text-center text-muted small">Немає активних чатів</div>
                        </div>
                    </div>
                </div>

                <!-- Chat Messages -->
                <div class="col-md-8">
                    <div v-if="activeChatRoom" class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <strong>{{ getChatPartner(activeChatRoom).username }}</strong>
                            <span v-if="getChatPartner(activeChatRoom).is_online"
                                class="badge bg-success">online</span>
                        </div>
                        <div class="card-body eme-chat-body" ref="chatBody">
                            <div v-for="msg in messages" :key="msg.id" class="eme-message"
                                :class="msg.sender === user.id ? 'eme-message-out' : 'eme-message-in'">
                                <div class="msg-text">{{ msg.text }}</div>
                                <div class="msg-time mt-1 opacity-50" style="font-size:9px;">{{ new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</div>
                            </div>
                        </div>
                        <div class="card-footer p-2">
                            <div class="input-group">
                                <input type="text" class="form-control" v-model="newMessage"
                                    placeholder="Напишіть повідомлення..." @keyup.enter="sendMessage">
                                <button class="btn btn-primary" @click="sendMessage"
                                    :disabled="!newMessage.trim()">→</button>
                            </div>
                        </div>
                    </div>
                    <div v-else class="card">
                        <div class="card-body module-placeholder py-5">
                            <div style="font-size:3rem;">💬</div>
                            <div class="mt-2 fw-bold">Оберіть чат</div>
                            <div class="text-muted mt-1">або напишіть комусь зі вкладки "Учасники"</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: ['user', 'auth'],
    data() {
        return {
            networkTab: 'users',
            networkSearch: '',
            networkUsers: [],
            externalNodes: [],
            chatRooms: [],
            activeChatRoom: null,
            messages: [],
            newMessage: '',
            chatPolling: null,
            loading: false
        }
    },
    computed: {
        filteredNetworkUsers() {
            if (!this.networkSearch) return this.networkUsers;
            const s = this.networkSearch.toLowerCase();
            return this.networkUsers.filter(u => 
                u.username.toLowerCase().includes(s) || 
                (u.first_name && u.first_name.toLowerCase().includes(s))
            );
        }
    },
    mounted() {
        this.fetchNetworkUsers();
    },
    beforeUnmount() {
        if (this.chatPolling) clearInterval(this.chatPolling);
    },
    methods: {
        async fetchNetworkUsers() {
            this.loading = true;
            try {
                const res = await fetch('/api/network/discovery/', { headers: this.auth() });
                const data = await res.json();
                this.networkUsers = data.users || [];
                this.externalNodes = data.external_nodes || [];
            } catch (e) { }
            finally { this.loading = false; }
        },
        visitExternalNode(node) {
            if (confirm(`Перейти на вузол ${node.name} (${node.ip})?`)) {
                window.location.href = `http://${node.ip}:8000`;
            }
        },
        async loadChatRooms() {
            try {
                const res = await fetch('/api/network/rooms/', { headers: this.auth() });
                const data = await res.json();
                this.chatRooms = data.results || data;
            } catch (e) { }
        },
        async startDM(targetUser) {
            try {
                const res = await fetch('/api/network/rooms/direct/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ user_id: targetUser.id })
                });
                const room = await res.json();
                this.networkTab = 'chat';
                this.loadChatRooms();
                this.openChat(room);
            } catch (e) { }
        },
        async openChat(room) {
            this.activeChatRoom = room;
            this.messages = [];
            await this.fetchMessages();
            this.scrollToBottom();
            
            if (this.chatPolling) clearInterval(this.chatPolling);
            this.chatPolling = setInterval(() => this.fetchMessages(), 3000);
        },
        async fetchMessages() {
            if (!this.activeChatRoom) return;
            try {
                const res = await fetch(`/api/network/rooms/${this.activeChatRoom.id}/messages/`, { headers: this.auth() });
                const data = await res.json();
                const newMessages = data.results || data;
                if (newMessages.length !== this.messages.length) {
                    this.messages = newMessages;
                    this.scrollToBottom();
                }
            } catch (e) { }
        },
        async sendMessage() {
            if (!this.newMessage.trim() || !this.activeChatRoom) return;
            const text = this.newMessage;
            this.newMessage = '';
            try {
                const res = await fetch(`/api/network/rooms/${this.activeChatRoom.id}/messages/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ text })
                });
                if (res.ok) {
                    this.fetchMessages();
                }
            } catch (e) { }
        },
        getChatPartner(room) {
            if (!room || !room.participants) return {};
            return room.participants.find(p => p.id !== this.user.id) || {};
        },
        scrollToBottom() {
            this.$nextTick(() => {
                const el = this.$refs.chatBody;
                if (el) el.scrollTop = el.scrollHeight;
            });
        }
    }
}
</script>

<style scoped>
.eme-app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--tblr-border-color);
}

.eme-app-title {
    font-size: 1.4rem;
    font-weight: 800;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.eme-chat-container {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 180px);
}

.eme-chat-body {
    flex-grow: 1;
    overflow-y: auto;
    max-height: 400px;
    padding: 16px;
    background: rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
}

.eme-message {
    max-width: 80%;
    margin-bottom: 12px;
    padding: 10px 14px;
    border-radius: 14px;
    font-size: 13px;
    position: relative;
}

.eme-message-out {
    align-self: flex-end !important;
    background: var(--tblr-primary) !important;
    color: white !important;
    border-bottom-right-radius: 2px !important;
}

.eme-message-in {
    align-self: flex-start !important;
    background: var(--tblr-bg-surface-secondary) !important;
    border-bottom-left-radius: 2px !important;
}

.module-placeholder {
    background: var(--tblr-card-bg);
    border: 1px dashed var(--tblr-border-color);
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    color: var(--tblr-secondary);
}
</style>
