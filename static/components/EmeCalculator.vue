<template>
  <div class="eme-app-page">
    <eme-app-title>Cal</eme-app-title>

    <div class="row">
      <div class="col">
        <input type="text" v-model="expression" @keydown.enter="equals">
      </div>
      <div class="col">
        <button @click="clear">Clear</button>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <button @click="backspace">Backspace</button>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <button @click="add">+</button>
        <button @click="subtract">-</button>
        <button @click="multiply">*</button>
        <button @click="divide">/</button>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <button @click="equals">=</button>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <p>Result: {{ result }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue"

export default {
  setup() {
    const expression = ref("")
    const result = ref("")

    const clear = () => {
      expression.value = ""
      result.value = ""
    }

    const backspace = () => {
      expression.value = expression.value.slice(0, -1)
    }

    const add = () => expression.value += "+"
    const subtract = () => expression.value += "-"
    const multiply = () => expression.value += "*"
    const divide = () => expression.value += "/"

    const equals = () => {
      try {
        result.value = eval(expression.value)
      } catch {
        result.value = "Error"
      }
    }

    return {
      expression,
      result,
      clear,
      backspace,
      add,
      subtract,
      multiply,
      divide,
      equals
    }
  }
}
</script>