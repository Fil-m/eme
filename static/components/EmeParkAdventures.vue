<template>
  <div class="park-adventures-wrapper" :class="[backgroundClass, {'park-adventures-wrapper--scanner-expanded': scannerExpanded, 'park-adventures-wrapper--scanner-minimized': !scannerExpanded}]">
    <div class="container">
      
      <!-- Top HUD -->
      <div class="top_hud d-flex justify-content-between align-items-start">
        <!-- Materials -->
        <div class="materials d-flex gap-3">
          <div class="btn_container btn_wood" title="Wood">
            <div class="hud-badge">{{ player.wood }}</div>
          </div>
          <div class="btn_container btn_iron" title="Iron">
            <div class="hud-badge">{{ player.iron }}</div>
          </div>
          <div class="btn_container btn_gold" title="Gold">
            <div class="hud-badge">{{ player.gold }}</div>
          </div>
        </div>

        <!-- Mode Toggle -->
        <div class="input_wrap glass-card">
          <label class="form-check form-switch m-0 d-flex align-items-center gap-2">
            <input class="form-check-input" type="checkbox" v-model="battleMode">
            <span class="mode-text small fw-bold">{{ battleMode ? 'ESCAPE' : 'BATTLE' }}</span>
          </label>
        </div>
      </div>

      <!-- Health Indicators -->
      <div class="health-system">
        <div class="btn_container btn_health player-health" :style="{ '--hp': player.life + '%' }">
          <div class="hp-label">{{ player.life }}</div>
        </div>
        <div class="btn_container btn_dragon_health dragon-health" :style="{ '--hp': player.dragon_life + '%' }">
          <div class="hp-label">{{ player.dragon_life }}</div>
        </div>
      </div>

      <!-- Main Stage -->
      <div id="buttons_form">
        <!-- Construction -->
        <div class="construction-zone">
            <div class="btn_container btn_build_castle build build1" v-if="player.castle === 0 && !battleMode && backgroundClass !== 'forge_view' && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'">
              <button class="btn-action" @click="doAction('castle')">Build Castle</button>
            </div>
            <div class="btn_container btn_build_forge build build2" v-if="player.forge === 0 && player.castle > 0 && !battleMode && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'">
              <button class="btn-action" @click="doAction('forge')">Build Forge</button>
            </div>
            <div class="btn_container btn_build_magic build build3" v-if="player.magic === 0 && player.forge > 0 && !battleMode && backgroundClass !== 'won_view'">
              <button class="btn-action" @click="doAction('magic')">Build Magic</button>
            </div>
        </div>

        <!-- Arsenal -->
        <div class="right_btns glass-panel" v-if="player.forge > 0 || battleMode">
            <div class="btn_container btn_shield">
              <button class="btn-tool" @click="doMainAction('shield')"></button>
              <p class="tool-count">{{ player.shield }}</p>
            </div>
            <div class="btn_container btn_sword">
              <button class="btn-tool" @click="doMainAction('sword')"></button>
              <p class="tool-count">{{ player.sword }}</p>
            </div>
            
            <template v-if="player.magic > 0 || battleMode">
                <div class="btn_container btn_magic_shield">
                  <button class="btn-tool" @click="doMainAction('magic_shield')"></button>
                  <p class="tool-count">{{ player.magic_shield }}</p>
                </div>
                <div class="btn_container btn_magic_sword">
                  <button class="btn-tool" @click="doMainAction('magic_sword')"></button>
                  <p class="tool-count">{{ player.magic_sword }}</p>
                </div>
                <div class="btn_container btn_elixir">
                  <button class="btn-tool" @click="doMainAction('elixir')"></button>
                  <p class="tool-count">{{ player.elixir }}</p>
                </div>
                <div class="btn_container btn_flash">
                  <button class="btn-tool" @click="doMainAction('flash')"></button>
                  <p class="tool-count">{{ player.flash }}</p>
                </div>
            </template>
        </div>
      </div>
    </div> <!-- end container -->

    <!-- Bottom HUD -->
    <div class="bottom_group d-flex flex-column align-items-center gap-3 p-3">
      <!-- Activity Log -->
      <div id="messages-container" class="w-100">
        <div id="messages">
          <p>{{ player.log || 'Добро ласкаво в парк!' }}</p>
        </div>
      </div>

      <!-- Scanner Area -->
      <div class="qr-section w-100 d-flex justify-content-center">
        <div class="qr-container-pure glass-card w-100" style="max-width: 600px;">
          
          <!-- Video Container -->
          <div class="video-container-static">
               <div class="video-wrapper-static w-100" :class="{'video-wrapper--ready': lastFound, 'video-wrapper--error': cameraError}" style="height: 350px;">
                 <video ref="qrVideo" playsinline autoplay muted style="width: 100%; height: 100%; object-fit: cover;"></video>
                 <canvas ref="qrCanvas" style="display: none;"></canvas>
                 <div class="scanner-frame-overlay"></div>
                 
                 <!-- Loading Overlay if not ready -->
                 <div v-if="!cameraActive && !lastFound && !cameraError" class="scanner-loading-overlay d-flex flex-column align-items-center justify-content-center">
                    <div class="spinner-border text-primary mb-3" role="status"></div>
                    <p class="small text-white mb-2">Ініціалізація камери...</p>
                    <button class="btn btn-xs btn-outline-light opacity-50" @click="startCamera">Перезавантажити камеру</button>
                 </div>

                 <!-- Error Overlay -->
                 <div v-if="cameraError" class="scanner-error-overlay p-4 d-flex flex-column align-items-center justify-content-center text-center">
                    <div class="mb-3" style="font-size: 40px;">⚠️</div>
                    <div class="h6 text-danger mb-2">Помилка камери</div>
                    <div class="small text-white opacity-75 mb-3">{{ cameraError }}</div>
                    <div class="d-flex gap-2">
                       <button class="btn btn-sm btn-outline-light" @click="startCamera">Спробувати знову</button>
                       <a v-if="!isSecure" :href="httpsUrl" class="btn btn-sm btn-warning">HTTPS версія</a>
                    </div>
                 </div>
               </div>
          </div>

          <!-- Status -->
          <div id="qr-result" class="scanner-status-text mt-3 mb-2 text-center" v-if="lastFound">
             <div class="fw-bold text-success h5">✅ Знайдено: {{ lastFound }}</div>
          </div>
          <div v-else class="scanner-status-text mt-3 mb-2 opacity-75 text-center">
             Наведіть камеру на QR-код ресурсу
          </div>

          <!-- Action -->
          <div class="qr-actions mt-2">
             <button id="send-qrcode" class="btn btn-primary w-100 py-3 fw-bold" @click="scanQR" :disabled="loading || !lastFound">
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                Отримати ресурс!
             </button>
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
            player: {
                wood: 0, iron: 0, gold: 0,
                castle: 0, forge: 0, magic: 0,
                life: 100, dragon_life: 100,
                shield: 0, magic_shield: 0, sword: 0, magic_sword: 0,
                elixir: 0, flash: 0, log: ''
            },
            battleMode: false,
            lastFound: '',
            loading: false,
            isScanning: false,
            scanInterval: null,
            cameraSupported: true,
            cameraActive: false,
            cameraError: ''
        }
    },
    computed: {
        backgroundClass() {
            if (this.player.dragon_life <= 0) return 'won_view';
            if (this.battleMode) return 'fight_view';
            if (this.player.magic > 0) return 'magic_view';
            if (this.player.forge > 0) return 'forge_view';
            if (this.player.castle > 0) return 'castle_view';
            return '';
        },
        isSecure() {
            return window.isSecureContext;
        },
        httpsUrl() {
            return window.location.href.replace('http://', 'https://');
        }
    },
    methods: {
        async fetchStatus() {
            try {
                const res = await fetch('/api/game/status/', { headers: this.auth() });
                if (res.ok) {
                    this.player = await res.json();
                }
            } catch (e) {
                console.error("Game error:", e);
            }
        },
        async doAction(actionName) {
            this.loading = true;
            try {
                const res = await fetch('/api/game/action/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ action: actionName, battle_mode: false })
                });
                
                if (res.ok) {
                    this.player = await res.json();
                } else {
                    const error = await res.json();
                    alert(error.error || "Помилка");
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },
        async doMainAction(actionName) {
            this.loading = true;
            try {
                const res = await fetch('/api/game/action/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ action: actionName, battle_mode: this.battleMode })
                });
                if (res.ok) {
                    this.player = await res.json();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },
        async scanQR() {
            if (!this.lastFound.trim()) return;
            const codeToProcess = this.lastFound.trim();
            this.loading = true;
            try {
                const res = await fetch('/api/game/qr/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...this.auth() },
                    body: JSON.stringify({ resource_input: codeToProcess })
                });
                
                if (res.ok || res.status === 429) {
                    this.player = await res.json();
                } else {
                    alert("Недійсний код!");
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.lastFound = '';
                this.loading = false;
            }
        },
        startCamera() {
            this.cameraError = '';
            this.cameraActive = false;
            if (!this.isSecure) {
                this.cameraError = "Для доступу до камери необхідне безпечне з'єднання (HTTPS).";
                this.cameraSupported = false;
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.cameraError = "Браузер не підтримує доступ до камери.";
                this.cameraSupported = false;
                return;
            }

            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    const video = this.$refs.qrVideo;
                    if (video) {
                        video.srcObject = stream;
                        video.setAttribute("playsinline", true);
                        video.play();
                        this.cameraActive = true; // Set active immediately on stream start
                        if (this.scanInterval) clearInterval(this.scanInterval);
                        this.scanInterval = setInterval(this.processVideoFrame, 500);
                    }
                })
                .catch(err => {
                    console.error("Camera error:", err);
                    this.cameraSupported = false;
                    if (err.name === 'NotAllowedError') {
                        this.cameraError = "Доступ до камери заборонено користувачем.";
                    } else if (err.name === 'NotFoundError') {
                        this.cameraError = "Камеру не знайдено на пристрої.";
                    } else {
                        this.cameraError = "Не вдалося відкрити камеру: " + err.message;
                    }
                });
        },
        processVideoFrame() {
            const video = this.$refs.qrVideo;
            const canvas = this.$refs.qrCanvas;
            if (this.lastFound !== '') return;
            if (!video || !canvas || !window.jsQR) return;

            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                this.cameraActive = true;
                if (this.isScanning) return;
                
                this.isScanning = true;
                const ctx = canvas.getContext('2d', { willReadFrequently: true });
                canvas.height = video.videoHeight;
                canvas.width = video.videoWidth;
                
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                
                const code = window.jsQR(imageData.data, canvas.width, canvas.height, {
                    inversionAttempts: "dontInvert"
                });

                if (code && code.data && code.data.trim() !== '') {
                    this.lastFound = code.data;
                }
                this.isScanning = false;
            }
        }
    },
    mounted() {
        this.fetchStatus();
        this.startCamera();
    },
    beforeUnmount() {
        const video = this.$refs.qrVideo;
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        if (this.scanInterval) clearInterval(this.scanInterval);
    }
}
</script>

