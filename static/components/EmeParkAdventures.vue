<template>
  <div class="park-adventures-wrapper" :class="backgroundClass">
    <div class="container">
      
      <!-- Materials Row -->
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

      <!-- Right Group: Health -->
      <div class="right_group">
        <div class="btn_container btn_health">
          <div>{{ player.life }}</div>
        </div>
        <div class="btn_container btn_dragon_health">
          <div>{{ player.dragon_life }}</div>
        </div>
      </div>

      <!-- Main Interaction Form (div instead of form + prevent default) -->
      <div id="buttons_form">
        
        <!-- Toggle Battle Mode -->
        <div class="input_wrap">
          <input type="checkbox" id="battle_mode" v-model="battleMode">
          <div class="mode-text">{{ battleMode ? 'Escape Mode' : 'Battle' }}</div>
        </div>
        <br>

        <!-- Big Buildings Buttons -->
        <div class="btn_container btn_build_castle build build1" v-if="player.castle === 0 && !battleMode && backgroundClass !== 'forge_view' && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'">
          <button @click="doAction('castle')">Build Castle</button>
        </div>
        
        <div class="btn_container btn_build_forge build build2" v-if="player.forge === 0 && player.castle > 0 && !battleMode && backgroundClass !== 'magic_view' && backgroundClass !== 'won_view'">
          <button @click="doAction('forge')">Build Forge</button>
        </div>
        
        <div class="btn_container btn_build_magic build build3" v-if="player.magic === 0 && player.forge > 0 && !battleMode && backgroundClass !== 'won_view'">
          <button @click="doAction('magic')">Build Magic</button>
        </div>

        <!-- Right Side Buttons: Crafting / Items -->
        <div class="right_btns">
          <!-- Shown if in Forge or higher OR in Battle mode -->
          <template v-if="player.forge > 0 || battleMode">
            <div class="btn_container btn_shield">
              <button @click="doMainAction('shield')">Shield</button> <p>{{ player.shield }}</p>
            </div>
            <div class="btn_container btn_sword">
              <button @click="doMainAction('sword')">Sword</button> <p>{{ player.sword }}</p>
            </div>
          </template>

          <!-- Shown if in Magic or higher OR in Battle mode -->
          <template v-if="player.magic > 0 || battleMode">
            <div class="btn_container btn_magic_shield">
              <button @click="doMainAction('magic_shield')">Magic Shield</button> <p>{{ player.magic_shield }}</p>
            </div>
            <div class="btn_container btn_magic_sword">
              <button @click="doMainAction('magic_sword')">Magic Sword</button> <p>{{ player.magic_sword }}</p>
            </div>
            <div class="btn_container btn_elixir">
              <button @click="doMainAction('elixir')">Elixir</button> <p>{{ player.elixir }}</p>
            </div>
            <div class="btn_container btn_flash">
              <button @click="doMainAction('flash')">Flash</button> <p>{{ player.flash }}</p>
            </div>
          </template>
        </div>

      </div> <!-- end buttons_form -->
    </div> <!-- end container -->

    <!-- Bottom Group: Logs and QR -->
    <div class="bottom_group">
      <!-- Logs -->
      <div id="messages-container">
        <div id="messages">
          <p>{{ player.log }}</p>
        </div>
      </div>

      <!-- QR Reader / Resource input -->
      <div class="wrap">
        <div class="qr-container-pure">
          <div id="qr-result" v-if="lastFound">Щойно знайдено: {{ lastFound }}</div>
          <div id="qr_form" class="mt-2 d-flex align-items-center">
            <button id="send-qrcode" @click="scanQR" :disabled="loading" style="cursor: pointer;">Get your reward!</button>
          </div>
          
          <div class="mt-3 video-wrapper" v-if="cameraSupported">
            <video ref="qrVideo" playsinline autoplay muted></video>
            <canvas ref="qrCanvas" style="display: none;"></canvas>
          </div>
          <div v-else class="mt-3 text-center p-3 border rounded bg-dark-lt" style="background: rgba(0,0,0,0.4); border: 1px dashed #4ca528 !important;">
            <p class="small mb-2" style="font-size: 14px; text-shadow: none;">📷 Камера заблокована браузером (потрібно HTTPS).<br>Використовуйте фото для сканування:</p>
            <label class="btn btn-success d-inline-block p-2" style="background: #4ca528; border: none; border-radius: 8px; cursor: pointer;">
                <span>📂 Обрати фото QR</span>
                <input type="file" accept="image/*" capture="environment" @change="onFileScan" style="display: none;">
            </label>
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
            cameraSupported: true
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
            if (!this.qrInput.trim() && !this.lastFound.trim()) return;
            // If they clicked the button but the input is empty, fallback to lastFound
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
                    alert("Недійсний код!");
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.qrInput = '';
                this.lastFound = '';
                this.loading = false;
            }
        },
        startCamera() {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn("MediaDevices not supported");
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
                        
                        // Run scanner around 2 times a second (500ms) to prevent CPU overload
                        this.scanInterval = setInterval(this.processVideoFrame, 500);
                    }
                })
                .catch(err => {
                    console.error("Camera error:", err);
                    this.cameraSupported = false;
                });
        },
        onFileScan(e) {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);
                    
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const code = window.jsQR(imageData.data, canvas.width, canvas.height);
                    
                    if (code && code.data) {
                        this.lastFound = code.data;
                        this.qrInput = code.data;
                        this.player.log = "✅ QR-код розпізнано з фото! Натисніть кнопку отримання нагороди.";
                    } else {
                        alert("Не вдалося знайти QR-код на цьому зображенні.");
                    }
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        },
        processVideoFrame() {
            const video = this.$refs.qrVideo;
            const canvas = this.$refs.qrCanvas;
            
            // Do not scan if we already found a code and are waiting for user click
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
                    // Update UI but require manual click to collect
                    this.lastFound = code.data;
                    this.qrInput = code.data;
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
        // Stop camera stream when leaving the page
        const video = this.$refs.qrVideo;
        if (video && video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
        }
    }
}
</script>

