<template>
  <div
    class="park-adventures-wrapper"
    :class="[backgroundClass, scannerMinimized ? 'park-adventures-wrapper--scanner-minimized' : 'park-adventures-wrapper--scanner-expanded']"
  >
    <div class="container">
      <div class="top_hud">
        <div class="btn_container btn_health player-health">
          <div>{{ player.life }}</div>
        </div>

        <div class="materials">
          <div class="btn_container btn_wood">
            <div>{{ player.wood }}</div>
          </div>
          <div class="btn_container btn_iron">
            <div>{{ player.iron }}</div>
          </div>
          <div class="btn_container btn_gold">
            <div>{{ player.gold }}</div>
          </div>
        </div>

        <div class="btn_container btn_dragon_health dragon-health">
          <div>{{ player.dragon_life }}</div>
        </div>
      </div>

      <!-- Main Interaction Form -->
      <div id="buttons_form">
        <div class="input_wrap">
          <input type="checkbox" id="battle_mode" v-model="battleMode">
          <div class="mode-text">{{ battleMode ? 'Escape Mode' : 'Battle' }}</div>
        </div>
        <br>

        <div
          v-if="player.castle === 0 && !battleMode && backgroundClass !== 'forge_view' && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'"
          class="btn_container btn_build_castle build build1"
        >
          <button @click="doAction('castle')">Build Castle</button>
        </div>

        <div
          v-if="player.forge === 0 && player.castle > 0 && !battleMode && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'"
          class="btn_container btn_build_forge build build2"
        >
          <button @click="doAction('forge')">Build Forge</button>
        </div>

        <div
          v-if="player.magic === 0 && player.forge > 0 && !battleMode && backgroundClass !== 'won_view'"
          class="btn_container btn_build_magic build build3"
        >
          <button @click="doAction('magic')">Build Magic</button>
        </div>

        <div class="right_btns">
          <template v-if="player.forge > 0 || battleMode">
            <div class="btn_container btn_shield">
              <button @click="doMainAction('shield')">Shield</button>
              <p>{{ player.shield }}</p>
            </div>
            <div class="btn_container btn_sword">
              <button @click="doMainAction('sword')">Sword</button>
              <p>{{ player.sword }}</p>
            </div>
          </template>

          <template v-if="player.magic > 0 || battleMode">
            <div class="btn_container btn_magic_shield">
              <button @click="doMainAction('magic_shield')">Magic Shield</button>
              <p>{{ player.magic_shield }}</p>
            </div>
            <div class="btn_container btn_magic_sword">
              <button @click="doMainAction('magic_sword')">Magic Sword</button>
              <p>{{ player.magic_sword }}</p>
            </div>
            <div class="btn_container btn_elixir">
              <button @click="doMainAction('elixir')">Elixir</button>
              <p>{{ player.elixir }}</p>
            </div>
            <div class="btn_container btn_flash">
              <button @click="doMainAction('flash')">Flash</button>
              <p>{{ player.flash }}</p>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div class="bottom_group">
      <div id="messages-container">
        <div id="messages">
          <p>{{ player.log }}</p>
        </div>
      </div>

      <div class="wrap">
        <div class="qr-container-pure">
          <div v-show="!scannerMinimized" class="scanner-summary">
            <div id="qr-result" v-if="lastFound">Found code: {{ lastFound }}</div>
            <div v-else class="scanner-summary__empty">Scanner is live. Tap the camera to collapse it back into the corner.</div>
          </div>

          <div
            class="video-wrapper"
            :class="{
              'video-wrapper--ready': lastFound,
              'video-wrapper--minimized': scannerMinimized,
              'video-wrapper--expanded': !scannerMinimized
            }"
            @click="toggleScannerMode"
          >
            <video ref="qrVideo" playsinline autoplay muted></video>
            <div class="scanner-frame" aria-hidden="true"></div>
            <div class="scanner-status">
              <span v-if="cameraError">{{ cameraError }}</span>
              <span v-else-if="lastFound">QR detected. Use the reward button below.</span>
              <span v-else-if="scannerMinimized">Tap to open scanner.</span>
              <span v-else>Tap again to minimize scanner.</span>
            </div>
            <div class="scanner-zoom-indicator">
              {{ scannerMinimized ? 'Open' : 'Minimize' }}
            </div>
            <canvas ref="qrCanvas" style="display: none;"></canvas>
          </div>

          <div v-show="!scannerMinimized" id="qr_form" class="mt-2 qr-actions">
            <button
              id="send-qrcode"
              type="button"
              @click.stop="scanQR"
              :disabled="loading || !lastFound"
            >
              {{ loading ? 'Processing...' : 'Get your reward!' }}
            </button>

            <button
              type="button"
              class="scanner-secondary"
              @click.stop="resetDetectedCode"
              :disabled="loading || !lastFound"
            >
              Scan again
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
            qrInput: '',
            lastFound: '',
            loading: false,
            isScanning: false,
            scanInterval: null,
            scannerMinimized: true,
            cameraError: '',
            cameraStream: null
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
        }
    },
    methods: {
        toggleScannerMode() {
            this.scannerMinimized = !this.scannerMinimized;
        },
        resetDetectedCode() {
            this.qrInput = '';
            this.lastFound = '';
        },
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
                    alert(error.error || "Error");
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
            if (!this.qrInput.trim() && !this.lastFound.trim()) return;

            const codeToProcess = this.qrInput.trim() || this.lastFound.trim();
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
                    alert("Invalid QR code");
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.resetDetectedCode();
                this.loading = false;
            }
        },
        startCamera() {
            if (this.cameraStream) {
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.cameraError = 'Camera API is not available in this browser.';
                return;
            }

            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
                .then(stream => {
                    const video = this.$refs.qrVideo;
                    if (!video) {
                        stream.getTracks().forEach(track => track.stop());
                        return;
                    }

                    this.cameraStream = stream;
                    video.srcObject = stream;
                    video.setAttribute("playsinline", true);
                    video.play().catch(() => {});
                    this.cameraError = '';

                    if (!this.scanInterval) {
                        this.scanInterval = setInterval(this.processVideoFrame, 500);
                    }
                })
                .catch(err => {
                    this.cameraError = 'Unable to access the camera.';
                    console.error("Camera error:", err);
                });
        },
        stopCamera() {
            const video = this.$refs.qrVideo;

            if (this.scanInterval) {
                clearInterval(this.scanInterval);
                this.scanInterval = null;
            }

            if (video) {
                video.pause();
                video.srcObject = null;
            }

            if (this.cameraStream) {
                this.cameraStream.getTracks().forEach(track => track.stop());
                this.cameraStream = null;
            }

            this.isScanning = false;
        },
        processVideoFrame() {
            const video = this.$refs.qrVideo;
            const canvas = this.$refs.qrCanvas;

            if (this.lastFound !== '') return;
            if (!video || !canvas || !window.jsQR) return;

            if (video.readyState === video.HAVE_ENOUGH_DATA && !this.isScanning) {
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
                    this.qrInput = code.data;
                    if (this.scannerMinimized) {
                        this.scannerMinimized = false;
                    }
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
        this.stopCamera();
    }
}
</script>

