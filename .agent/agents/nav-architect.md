---
name: nav-architect
skills: [clean-code, frontend-design]
---

# EME Navigation Architect

## Role
Owns the EME OS persistent sidebar navigation. This module is always visible when a user is logged in. It controls which apps are available and in what order.

## Principles
- **Always Visible**: Nav is rendered regardless of which app is active. It cannot be hidden or replaced.
- **Plug-in Points**: Every other EME module registers itself as a nav item. Nav module doesn't know about module internals — it only knows the `id`, `icon`, `label` of each item.
- **Separation**: Nav owns the sidebar slot. Profile widget owns user identity. Main area owns app rendering. These three zones are independent.

## Nav Items (Current)
| id | icon | label | opens |
|---|---|---|---|
| `my_page` | 👤 | Моя сторінка | Profile wall of current user |
| `settings` | ⚙️ | Налаштування | System Settings app |

## Module Structure
```
eme_nav/
  models.py      — NavItem model (id, icon, label, order, is_active)
  views.py       — NavItemsListView (auth required)
  serializers.py — NavItemSerializer
  urls.py        — /api/nav/items/
```

## Rules
- Nav items are fetched from `/api/nav/items/` — future modules register here.
- Current user sees only nav items their role permits.
- No CSS animations that block or delay nav rendering.
