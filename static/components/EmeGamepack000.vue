<template>
  <div class="eme-app-page">
    <eme-app-title>Mini Games</eme-app-title>

    <!-- MENU -->
    <div v-if="game === 'menu'">
      <h3>Choose game</h3>

      <button @click="startGuess">Guess Number</button>
      <button @click="startClicker">Clicker</button>
      <button @click="startRPS">Rock Paper Scissors</button>
    </div>

    <!-- GUESS NUMBER -->
    <div v-if="game === 'guess'">
      <h3>Guess number (1‑100)</h3>

      <input v-model="guessInput" @keydown.enter="checkGuess">
      <button @click="checkGuess">Try</button>

      <p>{{ guessMessage }}</p>

      <button @click="goMenu">Menu</button>
    </div>

    <!-- CLICKER -->
    <div v-if="game === 'clicker'">
      <h3>Clicker</h3>

      <p>Score: {{ score }}</p>
      <p v-if="timeLeft>0">Time: {{ timeLeft }}</p>

      <button @click="click">CLICK</button>
      <button @click="startTimer">Start 10s</button>

      <button @click="goMenu">Menu</button>
    </div>

    <!-- ROCK PAPER SCISSORS -->
    <div v-if="game === 'rps'">
      <h3>Rock Paper Scissors</h3>

      <button @click="play('rock')">Rock</button>
      <button @click="play('paper')">Paper</button>
      <button @click="play('scissors')">Scissors</button>

      <p>Your: {{ playerChoice }}</p>
      <p>Computer: {{ computerChoice }}</p>
      <p>{{ rpsResult }}</p>

      <button @click="goMenu">Menu</button>
    </div>

  </div>
</template>

<script>
import { ref } from "vue"

export default {
  props: ['user','auth'],

  setup(){

    const game = ref("menu")
    const goMenu = () => game.value = "menu"

    // GUESS GAME
    const secret = ref(0)
    const guessInput = ref("")
    const guessMessage = ref("")

    const startGuess = () => {
      secret.value = Math.floor(Math.random()*100)+1
      guessInput.value = ""
      guessMessage.value = ""
      game.value = "guess"
    }

    const checkGuess = () => {
      const num = Number(guessInput.value)

      if(num > secret.value) guessMessage.value = "Less"
      else if(num < secret.value) guessMessage.value = "More"
      else guessMessage.value = "You win!"
    }

    // CLICKER
    const score = ref(0)
    const timeLeft = ref(0)

    const startClicker = () => {
      score.value = 0
      timeLeft.value = 0
      game.value = "clicker"
    }

    const click = () => {
      if(timeLeft.value > 0) score.value++
    }

    const startTimer = () => {
      timeLeft.value = 10

      const timer = setInterval(()=>{
        timeLeft.value--

        if(timeLeft.value <= 0){
          clearInterval(timer)
        }
      },1000)
    }

    // ROCK PAPER SCISSORS
    const playerChoice = ref("")
    const computerChoice = ref("")
    const rpsResult = ref("")

    const startRPS = () => {
      playerChoice.value = ""
      computerChoice.value = ""
      rpsResult.value = ""
      game.value = "rps"
    }

    const play = (choice) => {

      const options = ["rock","paper","scissors"]
      const comp = options[Math.floor(Math.random()*3)]

      playerChoice.value = choice
      computerChoice.value = comp

      if(choice === comp) rpsResult.value = "Draw"
      else if(
        (choice==="rock" && comp==="scissors") ||
        (choice==="paper" && comp==="rock") ||
        (choice==="scissors" && comp==="paper")
      ) rpsResult.value = "You win"
      else rpsResult.value = "Computer wins"
    }

    return {
      game,
      goMenu,

      startGuess,
      guessInput,
      guessMessage,
      checkGuess,

      startClicker,
      score,
      timeLeft,
      click,
      startTimer,

      startRPS,
      playerChoice,
      computerChoice,
      rpsResult,
      play
    }

  }
}
</script>