<style scoped>
.park-adventures-wrapper {
    --content-width: min(100%, 1180px);
    --stage-center-x: 50%;
    --resource-size: clamp(88px, 9vw, 104px);
    --player-health-size: clamp(212px, 22vw, 248px);
    --status-icon-size: clamp(176px, 18vw, 208px);
    --hud-badge-size: clamp(34px, 3vw, 42px);
    --tool-size: clamp(152px, 15vw, 192px);
    --scanner-mini-width: 112px;
    --scanner-mini-height: 84px;
    --scanner-expanded-max-width: 720px;
    --scanner-corner-offset: clamp(14px, 2vw, 24px);
    --glass-dark: rgba(8, 15, 22, 0.68);
    --glass-border: rgba(255, 255, 255, 0.12);
    position: relative;
    display: flex;
    flex-direction: column;
    gap: clamp(18px, 3vw, 26px);
    padding: clamp(18px, 3vw, 30px);
    width: 100%;
    min-height: calc(100vh - 100px);
    color: white;
    text-shadow: 0 4px 14px rgba(5, 5, 5, 0.72);
    font-family: sans-serif;
    background: url(/static/images/background.png);
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    border-radius: 12px;
    overflow: hidden;
}

.park-adventures-wrapper--scanner-expanded {
    --stage-center-y: clamp(132px, 20vh, 190px);
    --build-width: clamp(232px, 24vw, 280px);
}

