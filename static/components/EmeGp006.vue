<template>
  <div class="arcade-app-page">

    <eme-app-title>Arcade Games 🎮</eme-app-title>

    <!-- MENU -->
    <div class="game-menu">
      <button 
        v-for="gameItem in gameList" 
        :key="gameItem.id"
        @click="selectGame(gameItem.id)"
        :class="{ active: currentGame === gameItem.id }"
      >
        {{ gameItem.name }}
      </button>
    </div>

    <!-- GAME CONTAINER -->
    <div class="game-container">

      <!-- 1. SNAKE -->
      <div v-if="currentGame==='snake'" class="game">
        <h3>Snake 🐍</h3>
        <canvas ref="snakeCanvas" width="400" height="400"></canvas>
        <p>Score: {{ snakeScore }}</p>
        <button @click="startSnake">New Game</button>
      </div>

      <!-- 2. CLICKER -->
      <div v-if="currentGame==='clicker'" class="game">
        <h3>Clicker Challenge 👆</h3>
        <p class="score">Score: {{ clickerScore }}</p>
        <div class="clicker-area">
          <button class="click-button" @click="clickerScore++">CLICK ME!</button>
        </div>
        <button @click="clickerScore=0">Reset</button>
      </div>

      <!-- 3. DICE -->
      <div v-if="currentGame==='dice'" class="game">
        <h3>Dice Roller 🎲</h3>
        <div class="dice-display">{{ diceValue }}</div>
        <button @click="rollDice">Roll Dice</button>
        <p>Total rolls: {{ diceRolls }}</p>
      </div>

      <!-- 4. TIC TAC TOE -->
      <div v-if="currentGame==='tictactoe'" class="game">
        <h3>Tic Tac Toe ❌⭕</h3>
        <div class="tic-board">
          <button 
            v-for="(cell, index) in ticBoard" 
            :key="index"
            class="tic-cell"
            @click="makeTicMove(index)"
            :disabled="cell !== '' || ticWinner || ticDraw"
          >
            {{ cell }}
          </button>
        </div>
        <p>{{ ticStatus }}</p>
        <button @click="resetTic">New Game</button>
      </div>

      <!-- 5. MEMORY CARD -->
      <div v-if="currentGame==='memory'" class="game">
        <h3>Memory Cards 🃏</h3>
        <p>Moves: {{ memoryMoves }} | Matches: {{ memoryMatches }}</p>
        <div class="memory-grid">
          <button 
            v-for="(card, index) in memoryCards" 
            :key="index"
            class="memory-card"
            :class="{ flipped: card.flipped, matched: card.matched }"
            @click="flipCard(index)"
            :disabled="card.flipped || card.matched || memoryWaiting"
          >
            {{ card.flipped || card.matched ? card.value : '?' }}
          </button>
        </div>
        <button @click="resetMemory">New Game</button>
      </div>

      <!-- 6. ROCK PAPER SCISSORS -->
      <div v-if="currentGame==='rps'" class="game">
        <h3>Rock Paper Scissors ✂️</h3>
        <div class="rps-choice">
          <button @click="playRPS('rock')">🪨 Rock</button>
          <button @click="playRPS('paper')">📄 Paper</button>
          <button @click="playRPS('scissors')">✂️ Scissors</button>
        </div>
        <div class="rps-result" v-if="rpsPlayerChoice">
          <p>You: {{ rpsPlayerChoice }}</p>
          <p>Computer: {{ rpsComputerChoice }}</p>
          <h3>{{ rpsResult }}</h3>
        </div>
        <p>Score: You {{ rpsPlayerScore }} - {{ rpsComputerScore }} Computer</p>
      </div>

      <!-- 7. SIMON SAYS -->
      <div v-if="currentGame==='simon'" class="game">
        <h3>Simon Says 🔴🟡🟢🔵</h3>
        <div class="simon-grid">
          <button 
            v-for="color in simonColors" 
            :key="color"
            class="simon-button"
            :class="{ active: simonActive === color }"
            :style="{ backgroundColor: color }"
            @click="simonPlayerClick(color)"
            :disabled="!simonPlayerTurn"
          ></button>
        </div>
        <p>Round: {{ simonRound }}</p>
        <button @click="startSimon">Start Game</button>
      </div>

      <!-- 8. NUMBER GUESSER -->
      <div v-if="currentGame==='guesser'" class="game">
        <h3>Number Guesser 🔢</h3>
        <p>Guess a number between 1-100</p>
        <input type="number" v-model="guessInput" @keyup.enter="makeGuess" min="1" max="100">
        <button @click="makeGuess">Guess</button>
        <p>{{ guessMessage }}</p>
        <p>Attempts: {{ guessAttempts }}</p>
        <button @click="resetGuesser">New Game</button>
      </div>

      <!-- 9. WHACK A MOLE -->
      <div v-if="currentGame==='mole'" class="game">
        <h3>Whack a Mole 🐭</h3>
        <p>Score: {{ moleScore }}</p>
        <div class="mole-grid">
          <button 
            v-for="(hole, index) in moleHoles" 
            :key="index"
            class="mole-hole"
            :class="{ active: hole.active }"
            @click="whackMole(index)"
          >
            {{ hole.active ? '🐭' : '🕳️' }}
          </button>
        </div>
        <button @click="startMole" :disabled="moleInterval">Start Game</button>
        <button @click="stopMole">Stop</button>
      </div>

      <!-- 10. SPACE INVADERS (SIMPLE) -->
      <div v-if="currentGame==='space'" class="game">
        <h3>Space Invaders 👾</h3>
        <canvas ref="spaceCanvas" width="400" height="400"></canvas>
        <p>Score: {{ spaceScore }}</p>
        <button @click="startSpace">New Game</button>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from "vue"

