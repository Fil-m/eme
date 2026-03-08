<template>
  <div class="eme-app-page">

    <eme-app-title>Mini Games</eme-app-title>

    <!-- MENU -->
    <div class="row">
      <button @click="game='clicker'">Clicker</button>
      <button @click="game='ttt'">TicTacToe</button>
      <button @click="game='reaction'">Reaction</button>
      <button @click="game='dice'">Dice</button>
      <button @click="game='guess'">Guess</button>
    </div>

    <!-- CLICKER -->
    <div v-if="game==='clicker'">
      <h3>Clicker</h3>
      <p>Score: {{ score }}</p>
      <button @click="score++">CLICK</button>
      <button @click="score=0">Reset</button>
    </div>

    <!-- TIC TAC TOE -->
    <div v-if="game==='ttt'">
      <h3>Tic Tac Toe</h3>

      <div class="board">
        <button
          v-for="(cell,i) in board"
          :key="i"
          class="cell"
          @click="play(i)"
        >
          {{ cell }}
        </button>
      </div>

      <p>Player: {{ player }}</p>

      <button @click="resetTTT">Reset</button>
    </div>

    <!-- REACTION -->
    <div v-if="game==='reaction'">

      <h3>Reaction Test</h3>

      <button
        class="reaction-box"
        :style="{background: color}"
        @click="reactionClick"
      >
        CLICK
      </button>

      <br>

      <button @click="startReaction">Start</button>

      <p>{{ reactionMessage }}</p>

    </div>

    <!-- DICE -->
    <div v-if="game==='dice'">

      <h3>Dice</h3>

      <p style="font-size:40px">{{ dice }}</p>

      <button @click="rollDice">Roll</button>

    </div>

    <!-- GUESS NUMBER -->
    <div v-if="game==='guess'">

      <h3>Guess Number (1-10)</h3>

      <input v-model="guess">

      <button @click="checkGuess">Guess</button>

      <p>{{ guessMessage }}</p>

    </div>

  </div>
</template>

<script>
import { ref } from "vue"

export default {

props:['user','auth'],

setup(){

const game = ref("clicker")

/* CLICKER */

const score = ref(0)

/* TIC TAC TOE */

const board = ref(["","","","","","","","",""])
const player = ref("X")

const play = (i)=>{
  if(board.value[i] !== "") return
  board.value[i] = player.value
  player.value = player.value === "X" ? "O" : "X"
}

const resetTTT = ()=>{
  board.value = ["","","","","","","","",""]
  player.value = "X"
}

/* REACTION */

const color = ref("red")
const reactionMessage = ref("")
let startTime = 0

const startReaction = ()=>{
  color.value = "red"
  reactionMessage.value = ""

  setTimeout(()=>{
    color.value = "green"
    startTime = Date.now()
  }, Math.random()*3000 + 1000)
}

const reactionClick = ()=>{
  if(color.value === "green"){
    const time = Date.now() - startTime
    reactionMessage.value = "Reaction: " + time + " ms"
    color.value = "red"
  }
}

/* DICE */

const dice = ref(1)

const rollDice = ()=>{
  dice.value = Math.floor(Math.random()*6)+1
}

/* GUESS */

const guess = ref("")
const number = Math.floor(Math.random()*10)+1
const guessMessage = ref("")

const checkGuess = ()=>{
  if(parseInt(guess.value) === number){
    guessMessage.value = "Correct 🎉"
  } else if(parseInt(guess.value) > number){
    guessMessage.value = "Too big"
  } else {
    guessMessage.value = "Too small"
  }
}

return {
  game,
  score,
  board,
  player,
  play,
  resetTTT,
  color,
  startReaction,
  reactionClick,
  reactionMessage,
  dice,
  rollDice,
  guess,
  checkGuess,
  guessMessage
}

}
}
</script>

<style>

button{
margin:5px;
padding:8px 14px;
}

.board{
display:grid;
grid-template-columns:repeat(3,70px);
gap:5px;
margin-top:10px;
}

.cell{
height:70px;
font-size:22px;
}

.reaction-box{
width:120px;
height:120px;
border:none;
color:white;
margin-top:10px;
}

</style>