<style scoped>
/* Scoping all original Park Adventures styles to .park-adventures-wrapper */

.park-adventures-wrapper {
    position: relative;
    width: 100%;
    min-height: calc(100vh - 100px);
    color: white;
    text-shadow: 4px 10px 15px #050505;
    font-family: sans-serif;
    
    /* Default Background */
    background: url(/static/images/background.png);
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    border-radius: 12px;
    overflow: hidden;
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
    width: 90%;
    margin: 0 auto;
    position: relative;
    height: 100%;
}

.materials {
    display: flex;
    justify-content: center;
    font-size: 50px;
    padding-top: 20px;
}

.right_group, .mode-text {
    font-size: 50px;
}

#buttons_form {
    display: flex;
    flex-direction: column;
    width: 100%;
    align-items: flex-end;
    justify-content: space-around;
    margin-top: 80px;
}

#buttons_form button,
#send-qrcode {
    font-size: 50px;
    margin-top: 30px;
}

#send-qrcode {
    padding: 20px;
    border-radius: 10px;
    border: none;
    background-color: #4ca528;
    color: white;
    text-shadow: 4px 10px 15px #050505;
}

#qr-result {
    font-size: 40px;
}

#buttons_form button {
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
}

#buttons_form .build button {
    opacity: 0;
}

.btn_container {
    display: flex;
    align-items: baseline;
    justify-content: space-around;
    width: 150px;
    height: 150px;
    background-repeat: no-repeat;
    background-size: cover;
    background-position: center;
}

.btn_container p {
    font-size: 40px;
    margin-left: 10px;
    position: relative;
    left: 40px;
}

/* Icons */
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
    width: 130px;
    height: 130px;
    background-size: auto;
}

.btn_container.btn_health {
    position: absolute;
    top: 30px;
}

.btn_container.btn_dragon_health {
    position: absolute;
    top: 30px;
    right: 30px;
}

