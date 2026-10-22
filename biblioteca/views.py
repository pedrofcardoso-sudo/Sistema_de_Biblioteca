from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Emprestimo, Livro, Membro


class EstoqueInconsistenteError(Exception):
    pass


def lista_livros(request):
    livros = Livro.objects.select_related("autor").order_by("titulo")
    membros = Membro.objects.order_by("nome")
    return render(
        request,
        "biblioteca/lista_livros.html",
        {"livros": livros, "membros": membros},
    )


@require_POST
def emprestar_livro(request, livro_id):
    livro = get_object_or_404(Livro, pk=livro_id)
    membro_id = request.POST.get("membro_id", "")
    if not membro_id.isdecimal():
        messages.error(request, "Selecione um membro válido para o empréstimo.")
        return redirect("lista_livros")
    membro = get_object_or_404(Membro, pk=membro_id)

    with transaction.atomic():
        estoque_atualizado = Livro.objects.filter(
            pk=livro.pk,
            copias_disponiveis__gt=0,
        ).update(copias_disponiveis=F("copias_disponiveis") - 1)

        if estoque_atualizado:
            Emprestimo.objects.create(
                livro=livro,
                membro=membro,
                data_prevista_devolucao=timezone.localdate() + timedelta(days=14),
            )

    if not estoque_atualizado:
        messages.error(
            request,
            f'Não há cópias disponíveis de "{livro.titulo}" no momento.',
        )
        return redirect("lista_livros")

    messages.success(request, f'Empréstimo de "{livro.titulo}" registrado com sucesso!')
    return redirect("lista_livros")


@require_POST
def devolver_livro(request, emprestimo_id):
    emprestimo = get_object_or_404(
        Emprestimo.objects.select_related("livro"),
        pk=emprestimo_id,
    )

    try:
        with transaction.atomic():
            emprestimo_atualizado = Emprestimo.objects.filter(
                pk=emprestimo.pk,
                status__in=("ATIVO", "ATRASADO"),
            ).update(
                data_devolucao=timezone.localdate(),
                status="DEVOLVIDO",
            )

            if emprestimo_atualizado:
                estoque_atualizado = Livro.objects.filter(
                    pk=emprestimo.livro_id,
                    copias_disponiveis__lt=F("copias_totais"),
                ).update(copias_disponiveis=F("copias_disponiveis") + 1)
                if not estoque_atualizado:
                    raise EstoqueInconsistenteError(
                        "A devolução não foi registrada porque o estoque já "
                        "atingiu o total de cópias cadastrado. Confira o "
                        "estoque do livro no Admin."
                    )
    except EstoqueInconsistenteError as exc:
        messages.error(request, str(exc))
        return redirect("meus_emprestimos", membro_id=emprestimo.membro_id)

    if not emprestimo_atualizado:
        messages.warning(request, "Este empréstimo já foi devolvido.")
        return redirect("meus_emprestimos", membro_id=emprestimo.membro_id)

    messages.success(
        request,
        f'Devolução de "{emprestimo.livro.titulo}" registrada.',
    )
    return redirect("meus_emprestimos", membro_id=emprestimo.membro_id)


def meus_emprestimos(request, membro_id):
    membro = get_object_or_404(Membro, pk=membro_id)
    emprestimos = membro.emprestimo_set.select_related("livro").order_by(
        "-data_emprestimo"
    )
    total_multa = sum(
        (emprestimo.multa for emprestimo in emprestimos),
        Decimal("0.00"),
    )
    return render(
        request,
        "biblioteca/meus_emprestimos.html",
        {
            "membro": membro,
            "emprestimos": emprestimos,
            "total_multa": total_multa,
        },
    )


def relatorio_livros(request):
    livros = (
        Livro.objects.select_related("autor")
        .annotate(total_emprestimos=Count("emprestimo"))
        .order_by("-total_emprestimos", "titulo")
    )
    return render(
        request,
        "biblioteca/relatorio_livros.html",
        {"livros": livros},
    )
