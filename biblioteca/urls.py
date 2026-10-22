from django.urls import path

from . import views


urlpatterns = [
    path("", views.lista_livros, name="lista_livros"),
    path("emprestar/<int:livro_id>/", views.emprestar_livro, name="emprestar_livro"),
    path("devolver/<int:emprestimo_id>/", views.devolver_livro, name="devolver_livro"),
    path(
        "membro/<int:membro_id>/emprestimos/",
        views.meus_emprestimos,
        name="meus_emprestimos",
    ),
    path("relatorio/", views.relatorio_livros, name="relatorio_livros"),
]