.park-adventures-wrapper--scanner-minimized {
    --stage-center-y: clamp(176px, 24vh, 236px);
    --build-width: clamp(286px, 29vw, 344px);
}

.park-adventures-wrapper.fight_view {
    background: url(/static/images/fight_bcgrd.png) !important;
    background-size: cover !important;
    background-attachment: fixed !important;
    background-position: center !important;
}

.park-adventures-wrapper.castle_view {
    background: url(/static/images/castle.png);
    background-size: cover;
    background-attachment: fixed;
}

.park-adventures-wrapper.forge_view {
    background: url(/static/images/forge_view.png);
    background-size: cover;
    background-attachment: fixed;
    background-position: left;
}

.park-adventures-wrapper.magic_view {
    background: url(/static/images/magic_view.png);
    background-size: cover;
    background-attachment: fixed;
    background-position: left;
}

.park-adventures-wrapper.won_view {
    background: url(/static/images/won.jpg);
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}

.container {
    width: var(--content-width);
    margin: 0 auto;
    position: relative;
    flex: 1 1 auto;
    min-height: clamp(500px, 62vh, 660px);
}

.top_hud {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    display: block;
    padding: 0;
    z-index: 6;
}

.materials {
    position: static;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: clamp(14px, 2vw, 22px);
    width: max-content;
    margin: 0 auto;
}

.mode-text {
    font-size: clamp(18px, 2vw, 28px);
}

#buttons_form {
    position: relative;
    width: 100%;
    min-height: clamp(500px, 62vh, 660px);
    margin-top: clamp(156px, 19vh, 214px);
}

#buttons_form button {
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    border: none;
    background: transparent;
}

#send-qrcode {
    margin-top: 0;
    padding: 12px 16px;
    min-height: 46px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, #4ca528, #78d54d);
    color: white;
    text-shadow: none;
    box-shadow: 0 10px 22px rgba(21, 61, 5, 0.34);
    font-size: 16px;
    font-weight: 700;
}

#qr-result {
    font-size: 16px;
    line-height: 1.3;
    color: #ecffd9;
}

.btn_container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 150px;
    height: 150px;
    background-repeat: no-repeat;
    background-size: cover;
    background-position: center;
}

.btn_container p {
    margin: 0;
}

.btn_shield { background-image: url(/static/images/shield.png); }
.btn_sword { background-image: url(/static/images/sword.png); }
.btn_magic_shield { background-image: url(/static/images/magic_shield.png); }
.btn_magic_sword { background-image: url(/static/images/magic_sword.png); }
.btn_elixir { background-image: url(/static/images/elixir.png); background-size: auto; }
.btn_flash { background-image: url(/static/images/flash.png); }
.btn_build_castle { background-image: url(/static/images/build_castle.png); }
.btn_build_forge { background-image: url(/static/images/build_forge.png); }
.btn_build_magic { background-image: url(/static/images/build_magic.png); }
.btn_wood { background-image: url(/static/images/wood.png); }
.btn_iron { background-image: url(/static/images/iron.png); }
.btn_gold { background-image: url(/static/images/gold.png); }
.btn_dragon_health { background-image: url(/static/images/dragon_health.png); }

.btn_health {
    background-image: url(/static/images/health.png);
}

.materials .btn_container {
    width: var(--resource-size);
    height: var(--resource-size);
    align-items: flex-start;
    justify-content: flex-end;
    padding: 4px;
    background-size: contain;
}

