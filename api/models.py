"""
=============================================================================
LIFE RAINBOW 2.0 - Perfis de Usuário
Model: UserProfile (extensão do User do Django)
=============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Perfil estendido do usuário com controle de acesso por role.

    Roles:
    - admin: Acesso total ao sistema
    - comercial: Clientes, Vendas, Aluguéis, Agenda, Equipamentos, OS
    - tecnico: OS, Equipamentos, Agenda
    - financeiro: Financeiro, Contas
    - gerente: Relatórios, Dashboards
    """

    ROLE_ADMIN = 'admin'
    ROLE_COMERCIAL = 'comercial'
    ROLE_TECNICO = 'tecnico'
    ROLE_FINANCEIRO = 'financeiro'
    ROLE_GERENTE = 'gerente'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrador'),
        (ROLE_COMERCIAL, 'Comercial'),
        (ROLE_TECNICO, 'Técnico'),
        (ROLE_FINANCEIRO, 'Financeiro'),
        (ROLE_GERENTE, 'Gerente'),
    ]

    # Permissões por módulo para cada role
    ROLE_PERMISSIONS = {
        ROLE_ADMIN: {
            'dashboard': True,
            'clientes': True,
            'vendas': True,
            'alugueis': True,
            'agenda': True,
            'equipamentos': True,
            'assistencia': True,
            'financeiro': True,
            'whatsapp': True,
            'ai_assistant': True,
            'configuracoes': True,
        },
        ROLE_COMERCIAL: {
            'dashboard': True,
            'clientes': True,
            'vendas': True,
            'alugueis': True,
            'agenda': True,
            'equipamentos': True,
            'assistencia': True,
            'financeiro': False,      # Bloqueado
            'whatsapp': False,        # Bloqueado
            'ai_assistant': False,    # Bloqueado
            'configuracoes': False,   # Bloqueado
        },
        ROLE_TECNICO: {
            'dashboard': True,
            'clientes': False,
            'vendas': False,
            'alugueis': False,
            'agenda': True,
            'equipamentos': True,
            'assistencia': True,
            'financeiro': False,
            'whatsapp': False,
            'ai_assistant': False,
            'configuracoes': False,
        },
        ROLE_FINANCEIRO: {
            'dashboard': True,
            'clientes': False,
            'vendas': False,
            'alugueis': False,
            'agenda': False,
            'equipamentos': False,
            'assistencia': False,
            'financeiro': True,
            'whatsapp': False,
            'ai_assistant': False,
            'configuracoes': False,
        },
        ROLE_GERENTE: {
            'dashboard': True,
            'clientes': True,
            'vendas': True,
            'alugueis': True,
            'agenda': True,
            'equipamentos': True,
            'assistencia': True,
            'financeiro': True,
            'whatsapp': True,
            'ai_assistant': True,
            'configuracoes': False,
        },
    }

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuário'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_COMERCIAL,
        verbose_name='Perfil',
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        db_table = 'api_userprofile'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def permissions(self):
        """Retorna as permissões baseadas no role."""
        return self.ROLE_PERMISSIONS.get(self.role, self.ROLE_PERMISSIONS[self.ROLE_COMERCIAL])

    def has_permission(self, module: str) -> bool:
        """Verifica se o usuário tem permissão para um módulo específico."""
        return self.permissions.get(module, False)

    def get_allowed_modules(self) -> list:
        """Retorna lista de módulos permitidos."""
        return [module for module, allowed in self.permissions.items() if allowed]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria um perfil automaticamente quando um usuário é criado."""
    if created:
        # Superusers e staff são admin por padrão
        role = UserProfile.ROLE_ADMIN if (instance.is_superuser or instance.is_staff) else UserProfile.ROLE_COMERCIAL
        UserProfile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Garante que o perfil existe e é salvo."""
    if not hasattr(instance, 'profile'):
        role = UserProfile.ROLE_ADMIN if (instance.is_superuser or instance.is_staff) else UserProfile.ROLE_COMERCIAL
        UserProfile.objects.create(user=instance, role=role)
