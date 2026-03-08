<template>
  <div class="eme-app-page">

    <eme-app-title>Mini Games</eme-app-title>

    <div class="row">
      <button @click="game='clicker'">Clicker</button>
      <button @click="game='ttt'">TicTacToe</button>
      <button @click="game='guess'">Guess</button>
    </div>

    <!-- CLICKER -->

    <div v-if="game==='clicker'">
      <h3>Clicker</h3>
      <p>Score: {{ score }}</p>
      <button @click="score++">CLICK</button>
    </div>

    <!-- TIC TAC TOE -->

    <div v-if="game==='ttt'">
      <h3>Tic Tac Toe</h3>

      <div class="board">
        <button v-for="(cell,i) in board"
                :key="i"
                class="cell"
                @click="play(i)">
          {{ cell }}
        </button>
      </div>

      <p>Player: {{ player }}</p>
    </div>

    <!-- GUESS NUMBER -->

    <div v-if="game==='guess'">
      <h3>Guess the Number</h3>

      <input v-model="guess">

      <button @click="checkGuess">Guess</button>

      <p>{{ message }}</p>
    </div>

  </div>
</template>

<script>
import { ref } from "vue"

export default {

  props:['user','auth'],

  setup(){

    const game = ref("clicker")

    // CLICKER
    const score = ref(0)

    // TIC TAC TOE
    const board = ref(["","","","","","","","",""])
    const player = ref("X")

    const play = (i)=>{
      if(board.value[i] !== "") return
      board.value[i] = player.value
      player.value = player.value === "X" ? "O" : "X"
    }

    // GUESS GAME
    const guess = ref("")
    const number = Math.floor(Math.random()*10)+1
    const message = ref("Guess number 1-10")

    const checkGuess = ()=>{
      if(parseInt(guess.value) === number){
        message.value = "Correct 🎉"
      }else{
        message.value = "Try again"
      }
    }

    return {
      game,
      score,
      board,
      player,
      play,
      guess,
      message,
      checkGuess
    }

  }
}
</script>

<style>

.board{
display:grid;
grid-template-columns:repeat(3,60px);
gap:5px;
margin-top:10px;
}

.cell{
height:60px;
font-size:20px;
}

button{
margin:5px;
}

</style>