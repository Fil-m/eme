<template>
  <div class="eme-app-page">
    <eme-app-title>Завантаження нотатків</eme-app-title>
    <div class="row mt-3">
      <div class="col-md-8 offset-md-2">
        <input type="file" ref="fileInput" @change="onFileChange">
        <div v-if="selectedFile" class="card bg-dark border-secondary mt-3">
          <img :src="selectedFile" alt="Завантажений файл" class="card-img-top">
          <div class="card-body text-white">
            <p>Завантажений файл: {{ selectedFile }}</p>
          </div>
        </div>
        <div v-else class="card bg-dark border-secondary mt-3">
          <p>Виберите файл</p>
        </div>
      </div>
    </div>
    <div class="mt-3">
      <eme-app-title>Нотатки</eme-app-title>
      <div class="card bg-dark border-secondary mt-3">
        <p class="text-white">Текстова інформація</p>
        <div>
          <p>{{ noteContent }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';

export default {
  props: ['user', 'auth'],
  setup(props) {
    const selectedFile = ref(null);
    const noteContent = ref('');

    const onFileChange = async (e) => {
      const file = e.target.files[0];
      selectedFile.value = URL.createObjectURL(file);
      // Upload file to server
      const formData = new FormData();
      formData.append('files', file);
      const res = await fetch('/api/media/files/bulk-upload/', {
        method: 'POST',
        body: formData,
        headers: props.auth(),
      });
      const data = await res.json();
      noteContent.value = data.noteContent;
    };

    onMounted(async () => {
      const res = await fetch('/api/utils/memos/', {
        headers: props.auth(),
      });
      const data = await res.json();
      noteContent.value = data.noteContent;
    });

    return { selectedFile, noteContent };
  },
};
</script>

<style>
  .eme-app-page {
    padding: 20px;
    background-color: var(--tblr-body-color);
  }

  .eme-app-title {
    color: var(--eme-accent);
    font-size: 24px;
  }

  .card.bg-dark.border-secondary {
    border: 1px solid var(--eme-accent);
    box-shadow: 0 0 10px var(--eme-accent);
  }

  .card-img-top {
    width: 100%;
    height: 200px;
    object-fit: cover;
  }

  .card-body {
    padding: 20px;
  }

  .mt-3 {
    margin-top: 20px;
  }
</style>