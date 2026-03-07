<template>
    <div class="eme-app-page d-flex flex-column h-100" style="background: #0f111a; color: #e2e8f0;">
        <!-- Header -->
        <div class="eme-app-header border-bottom px-4 py-3 d-flex justify-content-between align-items-center" style="background: rgba(26, 28, 46, 0.8); backdrop-filter: blur(12px);">
            <div class="d-flex align-items-center gap-3">
                <span style="font-size:1.6rem;">🕵️‍♂️</span>
                <h1 class="m-0 fs-3 fw-bold" style="background:linear-gradient(135deg,#ff4b2b,#ff416c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Мафія</h1>
                <span v-if="activeRoom" class="badge bg-secondary ms-2">{{ activeRoom.name }}</span>
            </div>
            <div class="d-flex gap-2">
                <button v-if="activeRoom" class="btn btn-sm btn-outline-danger" @click="leaveRoom">В лоббі</button>
                <button class="btn btn-sm btn-ghost-secondary" @click="$emit('close')">✕</button>
            </div>
        </div>

        <!-- LOBBY -->
        <div v-if="!activeRoom" class="flex-grow-1 p-4 overflow-auto">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Доступні ігри</h2>
                <button class="btn btn-primary" @click="showCreateModal = true">+ Нова гра</button>
            </div>

            <div v-if="loading" class="text-center py-5"><div class="spinner-border text-danger"></div></div>
            
            <div v-else-if="rooms.length === 0" class="text-center text-muted py-5">
                <div class="fs-1 mb-2">📭</div>
                Поки що немає активних кімнат. Створіть першу!
            </div>

            <div v-else class="row g-3">
                <div v-for="room in rooms" :key="room.id" class="col-md-6 col-lg-4">
                    <div class="card bg-dark border-secondary">
                        <div class="card-body">
                            <h5 class="card-title">{{ room.name }}</h5>
                            <p class="text-muted small mb-3">Хост: {{ room.host_username }} | Статус: {{ room.status_display }}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-dark-lt border border-secondary">{{ room.players_count }} / 10 гравців</span>
                                <button class="btn btn-sm btn-outline-danger" @click="joinRoom(room)">Приєднатися</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ACTIVE ROOM -->
        <div v-else class="d-flex flex-grow-1 overflow-hidden">
            <!-- Game Sidebar (Players / Info) -->
            <div class="sidebar border-right d-flex flex-column h-100" style="width: 250px; background: rgba(0,0,0,0.2); border-right: 1px solid rgba(255,255,255,0.05);">
                <div class="p-3 border-bottom border-secondary text-center">
                    <h3 class="fs-5 mb-1">{{ activeRoom.status === 'lobby' ? 'Очікування гравців' : (activeRoom.status === 'finished' ? 'Гру завершено' : (activeRoom.status === 'night' ? `Ніч ${activeRoom.phase_number}` : `День ${activeRoom.phase_number}`)) }}</h3>
                    
                    <div v-if="myPlayer && activeRoom.status !== 'lobby'" class="mt-2 p-2 rounded" style="background: rgba(255,255,255,0.05);">
                        <div class="small text-muted">Ваша роль:</div>
                        <div class="fs-4 fw-bold" :class="roleColor(myPlayer.role)">{{ myPlayer.role_display }}</div>
                    </div>
                </div>

                <div class="flex-grow-1 overflow-auto p-2">
                    <div class="small fw-bold text-muted px-2 py-1 text-uppercase">Учасники ({{ players.length }})</div>
                    <div v-for="p in players" :key="p.id" class="d-flex align-items-center gap-2 p-2 rounded mb-1" :class="{'bg-dark': myPlayer && p.id === myPlayer.id}">
                        <div class="flex-shrink-0" style="width:8px;height:8px;border-radius:50%;" :class="p.is_alive ? 'bg-success' : 'bg-danger'"></div>
                        <div class="flex-grow-1 text-truncate" :class="{'text-decoration-line-through text-muted': !p.is_alive}">
                            {{ p.username }} <span v-if="p.user === activeRoom.host" title="Хост">👑</span>
                        </div>
                        <div v-if="myPlayer && myPlayer.role === 'mafia' && p.role === 'mafia'" class="badge bg-danger-lt px-1" title="Напарник мафії">М</div>
                    </div>
                </div>

                <div v-if="isHost && activeRoom.status === 'lobby'" class="p-3 border-top border-secondary">
                    <button class="btn btn-danger w-100" @click="startGame" :disabled="players.length < 3">
                        Почати гру (потрібно мін. 3)
                    </button>
                </div>
                <!-- Host phase toggle for manual transitions if needed or debugging -->
                <div v-if="isHost && activeRoom.status !== 'lobby' && activeRoom.status !== 'finished'" class="p-3 border-top border-secondary">
                    <button class="btn btn-outline-warning btn-sm w-100" @click="nextPhase">
                        Завершити {{ activeRoom.status === 'night' ? 'Ніч' : 'День' }}
                    </button>
                    <div class="small text-muted text-center mt-1" v-if="activeRoom.human_moderator">Режим: Живий Ведучий</div>
                </div>
            </div>

            <!-- Main Game Area (Chat & Actions) -->
            <div class="flex-grow-1 d-flex flex-column bg-dark h-100 position-relative">
                
                <!-- Night Overlay overlay -->
                <div v-if="activeRoom.status === 'night'" class="position-absolute w-100 h-100 pointer-events-none" style="background: rgba(0, 0, 50, 0.4); z-index: 1;"></div>

                <!-- Chat history -->
                <div class="flex-grow-1 overflow-auto p-4 z-index-2 position-relative" id="mafiaChatBox">
                    <div v-if="activeRoom.status === 'lobby'" class="text-center text-muted mt-5">
                        <div class="fs-1">⏳</div>
                        <h4 class="mt-3">Очікування гравців...</h4>
                        <p>Спілкуйтесь поки збирається компанія.</p>
                    </div>

                    <div v-for="m in messages" :key="m.id" class="mb-3">
                        <!-- System Message -->
                        <div v-if="m.msg_type === 'system'" class="text-center my-3">
                            <span class="badge bg-warning text-dark p-2" style="font-size: 0.9rem;">{{ m.text }}</span>
                        </div>
                        <!-- Mafia Message -->
                        <div v-else-if="m.msg_type === 'mafia'" class="d-flex flex-column align-items-start ms-4">
                            <div class="small text-danger fw-bold">🕴️ {{ m.sender_name }} (Мафія-чат)</div>
                            <div class="p-2 rounded bg-danger text-light" style="max-width: 80%; border: 1px solid #dc3545;">{{ m.text }}</div>
                        </div>
                        <!-- Public Message -->
                        <div v-else class="d-flex flex-column" :class="m.sender === (myPlayer?myPlayer.id:-1) ? 'align-items-end' : 'align-items-start'">
                            <div class="small text-muted">{{ m.sender_name }}</div>
                            <div class="p-2 rounded" :class="m.sender === (myPlayer?myPlayer.id:-1) ? 'bg-primary text-light' : 'bg-secondary text-light'" style="max-width: 80%;">
                                {{ m.text }}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Input & Actions Area -->
                <div class="p-3 border-top border-secondary bg-dark z-index-2 position-relative">
                    
                    <!-- Game Actions Panel (Night/Day voting) -->
                    <div v-if="canTakeAction" class="mb-3 p-3 rounded" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
                        <h5 class="mb-2 text-warning">{{ actionPanelTitle }}</h5>
                        <div class="d-flex gap-2 flex-wrap">
                            <button v-for="p in aliveOtherPlayers" :key="'act'+p.id" 
                                    class="btn" :class="selectedTarget === p.id ? 'btn-danger' : 'btn-outline-danger'" 
                                    @click="selectedTarget = p.id">
                                {{ p.username }}
                            </button>
                        </div>
                        <div class="mt-3 d-flex justify-content-end">
                            <button class="btn btn-sm" :class="selectedTarget ? 'btn-danger' : 'btn-secondary'" :disabled="!selectedTarget" @click="submitAction">
                                Підтвердити вибір
                            </button>
                        </div>
                    </div>
                    
                    <div v-if="activeRoom.status === 'night' && (!myPlayer || !['mafia', 'doctor', 'detective'].includes(myPlayer.role)) && myPlayer.is_alive" class="mb-3 text-center text-muted">
                        Місто засинає. Ви спите і нічого не чуєте... 💤
                    </div>

                    <div v-if="myPlayer && !myPlayer.is_alive" class="mb-3 text-center text-danger">
                        🕯️ Ви мертві. Ви можете спостерігати, але не можете спілкуватись або діяти.
                    </div>

                    <!-- Chat Input -->
                    <div class="d-flex gap-2" v-if="canChat">
                        <select v-if="myPlayer && myPlayer.role === 'mafia' && activeRoom.status === 'night'" v-model="msgType" class="form-select" style="width: auto;">
                            <option value="mafia">Чат Мафії</option>
                            <option value="public" disabled>Публічний (Заблоковано вночі)</option>
                        </select>
                        <input type="text" class="form-control" v-model="myMsg" @keyup.enter="sendChat" placeholder="Ваше повідомлення...">
                        <button class="btn btn-primary" @click="sendChat">Відправити</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Create Room Modal -->
        <div v-if="showCreateModal" class="eme-modal-overlay" @click.self="showCreateModal = false">
            <div class="eme-modal bg-dark border-secondary p-4 rounded" style="width: 400px;">
                <h4 class="mb-3">Нова гра в Мафію</h4>
                <div class="mb-3">
                    <label class="form-label text-muted">Назва кімнати</label>
                    <input type="text" class="form-control" v-model="newRoom.name" placeholder="Чікаго 1930">
                </div>
                <div class="mb-4 form-check">
                    <input type="checkbox" class="form-check-input" id="moderatorCheck" v-model="newRoom.human_moderator">
                    <label class="form-check-label text-muted" for="moderatorCheck">
                        Живий Ведучий <br>
                        <small class="text-secondary">Ви зможете вручну перемикати фази та бачити всі ролі гравців. Інакше сервером все автоматизовано.</small>
                    </label>
                </div>
                <div class="d-flex justify-content-end gap-2">
                    <button class="btn btn-ghost-secondary" @click="showCreateModal = false">Скасувати</button>
                    <button class="btn btn-danger" @click="createRoom">Створити</button>
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
            loading: false,
            rooms: [],
            activeRoom: null,
            players: [],
            messages: [],
            myPlayer: null,
            polling: null,
            showCreateModal: false,
            newRoom: { name: '', human_moderator: false },
            myMsg: '',
            msgType: 'public',
            selectedTarget: null
        };
    },
    computed: {
        isHost() {
            return this.activeRoom && this.activeRoom.host === this.user.id;
        },
        aliveOtherPlayers() {
            if(!this.myPlayer) return [];
            return this.players.filter(p => p.is_alive && p.id !== this.myPlayer.id);
        },
        canChat() {
            if(!this.myPlayer) return false;
            // Ghost can't talk
            if(!this.myPlayer.is_alive) return false;
            // Lobby or Finished or Day = everyone talks
            if(['lobby', 'finished', 'day'].includes(this.activeRoom.status)) {
                this.msgType = 'public';
                return true;
            }
            // Night = only mafia can talk in mafia chat
            if(this.activeRoom.status === 'night' && this.myPlayer.role === 'mafia') {
                this.msgType = 'mafia';
                return true;
            }
            return false;
        },
        canTakeAction() {
            if(!this.myPlayer || !this.myPlayer.is_alive) return false;
            if(this.activeRoom.status === 'day') return this.aliveOtherPlayers.length > 0;
            if(this.activeRoom.status === 'night') {
                return ['mafia', 'doctor', 'detective'].includes(this.myPlayer.role);
            }
            return false;
        },
        actionPanelTitle() {
            if(this.activeRoom.status === 'day') return "Денне голосування (Линч): Кого ви підозрюєте?";
            if(this.myPlayer.role === 'mafia') return "Ніч: Оберіть жертву (всі мафіозі мають обрати одного)";
            if(this.myPlayer.role === 'doctor') return "Ніч: Кого вилікувати?";
            if(this.myPlayer.role === 'detective') return "Ніч: Кого перевірити?";
            return "Оберіть гравця";
        }
    },
    methods: {
        hdrs() { return { 'Content-Type': 'application/json', ...this.auth() }; },
        roleColor(role) {
            const map = {
                'unassigned': 'text-muted',
                'townie': 'text-success',
                'mafia': 'text-danger',
                'doctor': 'text-info',
                'detective': 'text-primary'
            };
            return map[role] || 'text-light';
        },
        scrollToBottom() {
            setTimeout(() => {
                const box = document.getElementById('mafiaChatBox');
                if(box) box.scrollTop = box.scrollHeight;
            }, 100);
        },
        async loadRooms() {
            this.loading = true;
            try {
                const res = await fetch('/api/mafia/rooms/', { headers: this.hdrs() });
                const data = await res.json();
                this.rooms = data.results || data;
            } finally { this.loading = false; }
        },
        async createRoom() {
            if(!this.newRoom.name.trim()) return;
            const res = await fetch('/api/mafia/rooms/', {
                method: 'POST',
                headers: this.hdrs(),
                body: JSON.stringify(this.newRoom)
            });
            if(res.ok) {
                this.showCreateModal = false;
                const r = await res.json();
                this.joinRoom(r);
            }
        },
        async joinRoom(room) {
            await fetch(`/api/mafia/rooms/${room.id}/join/`, { method: 'POST', headers: this.hdrs() });
            this.activeRoom = room;
            this.startPolling();
        },
        leaveRoom() {
            this.stopPolling();
            this.activeRoom = null;
            this.players = [];
            this.messages = [];
            this.myPlayer = null;
            this.loadRooms();
        },
        async syncRoomState() {
            if(!this.activeRoom) return;
            // Fetch players
            const pRes = await fetch(`/api/mafia/players/?room=${this.activeRoom.id}`, { headers: this.hdrs() });
            const pData = await pRes.json();
            this.players = pData.results || pData;
            
            // Identify me
            this.myPlayer = this.players.find(p => p.username === this.user.username) || null;

            // Fetch generic room status
            const rRes = await fetch(`/api/mafia/rooms/${this.activeRoom.id}/`, { headers: this.hdrs() });
            this.activeRoom = await rRes.json();

            // Fetch chat
            const cRes = await fetch(`/api/mafia/messages/?room=${this.activeRoom.id}`, { headers: this.hdrs() });
            const cData = await cRes.json();
            const msgs = cData.results || cData;
            
            if(msgs.length > this.messages.length) {
                this.messages = msgs;
                this.scrollToBottom();
            }
        },
        startPolling() {
            this.syncRoomState();
            this.polling = setInterval(this.syncRoomState, 2000);
        },
        stopPolling() {
            if(this.polling) clearInterval(this.polling);
        },
        async startGame() {
            await fetch(`/api/mafia/rooms/${this.activeRoom.id}/start/`, { method: 'POST', headers: this.hdrs() });
            this.syncRoomState();
        },
        async nextPhase() {
            await fetch(`/api/mafia/rooms/${this.activeRoom.id}/next_phase/`, { method: 'POST', headers: this.hdrs() });
            this.selectedTarget = null;
            this.syncRoomState();
        },
        async sendChat() {
            if(!this.myMsg.trim()) return;
            const text = this.myMsg;
            this.myMsg = '';
            await fetch('/api/mafia/messages/', {
                method: 'POST',
                headers: this.hdrs(),
                body: JSON.stringify({ room: this.activeRoom.id, text: text, msg_type: this.msgType })
            });
            this.syncRoomState();
        },
        async submitAction() {
            if(!this.selectedTarget) return;
            let action_type = '';
            if(this.activeRoom.status === 'day') action_type = 'vote_lynch';
            else if(this.myPlayer.role === 'mafia') action_type = 'vote_kill';
            else if(this.myPlayer.role === 'doctor') action_type = 'heal';
            else if(this.myPlayer.role === 'detective') action_type = 'inspect';

            const res = await fetch(`/api/mafia/rooms/${this.activeRoom.id}/submit_action/`, {
                method: 'POST',
                headers: this.hdrs(),
                body: JSON.stringify({ action_type: action_type, target_id: this.selectedTarget })
            });
            const data = await res.json();
            
            if(!res.ok) alert(data.error);
            else if(data.result) alert(`Результат перевірки комісара: ${data.result}`);
            
            // Just clear target. Action is registered.
            // Visually we could show a "voted" state, but polling next phase resolves it.
            this.selectedTarget = null;
            alert("Дію збережено. Очікування інших...");
        }
    },
    mounted() {
        this.loadRooms();
    },
    unmounted() {
        this.stopPolling();
    }
};
</script>

<style scoped>
.z-index-2 { z-index: 2; }
.pointer-events-none { pointer-events: none; }
</style>
