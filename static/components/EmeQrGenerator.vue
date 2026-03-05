<template>
    <div class="eme-app-page p-4">
        <div class="d-flex align-items-center mb-4">
            <span style="font-size:2rem; margin-right: 15px;">🔍</span>
            <h1 class="m-0" style="color: #00e5ff;">QR Генератор</h1>
            <button class="btn btn-sm btn-ghost-secondary ms-auto" @click="$emit('close')">✕</button>
        </div>

        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow-sm" style="background: var(--tblr-card-bg); border: 1px solid var(--tblr-border-color); border-radius: 16px;">
                    <div class="card-body p-4 text-center">
                        <div class="mb-4">
                            <label class="form-label text-start" style="color: #94a3b8;">Текст або посилання для коду</label>
                            <textarea 
                                class="form-control" 
                                v-model="text" 
                                rows="3" 
                                placeholder="Введіть що завгодно..."
                                style="background: rgba(255,255,255,0.05); color: white; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"
                            ></textarea>
                        </div>

                        <div class="qr-preview-container mb-4 d-flex justify-content-center align-items-center" style="min-height: 220px; background: rgba(0,0,0,0.2); border-radius: 12px; border: 1px dashed rgba(0,229,255,0.2);">
                            <div v-show="text" ref="qrcode" class="p-3 bg-white rounded"></div>
                            <div v-if="!text" class="text-muted small">Введіть текст, щоб побачити код</div>
                        </div>

                        <div class="d-grid gap-2">
                            <button class="btn btn-primary" :disabled="!text" @click="downloadQR">
                                📥 Завантажити код на телефон
                            </button>
                            <button class="btn btn-ghost-secondary btn-sm" @click="text = ''">Очистити</button>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 p-3 rounded" style="background: rgba(0,229,255,0.05); border: 1px solid rgba(0,229,255,0.1);">
                    <div class="small text-muted">
                        💡 <strong>Порада:</strong> Цей код генерується миттєво і не зберігається на сервері. Ви можете використовувати його для передачі посилань, паролів Wi-Fi або контактів.
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
// Ми використовуємо CDN версію для надійності в SFC лоудері
const QR_SCRIPT_URL = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';

export default {
    props: ['user', 'auth'],
    emits: ['close'],
    data() {
        return {
            text: '',
            qrInstance: null
        };
    },
    watch: {
        text() {
            this.generateQR();
        }
    },
    methods: {
        async loadLibrary() {
            if (window.QRCode) return;
            return new Promise((resolve) => {
                const script = document.createElement('script');
                script.src = QR_SCRIPT_URL;
                script.onload = resolve;
                document.head.appendChild(script);
            });
        },
        async generateQR() {
            await this.loadLibrary();
            if (!this.text) return;

            // Очищуємо попередній код
            this.$refs.qrcode.innerHTML = '';
            
            this.qrInstance = new QRCode(this.$refs.qrcode, {
                text: this.text,
                width: 200,
                height: 200,
                colorDark : "#000000",
                colorLight : "#ffffff",
                correctLevel : QRCode.CorrectLevel.H
            });
        },
        downloadQR() {
            const img = this.$refs.qrcode.querySelector('img');
            if (!img) return;
            
            const link = document.createElement('a');
            link.href = img.src;
            link.download = `qr_code_${Date.now()}.png`;
            link.click();
        }
    },
    mounted() {
        this.loadLibrary();
    }
}
</script>

<style scoped>
.form-control:focus {
    background: rgba(255,255,255,0.08);
    border-color: #00e5ff;
    box-shadow: 0 0 0 0.25rem rgba(0, 229, 255, 0.1);
}
</style>