export default {
  props: ['user', 'auth'],
  
  setup() {
    const currentGame = ref("snake")
    
    const gameList = [
      { id: "snake", name: "Snake" },
      { id: "clicker", name: "Clicker" },
      { id: "dice", name: "Dice" },
      { id: "tictactoe", name: "Tic Tac Toe" },
      { id: "memory", name: "Memory" },
      { id: "rps", name: "RPS" },
      { id: "simon", name: "Simon" },
      { id: "guesser", name: "Guesser" },
      { id: "mole", name: "Whack a Mole" },
      { id: "space", name: "Space" }
    ]
    
    const selectGame = (gameId) => {
      currentGame.value = gameId
    }
    
    /* SNAKE GAME */
    const snakeCanvas = ref(null)
    const snakeScore = ref(0)
    let snakeCtx, snake, food, dx, dy, snakeInterval
    const grid = 20
    
    const startSnake = () => {
      if(snakeInterval) clearInterval(snakeInterval)
      
      snakeScore.value = 0
      snake = [{x:200, y:200}]
      food = {x:100, y:100}
      dx = grid
      dy = 0
      
      snakeInterval = setInterval(gameLoop, 120)
    }
    
    const gameLoop = () => {
      if(!snakeCtx) return
      
      snakeCtx.clearRect(0, 0, 400, 400)
      
      const head = {
        x: snake[0].x + dx,
        y: snake[0].y + dy
      }
      
      // Wall collision
      if(head.x < 0 || head.x >= 400 || head.y < 0 || head.y >= 400) {
        clearInterval(snakeInterval)
        return
      }
      
      snake.unshift(head)
      
      if(head.x === food.x && head.y === food.y) {
        snakeScore.value++
        food = {
          x: Math.floor(Math.random()*20)*grid,
          y: Math.floor(Math.random()*20)*grid
        }
      } else {
        snake.pop()
      }
      
      // Self collision
      for(let i = 1; i < snake.length; i++) {
        if(snake[i].x === head.x && snake[i].y === head.y) {
          clearInterval(snakeInterval)
        }
      }
      
      snakeCtx.fillStyle = "red"
      snakeCtx.fillRect(food.x, food.y, 18, 18)
      
      snakeCtx.fillStyle = "green"
      snake.forEach(part => {
        snakeCtx.fillRect(part.x, part.y, 18, 18)
      })
    }
    
    /* CLICKER */
    const clickerScore = ref(0)
    
    /* DICE */
    const diceValue = ref(1)
    const diceRolls = ref(0)
    
    const rollDice = () => {
      diceValue.value = Math.floor(Math.random() * 6) + 1
      diceRolls.value++
    }
    
    /* TIC TAC TOE */
    const ticBoard = ref(Array(9).fill(''))
    const ticCurrentPlayer = ref('X')
    const ticWinner = ref(null)
    const ticDraw = ref(false)
    
    const ticStatus = ref("Player X's turn")
    
    const makeTicMove = (index) => {
      if(ticBoard.value[index] !== '' || ticWinner.value) return
      
      const newBoard = [...ticBoard.value]
      newBoard[index] = ticCurrentPlayer.value
      ticBoard.value = newBoard
      
      checkTicWinner()
      
      if(!ticWinner.value) {
        ticCurrentPlayer.value = ticCurrentPlayer.value === 'X' ? 'O' : 'X'
        ticStatus.value = `Player ${ticCurrentPlayer.value}'s turn`
      }
    }
    
    const checkTicWinner = () => {
      const winPatterns = [
        [0,1,2], [3,4,5], [6,7,8],
        [0,3,6], [1,4,7], [2,5,8],
        [0,4,8], [2,4,6]
      ]
      
      for(let pattern of winPatterns) {
        const [a,b,c] = pattern
        if(ticBoard.value[a] && 
           ticBoard.value[a] === ticBoard.value[b] && 
           ticBoard.value[a] === ticBoard.value[c]) {
          ticWinner.value = ticBoard.value[a]
          ticStatus.value = `Player ${ticWinner.value} wins!`
          return
        }
      }
      
      if(ticBoard.value.every(cell => cell !== '')) {
        ticDraw.value = true
        ticStatus.value = "It's a draw!"
      }
    }
    
    const resetTic = () => {
      ticBoard.value = Array(9).fill('')
      ticCurrentPlayer.value = 'X'
      ticWinner.value = null
      ticDraw.value = false
      ticStatus.value = "Player X's turn"
    }
    
    /* MEMORY GAME */
    const memoryCards = ref([])
    const memoryMoves = ref(0)
    const memoryMatches = ref(0)
    const memoryWaiting = ref(false)
    let firstIndex = null
    let secondIndex = null
    
    const initMemory = () => {
      const values = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼']
      const cards = [...values, ...values].sort(() => Math.random() - 0.5)
      memoryCards.value = cards.map(value => ({
        value,
        flipped: false,
        matched: false
      }))
      memoryMoves.value = 0
      memoryMatches.value = 0
    }
    
    const flipCard = (index) => {
      if(memoryWaiting.value) return
      if(memoryCards.value[index].flipped || memoryCards.value[index].matched) return
      
      const newCards = [...memoryCards.value]
      newCards[index].flipped = true
      memoryCards.value = newCards
      
      if(firstIndex === null) {
        firstIndex = index
      } else if(secondIndex === null && index !== firstIndex) {
        secondIndex = index
        memoryMoves.value++
        checkMatch()
      }
    }
    
    const checkMatch = () => {
      memoryWaiting.value = true
      
      if(memoryCards.value[firstIndex].value === memoryCards.value[secondIndex].value) {
        const newCards = [...memoryCards.value]
        newCards[firstIndex].matched = true
        newCards[secondIndex].matched = true
        memoryCards.value = newCards
        memoryMatches.value++
        firstIndex = null
        secondIndex = null
        memoryWaiting.value = false
      } else {
        setTimeout(() => {
          const newCards = [...memoryCards.value]
          newCards[firstIndex].flipped = false
          newCards[secondIndex].flipped = false
          memoryCards.value = newCards
          firstIndex = null
          secondIndex = null
          memoryWaiting.value = false
        }, 1000)
      }
    }
    
    const resetMemory = () => {
      initMemory()
      firstIndex = null
      secondIndex = null
      memoryWaiting.value = false
    }
    
    /* ROCK PAPER SCISSORS */
    const rpsPlayerChoice = ref('')
    const rpsComputerChoice = ref('')
    const rpsResult = ref('')
    const rpsPlayerScore = ref(0)
    const rpsComputerScore = ref(0)
    
    const playRPS = (choice) => {
      const choices = ['rock', 'paper', 'scissors']
      const computer = choices[Math.floor(Math.random() * 3)]
      
      rpsPlayerChoice.value = choice
      rpsComputerChoice.value = computer
      
      if(choice === computer) {
        rpsResult.value = "It's a tie!"
      } else if(
        (choice === 'rock' && computer === 'scissors') ||
        (choice === 'paper' && computer === 'rock') ||
        (choice === 'scissors' && computer === 'paper')
      ) {
        rpsResult.value = "You win!"
        rpsPlayerScore.value++
      } else {
        rpsResult.value = "Computer wins!"
        rpsComputerScore.value++
      }
    }
    
    /* SIMON SAYS */
    const simonColors = ['red', 'yellow', 'green', 'blue']
    const simonSequence = ref([])
    const simonPlayerSequence = ref([])
    const simonRound = ref(1)
    const simonActive = ref('')
    const simonPlayerTurn = ref(false)
    let simonInterval = null
    
    const startSimon = () => {
      simonSequence.value = []
      simonPlayerSequence.value = []
      simonRound.value = 1
      simonPlayerTurn.value = false
      nextSimonRound()
    }
    
    const nextSimonRound = () => {
      simonPlayerTurn.value = false
      simonSequence.value.push(simonColors[Math.floor(Math.random() * 4)])
      
      let i = 0
      simonInterval = setInterval(() => {
        if(i < simonSequence.value.length) {
          simonActive.value = simonSequence.value[i]
          setTimeout(() => {
            simonActive.value = ''
          }, 500)
          i++
        } else {
          clearInterval(simonInterval)
          simonPlayerTurn.value = true
          simonPlayerSequence.value = []
        }
      }, 800)
    }
    
    const simonPlayerClick = (color) => {
      if(!simonPlayerTurn.value) return
      
      simonActive.value = color
      setTimeout(() => {
        simonActive.value = ''
      }, 300)
      
      simonPlayerSequence.value.push(color)
      
      const currentIndex = simonPlayerSequence.value.length - 1
      if(simonPlayerSequence.value[currentIndex] !== simonSequence.value[currentIndex]) {
        alert('Game Over!')
        simonPlayerTurn.value = false
        return
      }
      
      if(simonPlayerSequence.value.length === simonSequence.value.length) {
        simonRound.value++
        nextSimonRound()
      }
    }
    
    /* NUMBER GUESSER */
    const secretNumber = ref(Math.floor(Math.random() * 100) + 1)
    const guessInput = ref('')
    const guessMessage = ref('')
    const guessAttempts = ref(0)
    
    const makeGuess = () => {
      const guess = parseInt(guessInput.value)
      if(isNaN(guess)) return
      
      guessAttempts.value++
      
      if(guess === secretNumber.value) {
        guessMessage.value = `Correct! You won in ${guessAttempts.value} attempts!`
      } else if(guess < secretNumber.value) {
        guessMessage.value = 'Too low! Try again.'
      } else {
        guessMessage.value = 'Too high! Try again.'
      }
      
      guessInput.value = ''
    }
    
    const resetGuesser = () => {
      secretNumber.value = Math.floor(Math.random() * 100) + 1
      guessInput.value = ''
      guessMessage.value = ''
      guessAttempts.value = 0
    }
    
    /* WHACK A MOLE */
    const moleHoles = ref(Array(9).fill().map(() => ({ active: false })))
    const moleScore = ref(0)
    let moleInterval = null
    
    const startMole = () => {
      stopMole()
      moleScore.value = 0
      moleInterval = setInterval(() => {
        const newHoles = moleHoles.value.map(() => ({ active: false }))
        const randomIndex = Math.floor(Math.random() * 9)
        newHoles[randomIndex].active = true
        moleHoles.value = newHoles
      }, 800)
    }
    
    const stopMole = () => {
      if(moleInterval) {
        clearInterval(moleInterval)
        moleInterval = null
      }
    }
    
    const whackMole = (index) => {
      if(moleHoles.value[index].active) {
        moleScore.value++
        const newHoles = [...moleHoles.value]
        newHoles[index].active = false
        moleHoles.value = newHoles
      }
    }
    
    /* SPACE INVADERS */
    const spaceCanvas = ref(null)
    const spaceScore = ref(0)
    let spaceCtx, player, bullets, enemies, spaceInterval
    
    const startSpace = () => {
      if(spaceInterval) clearInterval(spaceInterval)
      
      player = { x: 180, y: 350, width: 40, height: 20 }
      bullets = []
      enemies = []
      spaceScore.value = 0
      
      // Create enemies
      for(let row = 0; row < 3; row++) {
        for(let col = 0; col < 5; col++) {
          enemies.push({
            x: 50 + col * 60,
            y: 50 + row * 40,
            width: 30,
            height: 20,
            alive: true
          })
        }
      }
      
      spaceInterval = setInterval(spaceGameLoop, 50)
    }
    
    const spaceGameLoop = () => {
      if(!spaceCtx) return
      
      spaceCtx.clearRect(0, 0, 400, 400)
      
      // Draw player
      spaceCtx.fillStyle = 'blue'
      spaceCtx.fillRect(player.x, player.y, player.width, player.height)
      
      // Move and draw bullets
      bullets = bullets.filter(b => b.y > 0)
      bullets.forEach(b => b.y -= 5)
      
      spaceCtx.fillStyle = 'red'
      bullets.forEach(b => spaceCtx.fillRect(b.x, b.y, 3, 10))
      
      // Draw enemies
      spaceCtx.fillStyle = 'green'
      enemies.forEach(enemy => {
        if(enemy.alive) {
          spaceCtx.fillRect(enemy.x, enemy.y, enemy.width, enemy.height)
        }
      })
      
      // Collision detection
      bullets.forEach((bullet, bIndex) => {
        enemies.forEach((enemy, eIndex) => {
          if(enemy.alive &&
             bullet.x > enemy.x &&
             bullet.x < enemy.x + enemy.width &&
             bullet.y > enemy.y &&
             bullet.y < enemy.y + enemy.height) {
            enemy.alive = false
            bullets.splice(bIndex, 1)
            spaceScore.value += 10
          }
        })
      })
      
      // Check win/lose
      if(enemies.every(e => !e.alive)) {
        clearInterval(spaceInterval)
        alert('You win!')
      }
    }
    
    const shootBullet = () => {
      bullets.push({ x: player.x + player.width/2, y: player.y })
    }
    
    /* KEYBOARD CONTROLS */
    const handleKeyDown = (e) => {
      if(currentGame.value === 'snake') {
        if(e.key === "ArrowUp") { dx = 0; dy = -grid }
        if(e.key === "ArrowDown") { dx = 0; dy = grid }
        if(e.key === "ArrowLeft") { dx = -grid; dy = 0 }
        if(e.key === "ArrowRight") { dx = grid; dy = 0 }
      }
      
      if(currentGame.value === 'space') {
        if(e.key === "ArrowLeft") player.x = Math.max(0, player.x - 10)
        if(e.key === "ArrowRight") player.x = Math.min(360, player.x + 10)
        if(e.key === " ") {
          e.preventDefault()
          shootBullet()
        }
      }
    }
    
    onMounted(() => {
      // Snake canvas
      if(snakeCanvas.value) {
        snakeCtx = snakeCanvas.value.getContext("2d")
      }
      
      // Space canvas
      if(spaceCanvas.value) {
        spaceCtx = spaceCanvas.value.getContext("2d")
      }
      
      window.addEventListener("keydown", handleKeyDown)
      
      // Initialize games
      initMemory()
    })
    
    onUnmounted(() => {
      window.removeEventListener("keydown", handleKeyDown)
      if(snakeInterval) clearInterval(snakeInterval)
      if(spaceInterval) clearInterval(spaceInterval)
      if(moleInterval) clearInterval(moleInterval)
    })
    
    return {
      currentGame,
      gameList,
      selectGame,
      
      // Snake
      snakeCanvas,
      snakeScore,
      startSnake,
      
      // Clicker
      clickerScore,
      
      // Dice
      diceValue,
      diceRolls,
      rollDice,
      
      // Tic Tac Toe
      ticBoard,
      ticStatus,
      ticWinner,
      ticDraw,
      makeTicMove,
      resetTic,
      
      // Memory
      memoryCards,
      memoryMoves,
      memoryMatches,
      memoryWaiting,
      flipCard,
      resetMemory,
      
      // RPS
      rpsPlayerChoice,
      rpsComputerChoice,
      rpsResult,
      rpsPlayerScore,
      rpsComputerScore,
      playRPS,
      
      // Simon
      simonColors,
      simonRound,
      simonActive,
      simonPlayerTurn,
      startSimon,
      simonPlayerClick,
      
      // Guesser
      guessInput,
      guessMessage,
      guessAttempts,
      makeGuess,
      resetGuesser,
      
      // Mole
      moleHoles,
      moleScore,
      moleInterval,
      startMole,
      stopMole,
      whackMole,
      
      // Space
      spaceCanvas,
      spaceScore,
      startSpace
    }
  }
}
</script>

