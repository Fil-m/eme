# EME OS Developer Guide for AI Agents

## Core Principles
1. **Framework**: Vue.js 3 with SFC (Single File Components).
2. **Styling**: Bootstrap 5 + Custom EME variables.
3. **Props**: All components receive `user` (object) and `auth` (function).
   - Use `headers: props.auth()` for all fetch requests.

## UI Components & Styles
- Root class: `eme-app-page`
- Titles: `eme-app-title`
- Cards: Use `.card.bg-dark.border-secondary`
- Colors:
  - Cyan Accent: `var(--eme-accent)` (#00e5ff)
  - Gradient: `var(--eme-grad)` (Cyan to Blue)
  - Text: `var(--tblr-body-color)` or white/muted.

## Common API Endpoints
- **Memos**: `/api/utils/memos/` (POST {content: string}, GET returns list)
- **Media**: 
  - Upload: `/api/media/files/bulk-upload/` (POST FormData with 'files')
  - List: `/api/media/files/`
- **Profiles**: `/api/profiles/me/`
- **Settings**: `/api/settings/me/`

## Standard Code Patterns
### Fetching Data
```javascript
const res = await fetch('/api/endpoint/', { headers: props.auth() });
const data = await res.json();
```

### Composition API Setup
```javascript
export default {
  props: ['user', 'auth'],
  setup(props) {
    const data = ref([]);
    // ... logic
    return { data };
  }
}
```

### Handling Files
```html
<input type="file" ref="fileInput" @change="onFileChange">
```
```javascript
const onFileChange = (e) => {
  const file = e.target.files[0];
  // use FileReader or FormData
};
```

## NO-GO Zones
- Do NOT use plain colors (red/blue). Use curated Bootstrap or EME classes.
- Do NOT forget to return variables from `setup()`.
- Do NOT use `index.html` direct imports. Use `import { ... } from 'vue'`.
- Always check if `ref.value` is null before using it.
