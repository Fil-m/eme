<template>
  <div class="schulte-table-app">
    <eme-app-title>Тренажер таблиць Шультьє 🎯</eme-app-title>

    <!-- Панель налаштувань -->
    <div class="settings-panel">
      <h3>⚙️ Налаштування</h3>
      
      <div class="settings-grid">
        <!-- Основні параметри -->
        <div class="setting-group">
          <label>Кількість стовпців:</label>
          <input type="number" v-model.number="settings.cols" min="2" max="10" @change="regenerateGrid">
        </div>
        
        <div class="setting-group">
          <label>Кількість рядків:</label>
          <input type="number" v-model.number="settings.rows" min="2" max="10" @change="regenerateGrid">
        </div>
        
        <div class="setting-group">
          <label>Розмір сторони (px):</label>
          <input type="number" v-model.number="settings.cellSize" min="30" max="150" step="5">
        </div>

        <!-- Порядок рахування -->
        <div class="setting-group">
          <label>Порядок:</label>
          <select v-model="settings.order">
            <option value="forward">Прямий (1→N)</option>
            <option value="backward">Зворотній (N→1)</option>
            <option value="random">Спонтанний</option>
          </select>
        </div>

        <!-- Тип символів -->
        <div class="setting-group">
          <label>Тип символів:</label>
          <select v-model="settings.symbolType" @change="regenerateGrid">
            <option value="numbers">Цифри</option>
            <option value="letters">Букви (A-Z)</option>
            <option value="custom">Користувацькі</option>
          </select>
        </div>

        <!-- Користувацькі символи -->
        <div class="setting-group" v-if="settings.symbolType === 'custom'">
          <label>Символи (через кому):</label>
          <input type="text" v-model="settings.customSymbols" @change="regenerateGrid" placeholder="A,B,C,D">
        </div>

        <!-- Кольори -->
        <div class="setting-group">
          <label>Колір фону:</label>
          <input type="color" v-model="settings.bgColor">
        </div>
        
        <div class="setting-group">
          <label>Колір цифр:</label>
          <input type="color" v-model="settings.textColor">
        </div>

        <!-- Режими -->
        <div class="setting-group">
          <label>
            <input type="checkbox" v-model="settings.showTimer">
            Таймер
          </label>
        </div>

        <div class="setting-group">
          <label>
            <input type="checkbox" v-model="settings.markClicked">
            Відмічати відклікані
          </label>
        </div>

        <div class="setting-group">
          <label>
            <input type="checkbox" v-model="settings.memoryMode">
            Режим пам'яті
          </label>
        </div>

        <!-- Сторона для спонтанного порядку -->
        <div class="setting-group" v-if="settings.order === 'random'">
          <label>Сторона показу:</label>
          <select v-model="settings.randomSide">
            <option value="top">Зверху</option>
            <option value="right">Справа</option>
            <option value="bottom">Знизу</option>
            <option value="left">Зліва</option>
          </select>
        </div>
      </div>

      <div class="settings-actions">
        <button @click="startGame" :disabled="gameActive">Старт</button>
        <button @click="resetGame">Скинути</button>
        <button @click="saveSettings">Зберегти налаштування</button>
        <button @click="loadSettings">Завантажити</button>
      </div>
    </div>

    <!-- Ігрове поле -->
    <div class="game-area">
      <!-- Інформація -->
      <div class="game-info">
        <div class="stats">
          <p>Знайдено: {{ foundCount }} / {{ totalItems }}</p>
          <p v-if="settings.showTimer">Час: {{ formatTime(elapsedTime) }}</p>
          <p v-if="nextTarget">Наступний: {{ nextTarget }}</p>
        </div>
        
        <!-- Показ цілі для спонтанного режиму -->
        <div v-if="settings.order === 'random' && currentTarget" class="random-target" :class="settings.randomSide">
          <div class="target-box" :style="{ backgroundColor: settings.bgColor, color: settings.textColor }">
            {{ currentTarget }}
          </div>
        </div>
      </div>

      <!-- Таблиця -->
      <div class="table-container" :style="{ 
        gridTemplateColumns: `repeat(${settings.cols}, ${settings.cellSize}px)` 
      }">
        <div
          v-for="(cell, index) in grid"
          :key="index"
          class="grid-cell"
          :style="{
            width: settings.cellSize + 'px',
            height: settings.cellSize + 'px',
            backgroundColor: cell.clicked && settings.markClicked ? '#90EE90' : settings.bgColor,
            color: settings.textColor,
            fontSize: (settings.cellSize * 0.4) + 'px',
            opacity: (settings.memoryMode && !cell.shown && !cell.clicked) ? 0.3 : 1
          }"
          @click="handleCellClick(index)"
        >
          {{ showCellContent(cell) }}
        </div>
      </div>

      <!-- Режим пам'яті - поле введення -->
      <div v-if="settings.memoryMode && gameActive" class="memory-input">
        <input 
          type="text" 
          v-model="memoryInput" 
          @keyup.enter="checkMemoryInput"
          :placeholder="'Введіть ' + nextTarget"
          autofocus
        >
        <button @click="checkMemoryInput">Перевірити</button>
      </div>

      <!-- Результати -->
      <div v-if="gameComplete" class="game-complete">
        <h2>🎉 Вітаємо! 🎉</h2>
        <p>Час: {{ formatTime(elapsedTime) }}</p>
        <p>Кліків: {{ totalClicks }}</p>
        <p>Помилок: {{ mistakes }}</p>
        <button @click="startGame">Грати ще</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onUnmounted } from 'vue'