<style>
.arcade-app-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.game-menu {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 20px 0;
  justify-content: center;
}

.game-menu button {
  padding: 8px 14px;
  background: #f0f0f0;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.game-menu button.active {
  background: #4CAF50;
  color: white;
  border-color: #45a049;
}

.game-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.game {
  text-align: center;
}

canvas {
  border: 2px solid #333;
  border-radius: 8px;
  margin: 10px 0;
  background: #f8f8f8;
}

button {
  margin: 5px;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #4CAF50;
  color: white;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s;
}

button:hover:not(:disabled) {
  background: #45a049;
  transform: scale(1.05);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.score {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

/* Dice */
.dice-display {
  font-size: 80px;
  margin: 20px;
  animation: roll 0.3s;
}

@keyframes roll {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Tic Tac Toe */
.tic-board {
  display: grid;
  grid-template-columns: repeat(3, 100px);
  gap: 5px;
  justify-content: center;
  margin: 20px auto;
}

.tic-cell {
  width: 100px;
  height: 100px;
  background: white;
  border: 2px solid #333;
  font-size: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* Memory */
.memory-grid {
  display: grid;
  grid-template-columns: repeat(4, 80px);
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.memory-card {
  width: 80px;
  height: 80px;
  background: #4CAF50;
  border: 2px solid #45a049;
  border-radius: 8px;
  font-size: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.memory-card.flipped {
  background: white;
}

.memory-card.matched {
  background: #ffd700;
  border-color: #daa520;
}

/* RPS */
.rps-choice {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.rps-result {
  margin: 20px 0;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 8px;
}

/* Simon */
.simon-grid {
  display: grid;
  grid-template-columns: repeat(2, 120px);
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.simon-button {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  transition: all 0.2s;
}

.simon-button.active {
  filter: brightness(1.5);
  transform: scale(1.05);
}

/* Mole */
.mole-grid {
  display: grid;
  grid-template-columns: repeat(3, 100px);
  gap: 10px;
  justify-content: center;
  margin: 20px 0;
}

.mole-hole {
  width: 100px;
  height: 100px;
  background: #8B4513;
  border-radius: 50%;
  font-size: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.mole-hole.active {
  background: #D2691E;
  transform: scale(1.1);
}

/* Clicker */
.clicker-area {
  margin: 30px 0;
}

.click-button {
  font-size: 30px;
  padding: 20px 40px;
  background: #ff6b6b;
  border-radius: 50px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

/* Input */
input[type="number"] {
  padding: 10px;
  font-size: 16px;
  border: 2px solid #ddd;
  border-radius: 6px;
  margin: 10px;
  width: 100px;
}

/* Responsive */
@media (max-width: 600px) {
  .game-menu button {
    padding: 6px 10px;
    font-size: 14px;
  }
  
  .memory-grid {
    grid-template-columns: repeat(4, 60px);
  }
  
  .memory-card {
    width: 60px;
    height: 60px;
    font-size: 24px;
  }
}
</style>