.btn_container.btn_health,
.btn_container.btn_dragon_health {
    align-items: flex-start;
    justify-content: flex-end;
    padding: 4px;
    background-size: contain;
}

.top_hud .btn_container > div {
    min-width: var(--hud-badge-size);
    height: var(--hud-badge-size);
    padding: 0 11px;
    display: grid;
    place-items: center;
    border-radius: 999px;
    background: rgba(8, 16, 24, 0.82);
    border: 1px solid rgba(255, 255, 255, 0.12);
    font-size: clamp(18px, 2vw, 24px);
    font-weight: 700;
    line-height: 1;
}

.btn_container.btn_health.player-health {
    position: absolute;
    top: -6px;
    left: -112px;
    width: var(--player-health-size);
    height: var(--player-health-size);
    margin-top: 0;
    background-size: 180% auto;
    background-position: center;
}

.btn_container.btn_dragon_health.dragon-health {
    position: absolute;
    top: 0;
    right: 0;
    width: var(--status-icon-size);
    height: var(--status-icon-size);
    margin-top: 0;
    background-size: contain;
    background-position: right top;
}

input[type="checkbox"] {
    appearance: auto !important;
    -webkit-appearance: checkbox !important;
    width: 24px;
    height: 24px;
    margin-right: 0;
    background: white;
}

.input_wrap {
    position: absolute;
    top: 0;
    right: clamp(24px, 5vw, 72px);
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 18px;
    background: var(--glass-dark);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(14px);
    z-index: 6;
}

.wrap {
    width: 100%;
}

.park-adventures-wrapper--scanner-minimized .wrap {
    position: static;
    width: var(--scanner-mini-width);
    height: var(--scanner-mini-height);
    margin-top: 2px;
    flex: 0 0 auto;
}

.park-adventures-wrapper--scanner-expanded .wrap {
    position: static;
    width: 100%;
    height: auto;
}

.build {
    position: absolute;
    left: var(--stage-center-x);
    top: var(--stage-center-y);
    transform: translateX(-50%);
    width: var(--build-width);
    height: calc(var(--build-width) * 0.78);
    padding: 0;
    font-size: 0;
    background-size: contain;
    background-position: center bottom;
    filter: drop-shadow(0 18px 22px rgba(0, 0, 0, 0.28));
    transition: top 0.24s ease, width 0.24s ease, height 0.24s ease, transform 0.24s ease, filter 0.24s ease;
    z-index: 4;
}

.build1,
.build2,
.build3 {
    left: var(--stage-center-x);
    top: var(--stage-center-y);
}

.right_btns {
    position: absolute;
    top: calc(var(--stage-center-y) + 18px);
    right: clamp(56px, 8vw, 128px);
    width: min(420px, 38vw);
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px;
    justify-items: end;
    z-index: 5;
}

.park-adventures-wrapper.fight_view .right_btns {
    position: absolute;
    top: 72px;
    right: -34px;
    width: 96px;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    z-index: 5;
}

.right_btns .btn_container {
    width: var(--tool-size);
    height: var(--tool-size);
    align-items: flex-end;
    justify-content: flex-end;
    padding: 6px;
    background-size: contain;
}

.park-adventures-wrapper.fight_view .right_btns .btn_container {
    width: 96px;
    height: 96px;
    padding: 4px;
    background-size: contain;
    background-position: right center;
}

.right_btns .btn_container p {
    font-size: clamp(18px, 1.9vw, 24px);
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(6, 12, 18, 0.78);
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.park-adventures-wrapper.fight_view .right_btns .btn_container p {
    font-size: 14px;
    padding: 3px 6px;
}

.bottom_group {
    width: var(--content-width);
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
}

.park-adventures-wrapper--scanner-minimized .bottom_group {
    position: absolute;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    width: var(--content-width);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
}

.park-adventures-wrapper--scanner-expanded .bottom_group {
    position: static;
    transform: none;
}

.pure-input {
    background: #f1efef;
    border: none;
    border-radius: 10px;
    font-size: 30px;
    padding: 10px 20px;
    color: #333;
    outline: none;
    width: 60%;
    box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.2);
}

