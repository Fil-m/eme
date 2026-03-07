<template>
    <div class="eme-scroll-container">
        <div class="container-fluid py-4 min-vh-100">
            <header class="mb-4">
                <div class="d-flex align-items-center gap-3">
                    <div class="header-icon-box">🧰</div>
                    <div>
                        <h1 class="page-title m-0">Утиліти (OmniTools)</h1>
                        <p class="text-muted m-0">Набір локальних інструментів для розробника (CyberChef / IT-Tools)</p>
                    </div>
                </div>
            </header>

            <div class="row g-4">
                <!-- Sidebar Selection -->
                <div class="col-md-3">
                    <div class="tools-sidebar">
                        <div class="tool-btn" :class="{active: activeTool === 'json'}" @click="activeTool = 'json'">
                            <span class="fs-4 me-2">{}</span> JSON Formatter
                        </div>
                        <div class="tool-btn" :class="{active: activeTool === 'base64'}" @click="activeTool = 'base64'">
                            <span class="fs-4 me-2">🔐</span> Base64 Encode/Decode
                        </div>
                        <div class="tool-btn" :class="{active: activeTool === 'uuid'}" @click="activeTool = 'uuid'">
                            <span class="fs-4 me-2">🆔</span> UUID Generator
                        </div>
                        <div class="tool-btn" :class="{active: activeTool === 'hash'}" @click="activeTool = 'hash'">
                            <span class="fs-4 me-2">#️⃣</span> Hash Calculator
                        </div>
                    </div>
                </div>

                <!-- Main Tool Area -->
                <div class="col-md-9">
                    <div class="tool-work-area card h-100">
                        
                        <!-- JSON FORMATTER -->
                        <div v-if="activeTool === 'json'" class="tool-content">
                            <h3>JSON Formatter</h3>
                            <textarea v-model="jsonInput" placeholder="Вставте JSON тут..." class="eme-textarea mt-3"></textarea>
                            <div class="d-flex gap-2 my-3">
                                <button class="btn btn-primary" @click="formatJson">Форматувати</button>
                                <button class="btn btn-outline-secondary" @click="minifyJson">Мінімізувати</button>
                                <button class="btn btn-outline-danger" @click="jsonInput=''; jsonOutput=''">Очистити</button>
                            </div>
                            <div v-if="jsonError" class="alert alert-danger">{{ jsonError }}</div>
                            <textarea v-model="jsonOutput" readonly placeholder="Результат..." class="eme-textarea output-area"></textarea>
                        </div>

                        <!-- BASE64 -->
                        <div v-if="activeTool === 'base64'" class="tool-content">
                            <h3>Base64 Encode / Decode</h3>
                            <textarea v-model="b64Input" placeholder="Текст або Base64..." class="eme-textarea mt-3"></textarea>
                            <div class="d-flex gap-2 my-3">
                                <button class="btn btn-primary" @click="b64Encode">Кодувати (Encode)</button>
                                <button class="btn btn-secondary" @click="b64Decode">Декодувати (Decode)</button>
                            </div>
                            <div v-if="b64Error" class="alert alert-danger">{{ b64Error }}</div>
                            <textarea v-model="b64Output" readonly placeholder="Результат..." class="eme-textarea output-area"></textarea>
                        </div>

                        <!-- UUID GENERATOR -->
                        <div v-if="activeTool === 'uuid'" class="tool-content">
                            <h3>UUID v4 Generator</h3>
                            <div class="d-flex align-items-center gap-3 mt-4">
                                <input type="number" v-model.number="uuidCount" min="1" max="100" class="form-control bg-dark text-white border-secondary" style="width: 100px">
                                <button class="btn btn-primary" @click="generateUuids">Генерувати</button>
                            </div>
                            <textarea v-model="uuidOutput" readonly class="eme-textarea output-area mt-4" style="height: 300px; font-family: monospace;"></textarea>
                        </div>

                        <!-- HASH CALCULATOR -->
                        <div v-if="activeTool === 'hash'" class="tool-content">
                            <h3>Hash Calculator (SHA-256)</h3>
                            <p class="text-muted">Для розрахунку хешів у браузері використовується Web Crypto API.</p>
                            <textarea v-model="hashInput" placeholder="Введіть текст..." class="eme-textarea mt-3" @input="calculateHash"></textarea>
                            <div class="mt-4 p-3 bg-dark rounded border border-secondary" style="font-family: monospace; word-break: break-all;">
                                <strong>SHA-256:</strong> <br>
                                <span class="text-primary">{{ hashOutput || '...' }}</span>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            activeTool: 'json',
            // JSON vars
            jsonInput: '',
            jsonOutput: '',
            jsonError: '',
            // Base64 vars
            b64Input: '',
            b64Output: '',
            b64Error: '',
            // UUID vars
            uuidCount: 5,
            uuidOutput: '',
            // Hash vars
            hashInput: '',
            hashOutput: ''
        }
    },
    methods: {
        formatJson() {
            this.jsonError = '';
            try {
                const obj = JSON.parse(this.jsonInput);
                this.jsonOutput = JSON.stringify(obj, null, 4);
            } catch (e) {
                this.jsonError = 'Помилка парсингу: ' + e.message;
            }
        },
        minifyJson() {
            this.jsonError = '';
            try {
                const obj = JSON.parse(this.jsonInput);
                this.jsonOutput = JSON.stringify(obj);
            } catch (e) {
                this.jsonError = 'Помилка парсингу: ' + e.message;
            }
        },
        b64Encode() {
            this.b64Error = '';
            try {
                // btoa handles ascii, encodeURIComponent fixes unicode issues for btoa
                this.b64Output = btoa(encodeURIComponent(this.b64Input).replace(/%([0-9A-F]{2})/g,
                    function toSolidBytes(match, p1) {
                        return String.fromCharCode('0x' + p1);
                    }));
            } catch (e) {
                this.b64Error = e.message;
            }
        },
        b64Decode() {
            this.b64Error = '';
            try {
                this.b64Output = decodeURIComponent(atob(this.b64Input).split('').map(function(c) {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join(''));
            } catch (e) {
                this.b64Error = 'Некоректний Base64 рядок.';
            }
        },
        generateUuids() {
            let res = [];
            for(let i = 0; i < this.uuidCount; i++){
                // crypto.randomUUID() available in secure contexts (localhost/https)
                if (window.crypto && crypto.randomUUID) {
                    res.push(crypto.randomUUID());
                } else {
                    // Fallback
                    res.push('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                        return v.toString(16);
                    }));
                }
            }
            this.uuidOutput = res.join('\n');
        },
        async calculateHash() {
            if (!this.hashInput) {
                this.hashOutput = '';
                return;
            }
            try {
                const msgUint8 = new TextEncoder().encode(this.hashInput);
                const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
                this.hashOutput = hashHex;
            } catch(e) {
                this.hashOutput = 'Помилка криптографії в браузері';
            }
        }
    }
}
</script>

<style scoped>
.page-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: white;
}

.header-icon-box {
    width: 50px;
    height: 50px;
    background: var(--eme-grad);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
}

.tools-sidebar {
    background: rgba(26, 28, 46, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.tool-btn {
    padding: 15px;
    border-radius: 12px;
    cursor: pointer;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.6);
    transition: all 0.2s;
    display: flex;
    align-items: center;
}

.tool-btn:hover {
    background: rgba(255, 255, 255, 0.05);
    color: white;
}

.tool-btn.active {
    background: rgba(0, 229, 255, 0.1);
    color: var(--eme-accent);
}

.tool-work-area {
    background: rgba(26, 28, 46, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 30px;
}

.tool-content h3 {
    margin-bottom: 20px;
    font-weight: 800;
    color: white;
}

.eme-textarea {
    width: 100%;
    min-height: 200px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 15px;
    color: #e1e1e1;
    font-family: monospace;
    resize: vertical;
}

.eme-textarea:focus {
    outline: none;
    border-color: var(--eme-accent);
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
}

.output-area {
    background: rgba(0, 0, 0, 0.5);
    color: #00ff88;
}
</style>
