from django.contrib import admin
from django.templatetags.static import static
from django.utils.html import format_html

from .models import Autor, Emprestimo, Livro, Membro


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ("nome", "nacionalidade", "data_nascimento")
    search_fields = ("nome",)


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "preco",
        "copias_totais",
        "copias_disponiveis",
        "visualizar_capa",
    )
    list_filter = ("autor",)
    search_fields = ("titulo", "isbn", "autor__nome")
    readonly_fields = ("visualizar_capa",)

    @admin.display(description="Capa")
    def visualizar_capa(self, obj):
        if not obj or not obj.capa:
            return "Sem capa"
        return format_html(
            '<img src="{}" alt="Capa de {}" style="height:100px;width:auto;">',
            static(obj.capa),
            obj.titulo,
        )


class EmprestimoInline(admin.TabularInline):
    model = Emprestimo
    extra = 0
    can_delete = False
    readonly_fields = (
        "livro",
        "data_emprestimo",
        "data_prevista_devolucao",
        "data_devolucao",
        "status",
        "dias_atraso",
        "multa",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Membro)
class MembroAdmin(admin.ModelAdmin):
    list_display = ("nome", "email", "data_cadastro")
    search_fields = ("nome", "email")
    inlines = (EmprestimoInline,)


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        "livro",
        "membro",
        "data_emprestimo",
        "data_prevista_devolucao",
        "data_devolucao",
        "status",
        "dias_atraso",
        "multa",
    )
    list_filter = ("status", "data_emprestimo", "data_prevista_devolucao")
    search_fields = ("livro__titulo", "membro__nome", "membro__email")
    readonly_fields = ("dias_atraso", "multa")
