from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.utils import timezone


VALOR_MULTA_POR_DIA = Decimal("2.00")


class Autor(models.Model):
    nome = models.CharField(max_length=150)
    nacionalidade = models.CharField(max_length=80)
    data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    titulo = models.CharField(max_length=200)
    autor = models.ForeignKey(
        Autor,
        on_delete=models.CASCADE,
        related_name="livros",
    )
    isbn = models.CharField(max_length=20, unique=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    copias_totais = models.PositiveIntegerField()
    copias_disponiveis = models.PositiveIntegerField()
    capa = models.CharField(
        max_length=255,
        blank=True,
        help_text="Caminho de uma imagem em biblioteca/static/.",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(copias_disponiveis__lte=models.F("copias_totais")),
                name="copias_disponiveis_nao_excedem_total",
            )
        ]

    def __str__(self):
        return self.titulo


class Membro(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Emprestimo(models.Model):
    STATUS_CHOICES = [
        ("ATIVO", "Ativo"),
        ("DEVOLVIDO", "Devolvido"),
        ("ATRASADO", "Atrasado"),
    ]

    livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    membro = models.ForeignKey(Membro, on_delete=models.CASCADE)
    data_emprestimo = models.DateField(auto_now_add=True)
    data_prevista_devolucao = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ATIVO")

    @property
    def esta_atrasado(self):
        return (
            self.status == "ATIVO"
            and self.data_prevista_devolucao is not None
            and self.data_prevista_devolucao < timezone.localdate()
        )

    @property
    def dias_atraso(self):
        if self.status == "DEVOLVIDO":
            data_final = self.data_devolucao
        elif self.status in ("ATIVO", "ATRASADO"):
            data_final = timezone.localdate()
        else:
            return 0

        if data_final is None:
            return 0

        if self.data_prevista_devolucao is None:
            return 0

        return max((data_final - self.data_prevista_devolucao).days, 0)

    @property
    def multa(self):
        return VALOR_MULTA_POR_DIA * self.dias_atraso

    def __str__(self):
        return f"{self.membro} → {self.livro}"
