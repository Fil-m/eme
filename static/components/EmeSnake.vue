<h1>Mini Games 🎮</h1>

<div>
<button onclick="showGame('snake')">Snake</button>
<button onclick="showGame('ttt')">Tic Tac Toe</button>
<button onclick="showGame('clicker')">Clicker</button>
</div>

<div id="snake" style="display:none">
<h2>Snake</h2>
<canvas id="snakeCanvas" width="400" height="400"></canvas>
</div>

<div id="ttt" style="display:none">

<h2>Tic Tac Toe</h2>

<div id="board">
{% for i in "012345678" %}
<button class="cell" onclick="play(this)"></button>
{% endfor %}
</div>

</div>

<div id="clicker" style="display:none">

<h2>Clicker</h2>

Score: <span id="score">0</span>

<br><br>

<button onclick="addScore()">CLICK</button>

</div>

<style>

#board{
display:grid;
grid-template-columns:repeat(3,80px);
gap:5px;
}

.cell{
width:80px;
height:80px;
font-size:30px;
}

canvas{
border:2px solid black;
}

</style>

<script>

function showGame(id){
document.getElementById("snake").style.display="none";
document.getElementById("ttt").style.display="none";
document.getElementById("clicker").style.display="none";

document.getElementById(id).style.display="block";
}

</script>

<script>

let score=0;

function addScore(){
score++;
document.getElementById("score").innerText=score;
}

</script>

<script>

let player="X";

function play(cell){

if(cell.innerHTML!="") return;

cell.innerHTML=player;

player = player==="X" ? "O" : "X";

}

</script>

<script>

const canvas=document.getElementById("snakeCanvas");
const ctx=canvas.getContext("2d");

let snake=[{x:200,y:200}];
let food={x:100,y:100};

let dx=20;
let dy=0;

document.addEventListener("keydown",e=>{

if(e.key=="ArrowUp"){dx=0;dy=-20;}
if(e.key=="ArrowDown"){dx=0;dy=20;}
if(e.key=="ArrowLeft"){dx=-20;dy=0;}
if(e.key=="ArrowRight"){dx=20;dy=0;}

});

function game(){

ctx.clearRect(0,0,400,400);

let head={x:snake[0].x+dx,y:snake[0].y+dy};

snake.unshift(head);

if(head.x==food.x && head.y==food.y){

food={
x:Math.floor(Math.random()*20)*20,
y:Math.floor(Math.random()*20)*20
};

}else{

snake.pop();

}

ctx.fillStyle="red";
ctx.fillRect(food.x,food.y,20,20);

ctx.fillStyle="green";

snake.forEach(p=>{
ctx.fillRect(p.x,p.y,20,20);
});

}

setInterval(game,120);

</script>