export default {
  props: ['user', 'auth'],
  
  setup() {
    // Налаштування за замовчуванням
    const defaultSettings = {
      cols: 5,
      rows: 5,
      cellSize: 80,
      order: 'forward',
      bgColor: '#ffffff',
      textColor: '#000000',
      showTimer: true,
      markClicked: true,
      symbolType: 'numbers',
      customSymbols: 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z',
      memoryMode: false,
      randomSide: 'top'
    }

    const settings = reactive({ ...defaultSettings })
    
    // Стан гри
    const grid = ref([])
    const gameActive = ref(false)
    const gameComplete = ref(false)
    const foundCount = ref(0)
    const totalItems = computed(() => settings.cols * settings.rows)
    const nextTarget = ref('')
    const currentTarget = ref('')
    const elapsedTime = ref(0)
    const totalClicks = ref(0)
    const mistakes = ref(0)
    const memoryInput = ref('')
    
    let timerInterval = null
    let targetSequence = []
    let currentIndex = 0

    // Генерація символів
    const generateSymbols = () => {
      const count = totalItems.value
      
      if (settings.symbolType === 'numbers') {
        return Array.from({ length: count }, (_, i) => (i + 1).toString())
      } 
      else if (settings.symbolType === 'letters') {
        const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
        return Array.from({ length: count }, (_, i) => letters[i % 26])
      }
      else if (settings.symbolType === 'custom') {
        const custom = settings.customSymbols.split(',').map(s => s.trim())
        return Array.from({ length: count }, (_, i) => custom[i % custom.length])
      }
    }

    // Створення сітки
    const regenerateGrid = () => {
      const symbols = generateSymbols()
      const shuffled = [...symbols].sort(() => Math.random() - 0.5)
      
      grid.value = shuffled.map(value => ({
        value,
        clicked: false,
        shown: !settings.memoryMode // В режимі пам'яті спочатку показуємо всі
      }))

      // В режимі пам'яті ховаємо після короткої затримки
      if (settings.memoryMode) {
        setTimeout(() => {
          grid.value = grid.value.map(cell => ({
            ...cell,
            shown: false
          }))
        }, 3000)
      }
    }

    // Початок гри
    const startGame = () => {
      regenerateGrid()
      gameActive.value = true
      gameComplete.value = false
      foundCount.value = 0
      totalClicks.value = 0
      mistakes.value = 0
      currentIndex = 0
      
      // Створення послідовності
      const symbols = grid.value.map(cell => cell.value)
      
      if (settings.order === 'forward') {
        targetSequence = [...symbols].sort((a, b) => a - b)
      } else if (settings.order === 'backward') {
        targetSequence = [...symbols].sort((a, b) => b - a)
      } else {
        targetSequence = symbols
      }
      
      nextTarget.value = targetSequence[0]
      
      // Таймер
      if (settings.showTimer) {
        elapsedTime.value = 0
        if (timerInterval) clearInterval(timerInterval)
        timerInterval = setInterval(() => {
          if (gameActive.value && !gameComplete.value) {
            elapsedTime.value++
          }
        }, 1000)
      }
    }

    // Скидання гри
    const resetGame = () => {
      gameActive.value = false
      gameComplete.value = false
      foundCount.value = 0
      elapsedTime.value = 0
      totalClicks.value = 0
      mistakes.value = 0
      memoryInput.value = ''
      if (timerInterval) clearInterval(timerInterval)
      regenerateGrid()
    }

    // Обробка кліку в звичайному режимі
    const handleCellClick = (index) => {
      if (!gameActive.value || gameComplete.value) return
      
      totalClicks.value++
      const cell = grid.value[index]
      
      // Режим пам'яті
      if (settings.memoryMode) {
        if (!cell.shown) {
          cell.shown = true
          if (cell.value === nextTarget.value) {
            cell.clicked = true
            foundCount.value++
            currentIndex++
            
            if (currentIndex < targetSequence.length) {
              nextTarget.value = targetSequence[currentIndex]
            } else {
              gameComplete.value = true
              gameActive.value = false
            }
          } else {
            mistakes.value++
            setTimeout(() => {
              cell.shown = false
            }, 500)
          }
        }
        return
      }
      
      // Звичайний режим
      if (settings.order === 'random') {
        currentTarget.value = targetSequence[Math.floor(Math.random() * targetSequence.length)]
      }
      
      if (cell.value === nextTarget.value && !cell.clicked) {
        cell.clicked = true
        foundCount.value++
        currentIndex++
        
        if (currentIndex < targetSequence.length) {
          nextTarget.value = targetSequence[currentIndex]
        } else {
          gameComplete.value = true
          gameActive.value = false
        }
      } else if (cell.value !== nextTarget.value) {
        mistakes.value++
      }
    }

    // Перевірка введення в режимі пам'яті
    const checkMemoryInput = () => {
      if (!gameActive.value || gameComplete.value) return
      
      totalClicks.value++
      
      if (memoryInput.value === nextTarget.value) {
        foundCount.value++
        currentIndex++
        
        if (currentIndex < targetSequence.length) {
          nextTarget.value = targetSequence[currentIndex]
        } else {
          gameComplete.value = true
          gameActive.value = false
        }
        memoryInput.value = ''
      } else {
        mistakes.value++
      }
    }

    // Відображення вмісту клітинки
    const showCellContent = (cell) => {
      if (settings.memoryMode) {
        return cell.shown || cell.clicked ? cell.value : '?'
      }
      return cell.value
    }

    // Форматування часу
    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    // Збереження/завантаження налаштувань
    const saveSettings = () => {
      localStorage.setItem('schulteSettings', JSON.stringify(settings))
      alert('Налаштування збережено!')
    }

    const loadSettings = () => {
      const saved = localStorage.getItem('schulteSettings')
      if (saved) {
        const parsed = JSON.parse(saved)
        Object.assign(settings, parsed)
        regenerateGrid()
        alert('Налаштування завантажено!')
      }
    }

    // Стеження за змінами
    watch(() => [settings.cols, settings.rows, settings.symbolType], () => {
      if (!gameActive.value) {
        regenerateGrid()
      }
    })

    // Очищення таймера
    onUnmounted(() => {
      if (timerInterval) clearInterval(timerInterval)
    })

    // Початкова генерація
    regenerateGrid()

    return {
      settings,
      grid,
      gameActive,
      gameComplete,
      foundCount,
      totalItems,
      nextTarget,
      currentTarget,
      elapsedTime,
      totalClicks,
      mistakes,
      memoryInput,
      startGame,
      resetGame,
      handleCellClick,
      checkMemoryInput,
      showCellContent,
      formatTime,
      saveSettings,
      loadSettings,
      regenerateGrid
    }
  }
}
</script>

