<template>
<div class="eme-app-page">

<eme-app-title>Mini Arcade</eme-app-title>

<!-- MENU -->
<div v-if="game==='menu'">

<h3>Choose Game</h3>

<button @click="startSnake">Snake</button>
<button @click="startRPS">Rock Paper Scissors</button>
<button @click="startMemory">Memory</button>
<button @click="startShooter">Shooter</button>
<button @click="startBreakout">Breakout</button>

</div>

<!-- SNAKE -->
<div v-if="game==='snake'">

<h3>Snake</h3>
<p>Score: {{ score }}</p>

<div class="board">
<div
v-for="(cell,i) in grid"
:key="i"
class="cell"
:class="{snake:snake.includes(i),food:food===i}"
></div>
</div>

<button @click="goMenu">Menu</button>

</div>

<!-- RPS -->
<div v-if="game==='rps'">

<h3>Rock Paper Scissors</h3>

<button @click="playRPS('rock')">Rock</button>
<button @click="playRPS('paper')">Paper</button>
<button @click="playRPS('scissors')">Scissors</button>

<p>You: {{ player }}</p>
<p>Computer: {{ computer }}</p>
<p>{{ rpsResult }}</p>

<button @click="goMenu">Menu</button>

</div>

<!-- MEMORY -->
<div v-if="game==='memory'">

<h3>Memory</h3>

<p>{{ memorySequence }}</p>

<input v-model="memoryInput">
<button @click="checkMemory">Check</button>

<p>{{ memoryResult }}</p>

<button @click="goMenu">Menu</button>

</div>

<!-- SHOOTER -->
<div v-if="game==='shooter'">

<h3>Shooter</h3>

<p>Score: {{ shooterScore }}</p>

<button @click="spawnEnemy">Spawn enemy</button>
<button @click="shoot">Shoot</button>

<p v-if="enemy">Enemy alive</p>
<p v-else>No enemy</p>

<button @click="goMenu">Menu</button>

</div>

<!-- BREAKOUT -->
<div v-if="game==='breakout'">

<h3>Breakout</h3>

<p>Blocks: {{ blocks }}</p>

<button @click="hitBlock">Hit</button>

<button @click="goMenu">Menu</button>

</div>

</div>
</template>

<script>
import {ref,onMounted,onUnmounted} from "vue"

export default{

props:['user','auth'],

setup(){

const game=ref("menu")
const goMenu=()=>{game.value="menu";stopSnake()}

//// SNAKE

const size=10
const grid=ref(Array(size*size).fill(0))

const snake=ref([22,21,20])
const direction=ref(1)
const food=ref(40)
const score=ref(0)

let timer=null

const startSnake=()=>{

game.value="snake"

snake.value=[22,21,20]
direction.value=1
score.value=0

spawnFood()

timer=setInterval(moveSnake,200)

}

const spawnFood=()=>{

let f=Math.floor(Math.random()*grid.value.length)

while(snake.value.includes(f)){
f=Math.floor(Math.random()*grid.value.length)
}

food.value=f

}

const moveSnake=()=>{

const head=snake.value[0]
const newHead=head+direction.value

if(newHead<0 || newHead>=grid.value.length){
gameOver()
return
}

snake.value.unshift(newHead)

if(newHead===food.value){

score.value++
spawnFood()

}else{

snake.value.pop()

}

}

const gameOver=()=>{

clearInterval(timer)
alert("Game Over")

}

const stopSnake=()=>clearInterval(timer)

const keyHandler=(e)=>{

if(game.value!=="snake") return

if(e.key==="ArrowUp") direction.value=-size
if(e.key==="ArrowDown") direction.value=size
if(e.key==="ArrowLeft") direction.value=-1
if(e.key==="ArrowRight") direction.value=1

}

onMounted(()=>window.addEventListener("keydown",keyHandler))
onUnmounted(()=>window.removeEventListener("keydown",keyHandler))

//// RPS

const player=ref("")
const computer=ref("")
const rpsResult=ref("")

const startRPS=()=>game.value="rps"

const playRPS=(choice)=>{

const options=["rock","paper","scissors"]
const comp=options[Math.floor(Math.random()*3)]

player.value=choice
computer.value=comp

if(choice===comp) rpsResult.value="Draw"
else if(
(choice==="rock" && comp==="scissors")||
(choice==="paper" && comp==="rock")||
(choice==="scissors" && comp==="paper")
) rpsResult.value="You win"
else rpsResult.value="Computer wins"

}

//// MEMORY

const memorySequence=ref("")
const memoryInput=ref("")
const memoryResult=ref("")

const startMemory=()=>{

game.value="memory"

memorySequence.value=
Math.floor(Math.random()*9)+""+
Math.floor(Math.random()*9)+""+
Math.floor(Math.random()*9)

memoryInput.value=""
memoryResult.value=""

}

const checkMemory=()=>{

if(memoryInput.value===memorySequence.value)
memoryResult.value="Correct"
else
memoryResult.value="Wrong"

}

//// SHOOTER

const shooterScore=ref(0)
const enemy=ref(false)

const startShooter=()=>{

game.value="shooter"
shooterScore.value=0
enemy.value=false

}

const spawnEnemy=()=>enemy.value=true

const shoot=()=>{

if(enemy.value){

enemy.value=false
shooterScore.value++

}

}

//// BREAKOUT

const blocks=ref(10)

const startBreakout=()=>{

game.value="breakout"
blocks.value=10

}

const hitBlock=()=>{

if(blocks.value>0) blocks.value--

}

return{

game,
goMenu,

grid,
snake,
food,
score,

startSnake,

startRPS,
player,
computer,
rpsResult,
playRPS,

startMemory,
memorySequence,
memoryInput,
memoryResult,
checkMemory,

startShooter,
spawnEnemy,
shoot,
enemy,
shooterScore,

startBreakout,
blocks,
hitBlock

}

}

}
</script>

<style>

.board{
display:grid;
grid-template-columns:repeat(10,20px);
gap:2px;
margin:20px 0;
}

.cell{
width:20px;
height:20px;
background:#eee;
}

.snake{
background:#2ecc71;
}

.food{
background:#e74c3c;
}

</style>