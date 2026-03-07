class ModuleRouter:
    """
    Роутер, який направляє запити відокремлених модулів у власні бази даних.
    Всі інші додатки використовують 'default'.
    """

    route_mapping = {
        'eme_kb': 'kb',
        'eme_media': 'media',
        'eme_ai': 'ai',
        'projects': 'kanban',
        'park_adventures': 'game',
        'park_adventures': 'game',
        'eme_chat': 'social',
        'eme_mafia': 'mafia',
        'eme_utils': 'utils',
    }

    def db_for_read(self, model, **hints):
        return self.route_mapping.get(model._meta.app_label, 'default')

    def db_for_write(self, model, **hints):
        return self.route_mapping.get(model._meta.app_label, 'default')

    def allow_relation(self, obj1, obj2, **hints):
        # Дозволяємо зв'язки, оскільки ми знімаємо db_constraint
        app1 = obj1._meta.app_label
        app2 = obj2._meta.app_label
        if app1 in self.route_mapping or app2 in self.route_mapping:
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        target_db = self.route_mapping.get(app_label)
        if target_db:
            return db == target_db
        # Всі інші додатки мігруються лише в default
        if db in self.route_mapping.values():
            return False
        return db == 'default'
