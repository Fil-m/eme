<template>
  <div class="eme-app-page">
    <h1 class="text-center">Notatki</h1>
    <div class="row mt-4">
      <div class="col-md-6">
        <img src="" alt="" class="img-fluid w-100">
      </div>
      <div class="col-md-6">
        <div class="card mt-4">
          <div class="card-body">
            <textarea class="form-control" rows="10" placeholder="Tekst notatki"></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  setup() {
    const fileInput = ref(null);
    const file = ref(null);
    const text = ref('');
    const image = ref(null);

    onMounted(() => {
      fileInput.value.addEventListener('change', (e) => {
        file.value = e.target.files[0];
      });
    });

    const loadFile = () => {
      if (file.value) {
        const reader = new FileReader();
        reader.onload = (e) => {
          image.value = e.target.result;
        };
        reader.readAsDataURL(file.value);
      }
    };

    const saveText = () => {
      text.value = textarea.value;
    };

    return {
      fileInput,
      file,
      text,
      image,
      loadFile,
      saveText,
    };
  },
};
</script>

<style>
.eme-app-page {
  padding: 20px;
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 10px;
}

.card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.card-body {
  padding: 20px;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
</style>