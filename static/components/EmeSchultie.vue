<template>
  <div class="eme-app-page">
    <div class="row">
      <div class="col-2" v-for="i in 5" :key="i">
        <div class="card bg-dark border-secondary" @click="onClick(i)">
          <span class="card-body">{{ randomNum }}</span>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-2" v-for="i in 5" :key="i">
        <div class="card bg-dark border-secondary" @click="onClick(i)">
          <span class="card-body">{{ randomNum }}</span>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-2" v-for="i in 5" :key="i">
        <div class="card bg-dark border-secondary" @click="onClick(i)">
          <span class="card-body">{{ randomNum }}</span>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-2" v-for="i in 5" :key="i">
        <div class="card bg-dark border-secondary" @click="onClick(i)">
          <span class="card-body">{{ randomNum }}</span>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col-2" v-for="i in 5" :key="i">
        <div class="card bg-dark border-secondary" @click="onClick(i)">
          <span class="card-body">{{ randomNum }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  props: {
    user: Object,
    auth: Function
  },
  setup(props) {
    const randomNum = ref('')

    const onClick = async (num) => {
      const res = await fetch(`/api/utils/memos/`, { headers: props.auth() })
      const data = await res.json()
      const random = Math.floor(Math.random() * 25) + 1
      if (data.length > 0 && data[data.length - 1].random === random) {
        randomNum.value = 'Correct!'
      } else {
        randomNum.value = `Wrong! Number: ${random}`
      }
    }

    onMounted(() => {
      for (let i = 1; i <= 25; i++) {
        const random = Math.floor(Math.random() * 5) + 1
        for (let j = 1; j <= 5; j++) {
          if (random === j) {
            onClick(i)
          }
        }
      }
    })

    return { randomNum, onClick }
  }
}
</script>

<style scoped>
  .eme-app-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
  }
  .card {
    margin: 10px;
    width: 50px;
    height: 50px;
  }
  .eme-app-title {
    color: var(--eme-accent);
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
  }
</style>