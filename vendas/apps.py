from django.apps import AppConfig


class VendasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendas'
    verbose_name = 'Gestão de Vendas'

    def ready(self):
        """Registra signals de integração com Estoque."""
        import vendas.signals  # noqa: F401
