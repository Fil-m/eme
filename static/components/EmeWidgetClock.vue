<template>
    <div class="widget-card clock-widget">
        <div class="time">{{ time }}</div>
        <div class="date">{{ date }}</div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            timer: null,
            time: '',
            date: ''
        }
    },
    mounted() {
        this.updateTime();
        this.timer = setInterval(this.updateTime, 1000);
    },
    unmounted() {
        clearInterval(this.timer);
    },
    methods: {
        updateTime() {
            const now = new Date();
            this.time = now.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
            this.date = now.toLocaleDateString('uk-UA', { weekday: 'long', month: 'long', day: 'numeric' });
        }
    }
}
</script>

<style scoped>
.widget-card {
    background: rgba(26, 28, 46, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 20px;
    height: 100%;
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    transition: transform 0.3s ease;
}

.widget-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 229, 255, 0.3);
}

.time {
    font-size: 3.5rem;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -1px;
    background: var(--eme-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.date {
    font-size: 1rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 8px;
    text-transform: capitalize;
}
</style>