<style scoped>
.schulte-table-app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.settings-panel {
  background: #f5f5f5;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-group label {
  font-weight: 600;
  color: #555;
  font-size: 14px;
}

.setting-group input[type="number"],
.setting-group input[type="text"],
.setting-group select {
  padding: 8px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.setting-group input[type="number"]:focus,
.setting-group input[type="text"]:focus,
.setting-group select:focus {
  border-color: #4CAF50;
  outline: none;
}

.setting-group input[type="color"] {
  width: 100%;
  height: 40px;
  border: 2px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
}

.setting-group input[type="checkbox"] {
  margin-right: 8px;
  transform: scale(1.2);
}

.settings-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.settings-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #4CAF50;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.settings-actions button:hover {
  background: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.settings-actions button:last-child {
  background: #2196F3;
}

.settings-actions button:last-child:hover {
  background: #1976D2;
}

.game-area {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.game-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stats {
  display: flex;
  gap: 30px;
}

.stats p {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.random-target {
  position: fixed;
  z-index: 1000;
}

.random-target.top {
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.random-target.right {
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.random-target.bottom {
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
}

.random-target.left {
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
}

.target-box {
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.table-container {
  display: grid;
  gap: 5px;
  justify-content: center;
  margin: 30px 0;
}

.grid-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.grid-cell:hover:not(.clicked) {
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.memory-input {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 30px;
}

.memory-input input {
  padding: 12px 20px;
  font-size: 18px;
  border: 2px solid #ddd;
  border-radius: 8px;
  width: 200px;
  text-align: center;
}

.memory-input input:focus {
  border-color: #4CAF50;
  outline: none;
}

.memory-input button {
  padding: 12px 30px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.memory-input button:hover {
  background: #45a049;
  transform: translateY(-2px);
}

.game-complete {
  text-align: center;
  margin-top: 40px;
  padding: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.game-complete h2 {
  font-size: 36px;
  margin-bottom: 20px;
}

.game-complete p {
  font-size: 24px;
  margin: 10px 0;
}

.game-complete button {
  margin-top: 20px;
  padding: 15px 40px;
  font-size: 20px;
  background: white;
  color: #764ba2;
  border: none;
  border-radius: 50px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.game-complete button:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(255,255,255,0.3);
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .game-info {
    flex-direction: column;
    gap: 15px;
  }
  
  .stats {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .grid-cell {
    font-size: 14px;
  }
}
</style>