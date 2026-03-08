<template>
  <div class="eme-app-page">
    <div class="card bg-dark border-secondary">
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <h2 class="eme-app-title">Game: Snake</h2>
          </div>
          <div class="col-md-6 text-end">
            <button @click="newGame">New Game</button>
          </div>
        </div>
        <div class="row mt-4" v-if="game">
          <div class="col-md-12">
            <canvas id="snakeCanvas" width="600" height="400"></canvas>
          </div>
        </div>
        <div class="row mt-4" v-if="game">
          <div class="col-md-12">
            <p>Score: {{ score }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Canvas } from 'vue-canvas';

const game = ref(false);
const score = ref(0);

const newGame = async () => {
  game.value = false;
  score.value = 0;
};

onMounted(async () => {
  await newGame();
});
</script>

<style>
  #snakeCanvas {
    border: 1px solid var(--tblr-body-color);
  }
</style>