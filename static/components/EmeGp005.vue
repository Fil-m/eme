<template>
  <div class="eme-app-page">

    <eme-app-title>Mini Games</eme-app-title>

    <!-- MENU -->
    <div class="row">
      <button @click="game='snake'">Snake</button>
      <button @click="game='clicker'">Clicker</button>
      <button @click="game='dice'">Dice</button>
    </div>

    <!-- SNAKE -->
    <div v-if="game==='snake'">

      <h3>Snake 🐍</h3>

      <canvas ref="canvas" width="400" height="400"></canvas>

      <p>Score: {{ snakeScore }}</p>

      <button @click="startSnake">Start</button>

    </div>

    <!-- CLICKER -->
    <div v-if="game==='clicker'">

      <h3>Clicker</h3>

      <p>Score: {{ score }}</p>

      <button @click="score++">CLICK</button>

      <button @click="score=0">Reset</button>

    </div>

    <!-- DICE -->
    <div v-if="game==='dice'">

      <h3>Dice</h3>

      <p style="font-size:40px">{{ dice }}</p>

      <button @click="rollDice">Roll</button>

    </div>

  </div>
</template>

<script>
import { ref, onMounted } from "vue"

export default {

props:['user','auth'],

setup(){

const game = ref("snake")

/* CLICKER */

const score = ref(0)

/* DICE */

const dice = ref(1)

const rollDice = ()=>{
  dice.value = Math.floor(Math.random()*6)+1
}

/* SNAKE */

const canvas = ref(null)
const snakeScore = ref(0)

let ctx
let snake
let food
let dx
let dy
let grid = 20

const startSnake = ()=>{

snakeScore.value = 0

snake = [{x:200,y:200}]
food = {x:100,y:100}

dx = grid
dy = 0

setInterval(gameLoop,120)

}

const gameLoop = ()=>{

if(!ctx) return

ctx.clearRect(0,0,400,400)

const head = {
x: snake[0].x + dx,
y: snake[0].y + dy
}

snake.unshift(head)

if(head.x === food.x && head.y === food.y){

snakeScore.value++

food = {
x: Math.floor(Math.random()*20)*grid,
y: Math.floor(Math.random()*20)*grid
}

}else{

snake.pop()

}

ctx.fillStyle = "red"
ctx.fillRect(food.x,food.y,20,20)

ctx.fillStyle = "green"

snake.forEach(part=>{
ctx.fillRect(part.x,part.y,20,20)
})

}

onMounted(()=>{

ctx = canvas.value.getContext("2d")

window.addEventListener("keydown",(e)=>{

if(e.key==="ArrowUp"){dx=0;dy=-grid}
if(e.key==="ArrowDown"){dx=0;dy=grid}
if(e.key==="ArrowLeft"){dx=-grid;dy=0}
if(e.key==="ArrowRight"){dx=grid;dy=0}

})

})

return{
game,
score,
dice,
rollDice,
canvas,
startSnake,
snakeScore
}

}

}
</script>

<style>

button{
margin:5px;
padding:8px 14px;
}

canvas{
border:2px solid black;
margin-top:10px;
}

</style>