<template>
  <div class="rpg-level">
    <!-- Інтерфейс гравця -->
    <div class="player-hud">
      <div class="player-stats">
        <div class="stat">❤️ HP: {{ player.health }}/{{ player.maxHealth }}</div>
        <div class="stat">⚔️ Сила: {{ player.strength }}</div>
        <div class="stat">🛡️ Захист: {{ player.defense }}</div>
        <div class="stat">✨ Досвід: {{ player.exp }}/{{ player.nextLevelExp }}</div>
        <div class="stat">📊 Рівень: {{ player.level }}</div>
      </div>
      
      <!-- Здоров'я у вигляді прогрес-бару -->
      <div class="health-bar">
        <div class="health-fill" :style="{ width: (player.health / player.maxHealth * 100) + '%' }"></div>
      </div>
      
      <!-- Інвентар (швидкий доступ) -->
      <div class="inventory">
        <div v-for="(item, index) in inventory" :key="index" 
             class="inventory-slot"
             :class="{ equipped: item.equipped }"
             @click="useItem(item)">
          {{ item.icon }}
          <span class="item-count" v-if="item.count > 1">{{ item.count }}</span>
        </div>
      </div>
    </div>

    <!-- Ігрове поле -->
    <div class="game-area">
      <!-- Карта (2D сітка) -->
      <div class="game-grid" :style="gridStyle">
        <div v-for="(row, y) in gameMap" :key="y" class="grid-row">
          <div v-for="(tile, x) in row" :key="x" 
               class="grid-cell"
               :class="{
                 'wall': tile.type === 'wall',
                 'floor': tile.type === 'floor',
                 'water': tile.type === 'water',
                 'chest': tile.type === 'chest',
                 'door': tile.type === 'door'
               }"
               :style="getTileStyle(tile)"
               @click="movePlayer(x, y)">
            
            <!-- Відображення гравця -->
            <div v-if="player.x === x && player.y === y" class="entity player">
              🦸‍♂️
              <div class="health-indicator" v-if="player.health < player.maxHealth">
                {{ player.health }}/{{ player.maxHealth }}
              </div>
            </div>
            
            <!-- Відображення ворогів -->
            <div v-for="enemy in enemiesAt(x, y)" :key="enemy.id" 
                 class="entity enemy"
                 :class="'difficulty-' + enemy.difficulty"
                 @click.stop="attackEnemy(enemy)">
              {{ enemy.icon }}
              <div class="enemy-tooltip">
                <div>{{ enemy.name }}</div>
                <div>❤️ {{ enemy.health }}/{{ enemy.maxHealth }}</div>
                <div>⚔️ {{ enemy.damage }}</div>
                <div>🛡️ {{ enemy.armor }}</div>
                <div>⭐ Складність: {{ enemy.difficultyLevel }}</div>
              </div>
            </div>
            
            <!-- Предмети на підлозі -->
            <div v-if="tile.item" class="item" @click.stop="pickupItem(x, y)">
              {{ tile.item.icon }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Бічна панель з ворогами -->
      <div class="enemy-panel">
        <h3>⚔️ Вороги на рівні</h3>
        <div v-for="enemy in enemies" :key="enemy.id" class="enemy-card"
             :class="'difficulty-' + enemy.difficulty"
             @click="targetEnemy(enemy)">
          <div class="enemy-icon">{{ enemy.icon }}</div>
          <div class="enemy-info">
            <div class="enemy-name">{{ enemy.name }}</div>
            <div class="enemy-stats">
              <span>❤️ {{ enemy.health }}/{{ enemy.maxHealth }}</span>
              <span>⚔️ {{ enemy.damage }}</span>
            </div>
            <div class="enemy-difficulty">
              <span v-for="n in enemy.difficultyLevel" :key="n">⭐</span>
              <span v-for="n in (5 - enemy.difficultyLevel)" :key="'empty'+n" class="empty-star">☆</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Лог бою -->
    <div class="combat-log">
      <div v-for="(log, index) in combatLog" :key="index" 
           :class="'log-' + log.type">
        {{ log.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

// Стан гравця
const player = reactive({
  x: 1,
  y: 1,
  health: 100,
  maxHealth: 100,
  strength: 15,
  defense: 10,
  exp: 0,
  nextLevelExp: 100,
  level: 1,
  gold: 50
})

// Інвентар
const inventory = ref([
  { id: 1, name: 'Меч', icon: '⚔️', type: 'weapon', damage: 5, equipped: true, count: 1 },
  { id: 2, name: 'Щит', icon: '🛡️', type: 'armor', defense: 3, equipped: true, count: 1 },
  { id: 3, name: 'Зілля здоров\'я', icon: '🧪', type: 'potion', heal: 30, count: 3 },
  { id: 4, name: 'Стріли', icon: '🏹', type: 'ammo', count: 15 }
])

// Лог бою
const combatLog = ref([])

// Додати повідомлення в лог
const addLog = (message, type = 'info') => {
  combatLog.value.unshift({ message, type, timestamp: Date.now() })
  if (combatLog.value.length > 10) combatLog.value.pop()
}

// *** СИСТЕМА ВОРОГІВ РІЗНОЇ СКЛАДНОСТІ ***

// Генерація ID для ворогів
let nextEnemyId = 1

// Фабрика створення ворогів різної складності
const createEnemy = (type, difficulty, x, y) => {
  const baseStats = {
    // Легкі вороги (рівень 1-2)
    goblin: { name: 'Гоблін', icon: '👺', baseHealth: 30, baseDamage: 5, baseArmor: 2, color: '#90EE90' },
    slime: { name: 'Слайм', icon: '🟢', baseHealth: 40, baseDamage: 3, baseArmor: 1, color: '#98FB98' },
    rat: { name: 'Щур', icon: '🐀', baseHealth: 20, baseDamage: 4, baseArmor: 1, color: '#DEB887' },
    
    // Середні вороги (рівень 3-4)
    orc: { name: 'Орк', icon: '👹', baseHealth: 60, baseDamage: 12, baseArmor: 5, color: '#CD5C5C' },
    skeleton: { name: 'Скелет', icon: '💀', baseHealth: 45, baseDamage: 10, baseArmor: 4, color: '#D3D3D3' },
    wolf: { name: 'Вовк', icon: '🐺', baseHealth: 50, baseDamage: 9, baseArmor: 3, color: '#A9A9A9' },
    
    // Важкі вороги (рівень 5)
    troll: { name: 'Троль', icon: '🗿', baseHealth: 100, baseDamage: 18, baseArmor: 8, color: '#8B4513' },
    demon: { name: 'Демон', icon: '👿', baseHealth: 85, baseDamage: 20, baseArmor: 7, color: '#DC143C' },
    dragon: { name: 'Дракон', icon: '🐉', baseHealth: 150, baseDamage: 30, baseArmor: 15, color: '#9400D3' }
  }
  
  const base = baseStats[type]
  const multiplier = difficulty * 0.5 // Чим вища складність, тим сильніший ворог
  
  return {
    id: nextEnemyId++,
    type,
    name: base.name,
    icon: base.icon,
    x,
    y,
    health: Math.floor(base.baseHealth * multiplier),
    maxHealth: Math.floor(base.baseHealth * multiplier),
    damage: Math.floor(base.baseDamage * multiplier),
    armor: Math.floor(base.baseArmor * multiplier),
    difficulty,
    difficultyLevel: difficulty, // 1-5
    experienceReward: base.baseHealth * difficulty,
    goldReward: base.baseDamage * difficulty * 2,
    specialAbilities: getSpecialAbilities(type, difficulty),
    color: base.color
  }
}

// Спеціальні здібності для складних ворогів
const getSpecialAbilities = (type, difficulty) => {
  const abilities = []
  if (difficulty >= 3) {
    abilities.push({ name: 'Критичний удар', chance: 0.1 + difficulty * 0.05 })
  }
  if (difficulty >= 4) {
    abilities.push({ name: 'Отрута', chance: 0.2 })
  }
  if (difficulty >= 5) {
    abilities.push({ name: 'Вогняне дихання', chance: 0.15 })
  }
  return abilities
}

// Список ворогів на карті
const enemies = ref([])

// Ініціалізація ворогів різної складності
const initEnemies = () => {
  enemies.value = [
    // Легкі вороги (difficulty 1)
    createEnemy('goblin', 1, 3, 3),
    createEnemy('rat', 1, 5, 2),
    createEnemy('slime', 1, 2, 5),
    createEnemy('goblin', 1, 7, 4),
    
    // Середні вороги (difficulty 2-3)
    createEnemy('skeleton', 2, 8, 8),
    createEnemy('wolf', 2, 4, 7),
    createEnemy('orc', 3, 9, 9),
    createEnemy('skeleton', 2, 6, 8),
    
    // Важкі вороги (difficulty 4-5)
    createEnemy('troll', 4, 12, 12),
    createEnemy('demon', 4, 14, 10),
    createEnemy('dragon', 5, 15, 15),
    
    // Елітний ворог з унікальним ім'ям
    { 
      ...createEnemy('demon', 5, 13, 13),
      name: 'Повелитель демонів',
      icon: '👾',
      health: 200,
      maxHealth: 200,
      specialAbilities: [...getSpecialAbilities('demon', 5), { name: 'Призив', chance: 0.25 }]
    }
  ]
}

// Фільтрація ворогів за позицією
const enemiesAt = (x, y) => {
  return enemies.value.filter(e => e.x === x && e.y === y && e.health > 0)
}

// *** КАРТА РІВНЯ ***

const mapWidth = 20
const mapHeight = 20
const tileSize = 60

const gridStyle = {
  display: 'grid',
  gridTemplateColumns: `repeat(${mapWidth}, ${tileSize}px)`
}

// Генерація карти з кімнатами та коридорами
const generateMap = () => {
  const map = []
  
  // Спочатку все заповнюємо стінами
  for (let y = 0; y < mapHeight; y++) {
    const row = []
    for (let x = 0; x < mapWidth; x++) {
      row.push({ type: 'wall' })
    }
    map.push(row)
  }
  
  // Створюємо кімнати
  const rooms = [
    { x: 1, y: 1, w: 5, h: 5 }, // Стартова кімната
    { x: 8, y: 2, w: 4, h: 4 }, // Кімната з легкими ворогами
    { x: 3, y: 8, w: 4, h: 4 }, // Кімната з середніми ворогами
    { x: 12, y: 10, w: 6, h: 6 }, // Кімната з босом
    { x: 14, y: 3, w: 3, h: 3 }, // Таємна кімната
    { x: 5, y: 13, w: 4, h: 4 }, // Кімната з скарбом
  ]
  
  // Вирізаємо кімнати
  rooms.forEach(room => {
    for (let y = room.y; y < room.y + room.h; y++) {
      for (let x = room.x; x < room.x + room.w; x++) {
        map[y][x] = { type: 'floor' }
      }
    }
  })
  
  // З'єднуємо кімнати коридорами
  for (let i = 0; i < rooms.length - 1; i++) {
    const room1 = rooms[i]
    const room2 = rooms[i + 1]
    
    // Горизонтальний коридор
    const startX = Math.min(room1.x + Math.floor(room1.w/2), room2.x + Math.floor(room2.w/2))
    const endX = Math.max(room1.x + Math.floor(room1.w/2), room2.x + Math.floor(room2.w/2))
    const y = room1.y + Math.floor(room1.h/2)
    
    for (let x = startX; x <= endX; x++) {
      map[y][x] = { type: 'floor' }
    }
    
    // Вертикальний коридор
    const startY = Math.min(room1.y + Math.floor(room1.h/2), room2.y + Math.floor(room2.h/2))
    const endY = Math.max(room1.y + Math.floor(room1.h/2), room2.y + Math.floor(room2.h/2))
    const x = room2.x + Math.floor(room2.w/2)
    
    for (let y = startY; y <= endY; y++) {
      map[y][x] = { type: 'floor' }
    }
  }
  
  // Додаємо спеціальні об'єкти
  // Скрині з скарбами
  map[3][4].item = { type: 'chest', icon: '📦', gold: 50, item: 'potion' }
  map[10][13].item = { type: 'chest', icon: '📦', gold: 100, item: 'sword' }
  map[14][14].item = { type: 'chest', icon: '📦', gold: 200, item: 'artifact' }
  
  // Двері
  map[5][8] = { type: 'door', locked: false, icon: '🚪' }
  map[8][12] = { type: 'door', locked: true, key: 'silver', icon: '🔒' }
  
  // Вода (декорації)
  map[7][15] = { type: 'water' }
  map[8][15] = { type: 'water' }
  map[7][16] = { type: 'water' }
  
  return map
}

const gameMap = ref(generateMap())

// Стилі для різних типів тайлів
const getTileStyle = (tile) => {
  const styles = {
    wall: { backgroundColor: '#4A4A4A' },
    floor: { backgroundColor: '#2D2D2D' },
    water: { backgroundColor: '#1E4B6E' },
    door: { backgroundColor: '#8B4513' },
    chest: { backgroundColor: '#FFD700' }
  }
  return styles[tile.type] || {}
}

// *** ІГРОВА ЛОГІКА ***

// Переміщення гравця
const movePlayer = (x, y) => {
  const tile = gameMap.value[y][x]
  
  // Перевірка чи можна пройти
  if (tile.type === 'wall') {
    addLog('Ви вперлися в стіну!', 'error')
    return
  }
  
  if (tile.type === 'door') {
    if (tile.locked) {
      addLog('Двері зачинені! Потрібен ключ.', 'warning')
      return
    }
  }
  
  // Перевірка на ворогів
  const enemiesHere = enemiesAt(x, y)
  if (enemiesHere.length > 0 && enemiesHere.some(e => e.health > 0)) {
    addLog('Шлях блокують вороги!', 'warning')
    return
  }
  
  // Оновлюємо позицію
  player.x = x
  player.y = y
  
  // Перевіряємо події на клітинці
  checkTileEvents(x, y)
}

// Атака ворога
const attackEnemy = (enemy) => {
  // Перевірка чи живий ворог
  if (enemy.health <= 0) {
    addLog('Ворог вже переможений!', 'info')
    return
  }
  
  // Розрахунок шкоди
  const playerDamage = player.strength + (inventory.value.find(i => i.type === 'weapon' && i.equipped)?.damage || 0)
  const enemyArmor = enemy.armor
  let damage = Math.max(1, playerDamage - enemyArmor)
  
  // Шанс критичного удару
  const isCritical = Math.random() < 0.1
  if (isCritical) {
    damage *= 2
    addLog(`КРИТИЧНИЙ УДАР!`, 'critical')
  }
  
  // Застосування шкоди
  enemy.health -= damage
  addLog(`Ви завдали ${damage} шкоди ${enemy.name}`, 'damage')
  
  // Перевірка смерті ворога
  if (enemy.health <= 0) {
    // Нагорода
    player.exp += enemy.experienceReward
    player.gold += enemy.goldReward
    
    addLog(`🎉 ${enemy.name} переможений! Отримано: ${enemy.experienceReward} досвіду, ${enemy.goldReward} золота`, 'victory')
    
    // Перевірка підвищення рівня
    if (player.exp >= player.nextLevelExp) {
      levelUp()
    }
    
    return
  }
  
  // Контратака ворога
  setTimeout(() => enemyAttack(enemy), 500)
}

// Контратака ворога
const enemyAttack = (enemy) => {
  if (enemy.health <= 0) return
  
  const enemyDamage = enemy.damage
  const playerArmor = player.defense + (inventory.value.find(i => i.type === 'armor' && i.equipped)?.defense || 0)
  let damage = Math.max(1, enemyDamage - playerArmor)
  
  // Спеціальні здібності ворога
  enemy.specialAbilities?.forEach(ability => {
    if (Math.random() < ability.chance) {
      if (ability.name === 'Критичний удар') {
        damage *= 1.5
        addLog(`${enemy.name} застосовує ${ability.name}!`, 'enemy-special')
      } else if (ability.name === 'Отрута') {
        player.health -= 5
        addLog(`${enemy.name} отруїв вас! -5 HP`, 'poison')
      }
    }
  })
  
  player.health -= damage
  addLog(`${enemy.name} завдає вам ${damage} шкоди`, 'enemy-damage')
  
  // Перевірка смерті гравця
  if (player.health <= 0) {
    player.health = 0
    addLog('💀 Ви загинули... Гра закінчена', 'death')
    // Тут можна додати логіку перезапуску
  }
}

// Підвищення рівня
const levelUp = () => {
  player.level++
  player.maxHealth += 20
  player.health = player.maxHealth
  player.strength += 5
  player.defense += 3
  player.nextLevelExp = Math.floor(player.nextLevelExp * 1.5)
  
  addLog(`✨ РІВЕНЬ ПІДВИЩЕНО! Ви досягли ${player.level} рівня!`, 'level-up')
}

// Використання предмета
const useItem = (item) => {
  if (item.type === 'potion' && item.count > 0) {
    player.health = Math.min(player.maxHealth, player.health + item.heal)
    item.count--
    addLog(`Ви використали ${item.name} +${item.heal} HP`, 'heal')
    
    if (item.count === 0) {
      inventory.value = inventory.value.filter(i => i.id !== item.id)
    }
  } else if (item.type === 'weapon' || item.type === 'armor') {
    // Знімаємо екіпіровку з усіх предметів цього типу
    inventory.value.forEach(i => {
      if (i.type === item.type) i.equipped = false
    })
    // Екіпіруємо вибраний предмет
    item.equipped = true
    addLog(`Ви екіпірували ${item.name}`, 'equip')
  }
}

// Підбір предмета
const pickupItem = (x, y) => {
  const tile = gameMap.value[y][x]
  if (tile.item) {
    if (tile.item.type === 'chest') {
      player.gold += tile.item.gold
      addLog(`Ви знайшли ${tile.item.gold} золота!`, 'treasure')
      
      // Додаємо предмет в інвентар якщо є
      if (tile.item.item === 'potion') {
        const potion = inventory.value.find(i => i.name === 'Зілля здоров\'я')
        if (potion) potion.count++
        else {
          inventory.value.push({ 
            id: Date.now(), 
            name: 'Зілля здоров\'я', 
            icon: '🧪', 
            type: 'potion', 
            heal: 30, 
            count: 1 
          })
        }
      }
    }
    delete tile.item
  }
}

// Перевірка подій на клітинці
const checkTileEvents = (x, y) => {
  const tile = gameMap.value[y][x]
  
  if (tile.type === 'door' && !tile.locked) {
    addLog('Ви відчинили двері', 'info')
  }
  
  // Автоматичний підбір предметів
  if (tile.item) {
    pickupItem(x, y)
  }
}

// Ціль для атаки
const targetEnemy = (enemy) => {
  if (enemy.health > 0) {
    // Підрахунок відстані
    const distance = Math.abs(player.x - enemy.x) + Math.abs(player.y - enemy.y)
    
    if (distance <= 1) {
      attackEnemy(enemy)
    } else {
      addLog(`${enemy.name} занадто далеко (${distance} клітинок)`, 'warning')
    }
  }
}

// Ініціалізація
onMounted(() => {
  initEnemies()
  addLog('Ласкаво просимо до підземелля!', 'welcome')
  addLog('Ваше завдання: перемогти всіх ворогів', 'info')
})
</script>

<style scoped>
.rpg-level {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  background: #1a1a1a;
  color: white;
  font-family: 'Arial', sans-serif;
}

.player-hud {
  background: #2a2a2a;
  border-radius: 10px;
  padding: 15px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 30px;
}

.player-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.stat {
  background: #333;
  padding: 5px 10px;
  border-radius: 5px;
  font-weight: bold;
}

.health-bar {
  flex: 1;
  height: 20px;
  background: #333;
  border-radius: 10px;
  overflow: hidden;
}

.health-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  transition: width 0.3s;
}

.inventory {
  display: flex;
  gap: 5px;
}

.inventory-slot {
  width: 50px;
  height: 50px;
  background: #333;
  border: 2px solid #444;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  position: relative;
  cursor: pointer;
}

.inventory-slot.equipped {
  border-color: #FFD700;
  box-shadow: 0 0 10px gold;
}

.item-count {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: #FF4444;
  color: white;
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 3px;
}

.game-area {
  display: flex;
  gap: 20px;
}

.game-grid {
  display: grid;
  gap: 2px;
  background: #333;
  padding: 2px;
}

.grid-cell {
  width: 60px;
  height: 60px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.grid-cell:hover {
  filter: brightness(1.2);
  transform: scale(1.02);
}

.wall {
  background: #4A4A4A;
  background-image: repeating-linear-gradient(45deg, #5A5A5A 0px, #5A5A5A 2px, #4A4A4A 2px, #4A4A4A 4px);
}

.floor {
  background: #2D2D2D;
}

.water {
  background: #1E4B6E;
  animation: waterRipple 2s infinite;
}

@keyframes waterRipple {
  0% { background: #1E4B6E; }
  50% { background: #2A5F8A; }
  100% { background: #1E4B6E; }
}

.entity {
  position: absolute;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.player {
  font-size: 32px;
  filter: drop-shadow(0 0 5px gold);
  animation: playerIdle 1s infinite;
}

@keyframes playerIdle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}

.enemy {
  font-size: 28px;
  cursor: pointer;
  position: relative;
}

.enemy:hover {
  transform: scale(1.1);
  filter: drop-shadow(0 0 5px red);
}

.enemy-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  border: 2px solid #444;
  border-radius: 5px;
  padding: 8px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 100;
  display: none;
}

.enemy:hover .enemy-tooltip {
  display: block;
}

/* Різні кольори для різних рівнів складності */
.difficulty-1 { color: #90EE90; } /* Зелений - легкий */
.difficulty-2 { color: #FFD700; } /* Жовтий - середній */
.difficulty-3 { color: #FFA500; } /* Помаранчевий - складний */
.difficulty-4 { color: #FF6347; } /* Червоний - дуже складний */
.difficulty-5 { color: #9400D3; } /* Фіолетовий - бос */

.enemy-panel {
  width: 250px;
  background: #2a2a2a;
  border-radius: 10px;
  padding: 15px;
  overflow-y: auto;
  max-height: 600px;
}

.enemy-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin-bottom: 10px;
  background: #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.enemy-card:hover {
  background: #444;
  transform: translateX(5px);
}

.enemy-icon {
  font-size: 32px;
}

.enemy-info {
  flex: 1;
}

.enemy-name {
  font-weight: bold;
  margin-bottom: 3px;
}

.enemy-stats {
  font-size: 12px;
  display: flex;
  gap: 8px;
  color: #aaa;
}

.enemy-difficulty {
  margin-top: 3px;
}

.empty-star {
  color: #444;
}

.combat-log {
  margin-top: 20px;
  background: #2a2a2a;
  border-radius: 10px;
  padding: 10px;
  height: 100px;
  overflow-y: auto;
  font-size: 12px;
}

.combat-log > div {
  padding: 2px 0;
}

.log-damage { color: #FF6B6B; }
.log-enemy-damage { color: #FFA500; }
.log-heal { color: #4CAF50; }
.log-critical { color: #FFD700; font-weight: bold; }
.log-victory { color: #4CAF50; font-weight: bold; }
.log-level-up { color: #9B59B6; font-weight: bold; }
.log-warning { color: #FFA500; }
.log-error { color: #FF4444; }
.log-treasure { color: #FFD700; }
.log-poison { color: #9B59B6; }
.log-equip { color: #87CEEB; }
.log-welcome { color: #4CAF50; font-size: 14px; }
</style>