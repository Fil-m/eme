<!DOCTYPE html>
<html>
<head>
<title>Mini Games</title>

<style>
body{
font-family:Arial;
background:#111;
color:white;
text-align:center;
}

.menu button{
margin:10px;
padding:10px 20px;
font-size:16px;
cursor:pointer;
}

.game{
display:none;
margin-top:20px;
}

canvas{
background:black;
border:2px solid lime;
}

#board{
display:grid;
grid-template-columns:repeat(3,80px);
gap:5px;
justify-content:center;
}

.cell{
width:80px;
height:80px;
font-size:30px;
}
</style>

</head>
<body>

<h1>🎮 Mini Games</h1>

<div class="menu">
<button onclick="showGame('snake')">Snake</button>
<button onclick="showGame('ttt')">Tic Tac Toe</button>
<button onclick="showGame('clicker')">Clicker</button>
</div>

<!-- SNAKE -->

<div id="snake" class="game">

<h2>Snake 🐍</h2>

<canvas id="snakeCanvas" width="400" height="400"></canvas>

</div>

<!-- TIC TAC TOE -->

<div id="ttt" class="game">

<h2>Tic Tac Toe</h2>

<div id="board">
{% for i in "012345678" %}
<button class="cell" onclick="play(this)"></button>
{% endfor %}
</div>

</div>

<!-- CLICKER -->

<div id="clicker" class="game">

<h2>Clicker</h2>

<p>Score: <span id="score">0</span></p>

<button onclick="addScore()">CLICK</button>

</div>

<script>

function showGame(id){

document.querySelectorAll(".game").forEach(g=>{
g.style.display="none";
});

document.getElementById(id).style.display="block";

}

</script>

<!-- CLICKER SCRIPT -->

<script>

let score=0;

function addScore(){
score++;
document.getElementById("score").innerText=score;
}

</script>

<!-- TIC TAC TOE SCRIPT -->

<script>

let player="X";

function play(cell){

if(cell.innerHTML!="") return;

cell.innerHTML=player;

player = player==="X" ? "O" : "X";

}

</script>

<!-- SNAKE SCRIPT -->

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

ctx.fillStyle="lime";

snake.forEach(p=>{
ctx.fillRect(p.x,p.y,20,20);
});

}

setInterval(game,120);

</script>

</body>
</html>