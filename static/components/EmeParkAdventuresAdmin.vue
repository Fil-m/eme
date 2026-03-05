<template>
  <div class="p-3">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="m-0 text-white">
        <span class="fs-2 me-2">🛡️</span> Панель Модератора: Park Adventures
      </h2>
      <button class="btn btn-primary" @click="fetchPlayers" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        Оновити дані
      </button>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div class="card bg-dark text-white border-secondary">
      <div class="table-responsive">
        <table class="table table-vcenter table-dark card-table table-striped">
          <thead>
            <tr>
              <th>Гравець</th>
              <th>Здоров'я Дракона</th>
              <th>Здоров'я Гравця</th>
              <th>Ресурси (🪵 / ⛓️ / 🪙)</th>
              <th>Інвентар</th>
              <th>Будівлі</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="players.length === 0 && !loading">
              <td colspan="6" class="text-center py-4 text-muted">Гравців не знайдено</td>
            </tr>
            <tr v-for="p in players" :key="p.id">
              <td>
                <div class="d-flex align-items-center">
                  <span class="avatar avatar-sm me-2 bg-primary text-white">{{ p.username.substring(0,2).toUpperCase() }}</span>
                  <div class="font-weight-medium">{{ p.username }}</div>
                </div>
              </td>
              <td>
                <div class="d-flex align-items-center">
                  <span class="me-2">{{ p.dragon_life }}</span>
                  <div class="progress progress-sm w-100">
                    <div class="progress-bar bg-danger" :style="{width: p.dragon_life + '%'}"></div>
                  </div>
                </div>
              </td>
              <td>
                <div class="d-flex align-items-center">
                  <span class="me-2">{{ p.life }}</span>
                  <div class="progress progress-sm w-100">
                    <div class="progress-bar bg-success" :style="{width: p.life + '%'}"></div>
                  </div>
                </div>
              </td>
              <td>
                <span class="badge bg-secondary me-1" title="Дерево">🪵 {{ p.wood }}</span>
                <span class="badge bg-secondary me-1" title="Залізо">⛓️ {{ p.iron }}</span>
                <span class="badge bg-secondary" title="Золото">🪙 {{ p.gold }}</span>
              </td>
              <td>
                <div class="d-flex flex-wrap gap-1">
                  <span v-if="p.shield > 0" class="badge bg-dark border border-secondary" title="Щит">🛡️ {{p.shield}}</span>
                  <span v-if="p.sword > 0" class="badge bg-dark border border-secondary" title="Меч">🗡️ {{p.sword}}</span>
                  <span v-if="p.magic_shield > 0" class="badge bg-primary" title="Чарівний Щит">🛡️✨ {{p.magic_shield}}</span>
                  <span v-if="p.magic_sword > 0" class="badge bg-primary" title="Чарівний Меч">🗡️✨ {{p.magic_sword}}</span>
                  <span v-if="p.elixir > 0" class="badge bg-warning text-dark" title="Еліксир">🧪 {{p.elixir}}</span>
                  <span v-if="p.flash > 0" class="badge bg-danger" title="Спалах">💥 {{p.flash}}</span>
                  <span v-if="p.shield==0 && p.sword==0 && p.magic_shield==0 && p.magic_sword==0 && p.elixir==0 && p.flash==0" class="text-muted small">Пусто</span>
                </div>
              </td>
              <td>
                <span v-if="p.castle > 0" class="badge bg-success me-1">🏰 Замок</span>
                <span v-if="p.forge > 0" class="badge bg-success me-1">⚒️ Кузня</span>
                <span v-if="p.magic > 0" class="badge bg-success">🔮 Магія</span>
                <span v-if="p.castle==0" class="text-muted small">Немає</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
    props: ['user', 'auth'],
    data() {
        return {
            players: [],
            loading: false,
            error: null,
            pollInterval: null
        }
    },
    methods: {
        async fetchPlayers() {
            this.loading = true;
            this.error = null;
            try {
                const res = await fetch('/api/game/admin/players/', { headers: this.auth() });
                if (res.ok) {
                    this.players = await res.json();
                } else if (res.status === 403) {
                    this.error = "У вас немає доступу Адміністратора/Модератора до цієї сторінки.";
                } else {
                    this.error = "Помилка завантаження даних.";
                }
            } catch (e) {
                console.error("Admin fetch error:", e);
                this.error = "Помилка мережі.";
            } finally {
                this.loading = false;
            }
        }
    },
    mounted() {
        this.fetchPlayers();
        // Auto-refresh every 10 seconds while the page is open
        this.pollInterval = setInterval(this.fetchPlayers, 10000);
    },
    beforeUnmount() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
    }
}
</script>
