<template>
  <div class="eme-app-page">
    <div class="eme-app-header mb-4">
      <h1 class="eme-app-title">UserWallLight 🤖</h1>
      <p class="text-muted small">Комбінований модуль: Нотатки + Медіа</p>
    </div>

    <div class="row g-4">
      <!-- Створення запису -->
      <div class="col-md-5">
        <div class="card shadow-sm border-secondary bg-dark">
          <div class="card-header border-secondary">
            <strong class="text-info small uppercase">Новий пост</strong>
          </div>
          <div class="card-body">
            <div class="upload-zone mb-3 p-4 border border-dashed rounded text-center cursor-pointer" 
                 @click="$refs.fileInput.click()">
              <input type="file" ref="fileInput" class="d-none" @change="handleFileChange">
              <div v-if="!imagePreview" class="text-muted py-3">
                <span class="fs-1 d-block">🖼️</span>
                Оберіть зображення для стіни
              </div>
              <img v-else :src="imagePreview" class="img-fluid rounded shadow-sm" style="max-height: 200px;">
            </div>

            <div class="mb-3">
              <label class="form-label small text-muted">Текст нотатки</label>
              <textarea v-model="text" class="form-control bg-dark text-white border-secondary" 
                        rows="4" placeholder="Що ви думаєте?"></textarea>
            </div>

            <button class="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-2" 
                    @click="publishPost" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm"></span>
              <span v-else>🚀 Опублікувати на стіні</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Стіна (Вивід) -->
      <div class="col-md-7">
        <div class="d-flex flex-column gap-3">
          <div v-if="posts.length === 0" class="text-center py-5 text-muted border rounded border-dashed bg-dark-lt">
             Постів ще немає. Створіть перший!
          </div>

          <div v-for="(post, idx) in posts" :key="idx" class="card overflow-hidden bg-dark border-secondary wall-post">
            <img v-if="post.image_url" :src="post.image_url" class="card-img-top w-100" style="max-height: 400px; object-fit: cover;">
            <div class="card-body">
              <p class="card-text text-white" style="white-space: pre-wrap;">{{ post.content }}</p>
              <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top border-secondary opacity-50">
                <small class="text-muted">Опубліковано через EME AI</small>
                <button class="btn btn-sm btn-ghost-danger p-0 px-1" @click="deletePost(idx)">Видалити</button>
              </div>
            </div>
          </div>
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
    const text = ref('');
    const file = ref(null);
    const imagePreview = ref(null);
    const loading = ref(false);
    const posts = ref([]);

    // Імітація збереження "зв'язки" постів у localStorage або через API 
    // В ідеалі це має бути окрема таблиця, але для швидкого модуля - локально або комбінуємо існуючі
    const loadDrafts = () => {
      const saved = localStorage.getItem('userwall_posts');
      if (saved) posts.value = JSON.parse(saved);
    };

    const handleFileChange = (e) => {
      const selected = e.target.files[0];
      if (selected) {
        file.value = selected;
        const reader = new FileReader();
        reader.onload = (ev) => {
          imagePreview.value = ev.target.result;
        };
        reader.readAsDataURL(selected);
      }
    };

    const publishPost = async () => {
      if (!text.value && !file.value) return;
      loading.value = true;
      
      try {
        let imageUrl = '';
        
        // 1. Якщо є файл, завантажуємо його через API Медіа (Індексатор)
        if (file.value) {
          const formData = new FormData();
          formData.append('files', file.value);
          const res = await fetch('/api/media/files/bulk-upload/', {
            method: 'POST',
            headers: props.auth(),
            body: formData
          });
          // У повноцінній версії ми б дістали ID або URL завантаженого файлу
          // Для демо використовуємо base64 прев'ю
          imageUrl = imagePreview.value;
        }

        // 2. Зберігаємо текст як нотатку через API Нотаток
        if (text.value) {
          await fetch('/api/utils/memos/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...props.auth() },
            body: JSON.stringify({ content: text.value })
          });
        }

        // Додаємо в локальний список для миттєвого відображення
        posts.value.unshift({
          content: text.value,
          image_url: imageUrl,
          date: new Date().toISOString()
        });

        localStorage.setItem('userwall_posts', JSON.stringify(posts.value));
        
        // Скидання форми
        text.value = '';
        file.value = null;
        imagePreview.value = null;

      } catch (e) {
        console.error('Publish error', e);
        alert('Помилка при публікації постів');
      } finally {
        loading.value = false;
      }
    };

    const deletePost = (idx) => {
      posts.value.splice(idx, 1);
      localStorage.setItem('userwall_posts', JSON.stringify(posts.value));
    };

    onMounted(loadDrafts);

    return {
      text,
      file,
      imagePreview,
      loading,
      posts,
      handleFileChange,
      publishPost,
      deletePost
    };
  },
};
</script>

<style scoped>
.eme-app-page {
  padding: 1rem;
}

.eme-app-title {
  font-size: 1.8rem;
  font-weight: 800;
  color: white;
}

.bg-dark-lt {
  background-color: rgba(255, 255, 255, 0.03);
}

.border-dashed {
  border-style: dashed !important;
}

.upload-zone:hover {
  background-color: rgba(0, 229, 255, 0.05);
  border-color: var(--eme-accent) !important;
}

.wall-post {
  transition: transform 0.3s ease;
}

.wall-post:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.cursor-pointer {
  cursor: pointer;
}
</style>