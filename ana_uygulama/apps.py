from django.apps import AppConfig


class AnaUygulamaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ana_uygulama'
    def ready(self):
        """
        Uygulama hazır olduğunda sinyalleri import eder.
        """
        import ana_uygulama.signals