input[type="checkbox"] {
    appearance: auto !important;
    -webkit-appearance: checkbox !important;
    width: 50px;
    height: 50px;
    margin-right: 20px;
    background: white;
}

.input_wrap {
    display: flex;
    align-items: center;
}

.wrap {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
    align-items: center;
}

.build {
    position: absolute;
    bottom: 250px;
    width: 20%;
    padding: 20px;
    font-size: 40px;
    z-index: 100;
}

.build1, .build2, .build3 {
    left: calc(50% - 93px);
}

.right_btns {
    margin-right: 50px;
}

.btn_elixir button { margin-right: 30px; }
.btn_flash button { margin-right: 15px; }

.bottom_group {
    position: absolute;
    bottom: 20px;
    width: 90%;
    left: 5%;
}

/* Pure non-bootstrap overrides */
.pure-input {
    background: #f1efef;
    border: none;
    border-radius: 10px;
    font-size: 30px;
    padding: 10px 20px;
    color: #333;
    outline: none;
    width: 60%;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.2);
}

.pure-input:focus {
    outline: none;
}

.qr-container-pure {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

#messages-container {
    position: relative;
    margin: 0 auto;
    height: 100px;
    overflow-y: auto;
    border: none;
    border-radius: 10px;
    padding: 5px;
    white-space: pre-wrap;
    background-color: #e4e6d3;
}

#messages {
    position: absolute;
    top: 0;
    width: 100%;
    height: 100%;
    color: #417c21;
    z-index: 9999;
    font-size: 40px;
    padding-left: 20px;
    display: flex;
    align-items: center;
    text-shadow: 4px 10px 15px #f1eaea;
}

#messages p {
    margin: 0;
    padding: 0;
}

/* 
=================================================== 
MOBILE ADAPTATIONS
=================================================== 
*/
@media (max-width: 992px) {
    /* Scale down all massive text sizes and margins */
    .materials { font-size: 24px; }
    .right_group, .mode-text { font-size: 24px; }
    
    #buttons_form button, #send-qrcode {
        font-size: 16px;
        margin-top: 5px;
        padding: 8px 15px;
    }
    
    #qr-result { font-size: 18px; color: #4ca528; background: rgba(0,0,0,0.5); padding: 5px 10px; border-radius: 8px;}
    
    .btn_container {
        width: 60px;
        height: 60px;
    }
    
    .btn_health {
        width: 80px;
        height: 80px;
    }
    
    .btn_container p {
        font-size: 18px;
        margin-left: 2px;
        left: unset;
    }

    /* Message log adaptations */
    #messages-container {
        height: 60px;
    }
    #messages {
        font-size: 16px;
        padding-left: 10px;
        text-shadow: 1px 1px 2px #f1eaea;
    }
    
    input[type="checkbox"] {
        width: 25px;
        height: 25px;
        margin-right: 10px;
    }

    .input_wrap {
        position: absolute;
        top: 140px;
        right: 10px;
        z-index: 100;
    }

    .build {
        font-size: 20px;
        width: 150px;
        top: 35%;
        bottom: auto;
        z-index: 100;
    }
    
    .build1, .build2, .build3 {
        left: calc(50% - 30px);
    }
    
    .right_btns {
        margin-right: 10px;
    }
    
    .btn_container.btn_health, .btn_container.btn_dragon_health {
        position: relative;
        top: 0;
        right: 0;
    }
    .right_group {
        display: flex;
        justify-content: flex-end;
        gap: 20px;
        margin-top: 10px;
        margin-right: 20px;
    }

    /* Form input & Video */
    .pure-input {
        font-size: 16px !important;
        width: 150px;
        padding: 8px 12px;
    }
    
    .video-wrapper {
        margin-top: 5px !important;
    }

    .video-wrapper video {
        width: 100%;
        max-width: 400px;
        height: auto;
        border-radius: 8px;
        border: none;
    }
    
    #buttons_form {
        margin-top: 20px;
    }
}
</style>
