from django.apps import AppConfig


class AlugueisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'alugueis'
    verbose_name = 'Gestão de Aluguéis'

    def ready(self):
        """Registra signals de integração com Financeiro."""
        import alugueis.signals  # noqa: F401
