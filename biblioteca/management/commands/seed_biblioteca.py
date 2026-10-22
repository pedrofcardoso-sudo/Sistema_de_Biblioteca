from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from biblioteca.models import Autor, Emprestimo, Livro, Membro


LIVROS_DEMONSTRACAO = (
    {
        "titulo": "Dom Casmurro",
        "autor": "Machado de Assis",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-001",
        "preco": Decimal("34.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/dom-casmurro.svg",
    },
    {
        "titulo": "Memórias Póstumas de Brás Cubas",
        "autor": "Machado de Assis",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-002",
        "preco": Decimal("39.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/memorias-postumas.svg",
    },
    {
        "titulo": "O Cortiço",
        "autor": "Aluísio Azevedo",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-003",
        "preco": Decimal("29.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/o-cortico.svg",
    },
    {
        "titulo": "O Guarani",
        "autor": "José de Alencar",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-004",
        "preco": Decimal("32.50"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/o-guarani.svg",
    },
    {
        "titulo": "A Moreninha",
        "autor": "Joaquim Manuel de Macedo",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-005",
        "preco": Decimal("27.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/a-moreninha.svg",
    },
    {
        "titulo": "O Alienista",
        "autor": "Machado de Assis",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-006",
        "preco": Decimal("24.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/o-alienista.svg",
    },
    {
        "titulo": "Triste Fim de Policarpo Quaresma",
        "autor": "Lima Barreto",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-007",
        "preco": Decimal("36.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/policarpo-quaresma.svg",
    },
    {
        "titulo": "O Ateneu",
        "autor": "Raul Pompeia",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-008",
        "preco": Decimal("31.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/o-ateneu.svg",
    },
    {
        "titulo": "A Escrava Isaura",
        "autor": "Bernardo Guimarães",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-009",
        "preco": Decimal("28.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/a-escrava-isaura.svg",
    },
    {
        "titulo": "Memórias de um Sargento de Milícias",
        "autor": "Manuel Antônio de Almeida",
        "nacionalidade": "Brasileira",
        "isbn": "DEMO-IESB-010",
        "preco": Decimal("33.90"),
        "copias_totais": 10,
        "copias_disponiveis": 10,
        "capa": "biblioteca/capas/sargento-de-milicias.svg",
    },
)

MEMBROS_DEMONSTRACAO = (
    ("Ana Silva", "ana@example.com"),
    ("Bruno Costa", "bruno@example.com"),
    ("Carla Souza", "carla@example.com"),
    ("Daniel Oliveira", "daniel@example.com"),
    ("Eduarda Lima", "eduarda@example.com"),
    ("Felipe Santos", "felipe@example.com"),
)


class Command(BaseCommand):
    help = "Cadastra livros, autores e membros de demonstração sem duplicá-los."

    @transaction.atomic
    def handle(self, *args, **options):
        livros_criados = 0
        livros_atualizados = 0
        for dados in LIVROS_DEMONSTRACAO:
            autor, _ = Autor.objects.get_or_create(
                nome=dados["autor"],
                defaults={"nacionalidade": dados["nacionalidade"]},
            )
            livro, criado = Livro.objects.get_or_create(
                isbn=dados["isbn"],
                defaults={
                    "titulo": dados["titulo"],
                    "autor": autor,
                    "preco": dados["preco"],
                    "copias_totais": dados["copias_totais"],
                    "copias_disponiveis": dados["copias_disponiveis"],
                    "capa": dados["capa"],
                },
            )
            emprestimos_ativos = Emprestimo.objects.filter(
                livro=livro,
                status__in=("ATIVO", "ATRASADO"),
            ).count()
            if emprestimos_ativos > dados["copias_totais"]:
                raise ValueError(
                    f'O livro "{dados["titulo"]}" tem mais empréstimos ativos '
                    "do que cópias previstas no catálogo de demonstração."
                )
            livro.titulo = dados["titulo"]
            livro.autor = autor
            livro.preco = dados["preco"]
            livro.copias_totais = dados["copias_totais"]
            livro.copias_disponiveis = dados["copias_totais"] - emprestimos_ativos
            livro.capa = dados["capa"]
            livro.save()
            livros_criados += int(criado)
            livros_atualizados += int(not criado)

        membros_criados = 0
        for nome, email in MEMBROS_DEMONSTRACAO:
            _, criado = Membro.objects.get_or_create(
                email=email,
                defaults={"nome": nome},
            )
            membros_criados += int(criado)

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo pronto: {len(LIVROS_DEMONSTRACAO)} livros "
                f"({livros_criados} novos, {livros_atualizados} atualizados), "
                f"{membros_criados} membros novos e "
                f"{len(MEMBROS_DEMONSTRACAO)} membros no total. "
                "O estoque disponível considera os empréstimos ativos."
            )
        )