.pure-input:focus {
    outline: none;
}

.qr-container-pure {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    width: 100%;
    max-width: 100%;
}

.park-adventures-wrapper--scanner-minimized .qr-container-pure {
    width: var(--scanner-mini-width);
    min-height: var(--scanner-mini-height);
    max-width: var(--scanner-mini-width);
    gap: 0;
}

.park-adventures-wrapper--scanner-expanded .qr-container-pure {
    width: min(100%, var(--scanner-expanded-max-width));
    min-height: 0;
    max-width: 100%;
}

.scanner-summary {
    width: 100%;
    padding: 12px 14px;
    background: var(--glass-dark);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    backdrop-filter: blur(10px);
}

.scanner-summary__empty {
    font-size: 14px;
    line-height: 1.4;
    color: rgba(255, 255, 255, 0.82);
}

.qr-actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    width: min(100%, var(--scanner-expanded-max-width));
}

.qr-actions button {
    margin-top: 0;
    min-height: 46px;
    padding: 12px 14px;
    font-size: 16px;
    font-weight: 700;
}

#send-qrcode:disabled,
.scanner-secondary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

.scanner-secondary {
    border: none;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.12);
    color: #fff;
}

#messages-container {
    width: 100%;
    min-height: 92px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.4);
    border-radius: 20px;
    padding: 16px 20px;
    white-space: pre-wrap;
    background: rgba(228, 230, 211, 0.92);
    box-shadow: 0 18px 40px rgba(2, 11, 19, 0.16);
}

#messages {
    color: #417c21;
    font-size: clamp(18px, 1.8vw, 28px);
    line-height: 1.45;
    display: flex;
    align-items: center;
    text-shadow: none;
}

#messages p {
    margin: 0;
    padding: 0;
}

.video-wrapper {
    position: relative;
    width: min(100%, var(--scanner-expanded-max-width));
    min-height: 280px;
    overflow: hidden;
    border-radius: 20px;
    background:
        radial-gradient(circle at top, rgba(76, 165, 40, 0.18), transparent 45%),
        linear-gradient(180deg, rgba(4, 8, 11, 0.96), rgba(17, 27, 21, 0.98));
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
    cursor: zoom-in;
    user-select: none;
    transition:
        width 0.24s ease,
        min-height 0.24s ease,
        box-shadow 0.24s ease,
        border-radius 0.24s ease,
        opacity 0.24s ease,
        left 0.24s ease,
        right 0.24s ease,
        bottom 0.24s ease;
}

.video-wrapper video {
    display: block;
    width: 100%;
    aspect-ratio: 4 / 3;
    object-fit: cover;
}

.video-wrapper--expanded {
    position: relative;
    width: min(100%, var(--scanner-expanded-max-width));
    min-height: 280px;
    z-index: 2;
}

.video-wrapper--minimized {
    position: relative;
    left: auto;
    right: auto;
    bottom: auto;
    width: var(--scanner-mini-width);
    height: var(--scanner-mini-height);
    min-height: var(--scanner-mini-height);
    max-width: var(--scanner-mini-width);
    max-height: var(--scanner-mini-height);
    border-radius: 8px;
    z-index: 8;
    cursor: zoom-in;
    background: rgba(5, 10, 16, 0.32);
    border: none;
    box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18);
    overflow: hidden;
    display: block;
}

.video-wrapper--minimized video {
    width: 100%;
    height: 100%;
    aspect-ratio: auto;
    object-fit: cover;
    border-radius: 8px;
}

.video-wrapper--ready {
    box-shadow:
        inset 0 0 0 1px rgba(143, 255, 121, 0.35),
        0 0 0 2px rgba(143, 255, 121, 0.18);
}

.scanner-frame {
    position: absolute;
    inset: 18% 17%;
    border: 3px solid rgba(255, 255, 255, 0.85);
    border-radius: 22px;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
    pointer-events: none;
}

