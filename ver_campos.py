import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from atendimentos.models import TipoServico, CampoServico

for tipo in TipoServico.objects.all().order_by('ordem'):
    campos = CampoServico.objects.filter(tipo_servico=tipo).order_by('ordem')
    print('')
    print('=' * 60)
    print(f'  {tipo.nome.upper()} ({tipo.codigo})')
    print(f'  Cor: {tipo.cor} | Categoria: {tipo.categoria}')
    print('=' * 60)

    secao_atual = None
    for campo in campos:
        if campo.secao != secao_atual:
            secao_atual = campo.secao
            print(f'\n  [{secao_atual}]')

        obrig = '*' if campo.obrigatorio else ' '

        opcoes = ''
        if campo.opcoes:
            opcoes = f' -> {campo.opcoes}'

        print(f'    {obrig} {campo.nome} ({campo.tipo_campo}){opcoes}')