<style scoped>
.park-adventures-wrapper {
    --resource-size: 150px;
    --player-health-size: 260px;
    --status-icon-size: 220px;
    --hud-badge-size: 42px;
    --tool-size: 190px;
    --scanner-mini-width: 140px;
    --scanner-mini-height: 105px;
    --scanner-expanded-max-width: 800px;
    --glass-dark: rgba(2, 8, 14, 0.72);
    --glass-border: rgba(255, 255, 255, 0.12);
    --eme-green: #4ca528;

    position: relative;
    width: 100%;
    min-height: calc(100vh - 100px);
    color: white;
    font-family: 'Inter', sans-serif;
    background: url(/static/images/background.png) center/cover no-repeat fixed;
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.park-adventures-wrapper.fight_view { background-image: url(/static/images/fight_bcgrd.png); }
.park-adventures-wrapper.castle_view { background-image: url(/static/images/castle.png); }
.park-adventures-wrapper.forge_view { background-image: url(/static/images/forge_view.png); }
.park-adventures-wrapper.magic_view { background-image: url(/static/images/magic_view.png); }
.park-adventures-wrapper.won_view { background-image: url(/static/images/won.jpg); }

.container {
    padding: 24px;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

/* TOP HUD */
.top_hud { z-index: 10; }

.btn_container {
    background-repeat: no-repeat;
    background-size: contain;
    background-position: center;
    position: relative;
}

.materials .btn_container { width: var(--resource-size); height: var(--resource-size); }
.btn_wood { background-image: url(/static/images/wood.png); }
.btn_iron { background-image: url(/static/images/iron.png); }
.btn_gold { background-image: url(/static/images/gold.png); }

.hud-badge {
    position: absolute;
    bottom: 20%;
    right: 15%;
    min-width: var(--hud-badge-size);
    height: var(--hud-badge-size);
    background: #000;
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 18px;
    border: 2px solid var(--eme-green);
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.glass-card {
    background: var(--glass-dark);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 12px 16px;
}

.form-check-input:checked { background-color: #ff3e3e; border-color: #ff3e3e; }

/* HEALTH SYSTEM */
.health-system {
    position: relative;
    height: 0;
    z-index: 5;
}

.player-health {
    position: absolute;
    top: 40px;
    left: -100px;
    width: var(--player-health-size);
    height: var(--player-health-size);
    background-image: url(/static/images/health.png);
}

.dragon-health {
    position: absolute;
    top: 40px;
    right: 0;
    width: var(--status-icon-size);
    height: var(--status-icon-size);
    background-image: url(/static/images/dragon_health.png);
}

.hp-label {
    position: absolute;
    bottom: 10%;
    width: 100%;
    text-align: center;
    font-size: 24px;
    font-weight: 900;
    color: white;
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
}

/* MAIN STAGE */
#buttons_form {
    flex-grow: 1;
    display: flex;
    justify-content: center;
    align-items: center;
}

.construction-zone {
    position: relative;
    width: 300px;
    height: 300px;
}

.btn-action {
    width: 100%;
    height: 100%;
    opacity: 0;
    cursor: pointer;
}

.btn_build_castle { width: 300px; height: 300px; background-image: url(/static/images/build_castle.png); }
.btn_build_forge { width: 300px; height: 300px; background-image: url(/static/images/build_forge.png); }
.btn_build_magic { width: 300px; height: 300px; background-image: url(/static/images/build_magic.png); }

.right_btns {
    position: fixed;
    right: 40px;
    top: 50%;
    transform: translateY(-50%);
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    padding: 24px;
    border-radius: 32px;
}

.btn-tool {
    width: 100%;
    height: 100%;
    background: transparent;
    border: none;
    cursor: pointer;
}

.right_btns .btn_container { width: var(--tool-size); height: var(--tool-size); }
.btn_shield { background-image: url(/static/images/shield.png); }
.btn_sword { background-image: url(/static/images/sword.png); }
.btn_magic_shield { background-image: url(/static/images/magic_shield.png); }
.btn_magic_sword { background-image: url(/static/images/magic_sword.png); }
.btn_elixir { background-image: url(/static/images/elixir.png); background-size: 60%; }
.btn_flash { background-image: url(/static/images/flash.png); }

.tool-count {
    position: absolute;
    top: 0;
    right: 0;
    background: #000;
    padding: 4px 10px;
    border-radius: 99px;
    font-weight: 800;
    font-size: 14px;
    border: 1px solid var(--eme-green);
}

/* BOTTOM HUD */
.bottom_group { z-index: 20; }

#messages-container {
    background: rgba(228, 230, 211, 0.9);
    border-radius: 16px;
    padding: 12px 20px;
    min-height: 80px;
    display: flex;
    align-items: center;
    color: #417c21;
    font-weight: 700;
    font-size: 18px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.video-wrapper-static {
    width: 100%;
    max-width: 600px;
    height: 350px;
    background: #000;
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    border: 2px solid var(--glass-border);
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}

.video-wrapper-static video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.video-wrapper--ready {
    border-color: var(--eme-green);
    box-shadow: 0 0 15px rgba(76, 165, 40, 0.4);
}

.scanner-frame-overlay {
    position: absolute;
    inset: 20%;
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 8px;
    pointer-events: none;
}

.scanner-loading-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 5;
}

.scanner-error-overlay {
    position: absolute;
    inset: 0;
    background: rgba(20, 5, 5, 0.9);
    z-index: 10;
}

.video-wrapper--error {
    border-color: #ff3e3e;
    box-shadow: 0 0 15px rgba(255, 62, 62, 0.4);
}

.btn-xs {
    padding: 2px 8px;
    font-size: 12px;
}

@media (max-width: 992px) {
    .video-wrapper-static {
        height: 250px;
    }
    .player-health { left: -60px; scale: 0.7; }
    .dragon-health { right: -20px; scale: 0.7; }
    .right_btns { right: 10px; padding: 10px; scale: 0.8; }
    .hud-badge { scale: 0.8; }
}
</style>