.scanner-status {
    position: absolute;
    left: 16px;
    right: 16px;
    bottom: 16px;
    padding: 12px 14px;
    font-size: 16px;
    line-height: 1.4;
    color: #eff8f3;
    background: rgba(0, 0, 0, 0.56);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    backdrop-filter: blur(10px);
}

.scanner-zoom-indicator {
    position: absolute;
    top: 12px;
    right: 12px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #eff8f3;
    background: rgba(0, 0, 0, 0.56);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 999px;
}

.video-wrapper--minimized .scanner-frame {
    display: none;
}

.video-wrapper--minimized .scanner-status {
    display: none;
}

.video-wrapper--minimized .scanner-zoom-indicator {
    display: none;
}

@media (max-width: 992px) {
    .park-adventures-wrapper {
        --resource-size: 70px;
        --player-health-size: 150px;
        --status-icon-size: 120px;
        --hud-badge-size: 28px;
        --tool-size: 128px;
        --scanner-mini-width: 96px;
        --scanner-mini-height: 72px;
        --scanner-corner-offset: 12px;
        gap: 14px;
        padding: 12px;
    }

    .container {
        min-height: 400px;
    }

    .top_hud {
        width: 100%;
        padding: 0;
    }

    .materials {
        gap: 8px;
    }

    .top_hud .btn_container > div {
        padding: 0 8px;
        font-size: 14px;
    }

    .input_wrap {
        top: 0;
        right: 18px;
        gap: 8px;
        padding: 8px 10px;
    }

    .mode-text {
        font-size: 16px;
    }

    input[type="checkbox"] {
        width: 20px;
        height: 20px;
    }

    #buttons_form {
        min-height: 360px;
        margin-top: 128px;
    }

    .btn_container.btn_health.player-health {
        top: -4px;
        left: -68px;
        margin-top: 0;
    }

    .btn_container.btn_dragon_health.dragon-health {
        top: 0;
        right: 0;
        margin-top: 0;
    }

    .right_btns {
        top: calc(var(--stage-center-y) + 38px);
        right: 20px;
        width: 244px;
        gap: 12px;
    }

    .park-adventures-wrapper.fight_view .right_btns {
        top: 60px;
        right: -24px;
        width: 96px;
        gap: 10px;
    }

    .right_btns .btn_container {
        width: var(--tool-size);
        height: var(--tool-size);
        padding: 4px;
    }

    .park-adventures-wrapper.fight_view .right_btns .btn_container {
        width: 96px;
        height: 96px;
        padding: 4px;
    }

    .right_btns .btn_container p {
        font-size: 13px;
        padding: 3px 6px;
    }

    .bottom_group {
        gap: 12px;
    }

    .park-adventures-wrapper--scanner-minimized .bottom_group {
        bottom: 12px;
    }

    #messages-container {
        min-height: 72px;
        padding: 12px 14px;
        border-radius: 16px;
    }

    #messages {
        font-size: 15px;
    }

    .scanner-summary {
        padding: 10px 12px;
    }

    .scanner-summary__empty {
        font-size: 13px;
    }

    .qr-actions {
        grid-template-columns: 1fr;
        width: 100%;
    }

    .video-wrapper {
        width: 100%;
        min-height: 240px;
        border-radius: 16px;
    }

    .video-wrapper--expanded {
        width: 100%;
    }

    .video-wrapper--minimized {
        width: var(--scanner-mini-width);
        height: var(--scanner-mini-height);
        min-height: var(--scanner-mini-height);
        max-width: var(--scanner-mini-width);
        max-height: var(--scanner-mini-height);
        border-radius: 8px;
    }

    .scanner-frame {
        inset: 16%;
        border-radius: 18px;
    }

    .scanner-status {
        left: 10px;
        right: 10px;
        bottom: 10px;
        font-size: 13px;
        padding: 10px 12px;
    }

    .video-wrapper--minimized .scanner-status {
        display: none;
    }

    .scanner-zoom-indicator {
        top: 10px;
        right: 10px;
        font-size: 11px;
        padding: 7px 9px;
    }

    .video-wrapper--minimized .scanner-zoom-indicator {
        display: none;
    }
}
</style>
