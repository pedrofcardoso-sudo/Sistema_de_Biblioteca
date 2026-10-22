from datetime import timedelta
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Autor, Emprestimo, Livro, Membro


class RegrasDeNegocioTest(TestCase):
    def setUp(self):
        self.autor = Autor.objects.create(
            nome="Machado de Assis",
            nacionalidade="Brasileira",
        )
        self.livro = Livro.objects.create(
            titulo="Dom Casmurro",
            autor=self.autor,
            isbn="9780000000001",
            copias_totais=1,
            copias_disponiveis=1,
        )
        self.sem_copia = Livro.objects.create(
            titulo="O Cortiço",
            autor=self.autor,
            isbn="9780000000002",
            copias_totais=1,
            copias_disponiveis=0,
        )
        self.membro = Membro.objects.create(nome="Ana", email="ana@example.com")

    def test_emprestar_define_prazo_e_decrementa_estoque(self):
        response = self.client.post(
            reverse("emprestar_livro", args=[self.livro.pk]),
            {"membro_id": self.membro.pk},
        )

        self.assertRedirects(response, reverse("lista_livros"))
        emprestimo = Emprestimo.objects.get()
        self.assertEqual(
            emprestimo.data_prevista_devolucao,
            timezone.localdate() + timedelta(days=14),
        )
        self.assertEqual(emprestimo.status, "ATIVO")
        self.livro.refresh_from_db()
        self.assertEqual(self.livro.copias_disponiveis, 0)

    def test_bloqueia_emprestimo_sem_copias(self):
        response = self.client.post(
            reverse("emprestar_livro", args=[self.sem_copia.pk]),
            {"membro_id": self.membro.pk},
            follow=True,
        )

        self.assertEqual(Emprestimo.objects.count(), 0)
        self.sem_copia.refresh_from_db()
        self.assertEqual(self.sem_copia.copias_disponiveis, 0)
        self.assertContains(response, "Não há cópias disponíveis")

    def test_emprestimo_rejeita_get_e_membro_invalido(self):
        url = reverse("emprestar_livro", args=[self.livro.pk])
        self.assertEqual(self.client.get(url).status_code, 405)

        response = self.client.post(url, {"membro_id": "inválido"}, follow=True)
        self.assertContains(response, "Selecione um membro válido")
        self.assertEqual(Emprestimo.objects.count(), 0)

    def test_devolver_repoe_estoque_apenas_uma_vez(self):
        self.client.post(
            reverse("emprestar_livro", args=[self.livro.pk]),
            {"membro_id": self.membro.pk},
        )
        emprestimo = Emprestimo.objects.get()
        url = reverse("devolver_livro", args=[emprestimo.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.client.post(url)

        emprestimo.refresh_from_db()
        self.livro.refresh_from_db()
        self.assertEqual(emprestimo.status, "DEVOLVIDO")
        self.assertEqual(emprestimo.data_devolucao, timezone.localdate())
        self.assertEqual(self.livro.copias_disponiveis, 1)

    def test_devolucao_preserva_registros_se_estoque_estiver_inconsistente(self):
        emprestimo = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate(),
        )

        response = self.client.post(
            reverse("devolver_livro", args=[emprestimo.pk]),
            follow=True,
        )

        emprestimo.refresh_from_db()
        self.livro.refresh_from_db()
        self.assertEqual(emprestimo.status, "ATIVO")
        self.assertIsNone(emprestimo.data_devolucao)
        self.assertEqual(self.livro.copias_disponiveis, 1)
        self.assertContains(response, "estoque já atingiu")

    def test_property_de_atraso_considera_status_e_prazo(self):
        hoje = timezone.localdate()
        atrasado = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje - timedelta(days=1),
        )
        no_prazo = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje + timedelta(days=3),
        )
        devolvido = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje - timedelta(days=5),
            status="DEVOLVIDO",
        )

        self.assertTrue(atrasado.esta_atrasado)
        self.assertFalse(no_prazo.esta_atrasado)
        self.assertFalse(devolvido.esta_atrasado)

    def test_calculos_de_atraso_sao_seguros_antes_de_preencher_datas(self):
        emprestimo_novo = Emprestimo()

        self.assertFalse(emprestimo_novo.esta_atrasado)
        self.assertEqual(emprestimo_novo.dias_atraso, 0)
        self.assertEqual(emprestimo_novo.multa, Decimal("0.00"))

    def test_multa_diaria_de_dois_reais_considera_dias_completos(self):
        hoje = timezone.localdate()
        atrasado = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje - timedelta(days=3),
        )
        vence_hoje = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje,
        )
        devolvido_atrasado = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje - timedelta(days=4),
            data_devolucao=hoje - timedelta(days=1),
            status="DEVOLVIDO",
        )
        devolvido_no_prazo = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=hoje - timedelta(days=2),
            data_devolucao=hoje - timedelta(days=2),
            status="DEVOLVIDO",
        )

        self.assertEqual(atrasado.dias_atraso, 3)
        self.assertEqual(atrasado.multa, Decimal("6.00"))
        self.assertEqual(vence_hoje.multa, Decimal("0.00"))
        self.assertEqual(devolvido_atrasado.dias_atraso, 3)
        self.assertEqual(devolvido_atrasado.multa, Decimal("6.00"))
        self.assertEqual(devolvido_no_prazo.multa, Decimal("0.00"))

    def test_tela_do_membro_exibe_multas_individuais_e_total(self):
        Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate() - timedelta(days=2),
        )
        Emprestimo.objects.create(
            livro=self.sem_copia,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(
            reverse("meus_emprestimos", args=[self.membro.pk])
        )

        self.assertContains(response, "R$ 4,00")
        self.assertContains(response, "R$ 2,00")
        self.assertContains(response, "Multa acumulada até hoje")

    def test_admin_exibe_dias_e_valor_da_multa_somente_para_leitura(self):
        emprestimo = Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate() - timedelta(days=1),
        )
        usuario = get_user_model().objects.create_superuser(
            username="admin-teste",
            email="admin@example.com",
            password="senha-segura-de-teste",
        )
        self.client.force_login(usuario)

        response = self.client.get(
            reverse(
                "admin:biblioteca_emprestimo_change",
                args=[emprestimo.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dias atraso:")
        self.assertContains(response, "Multa:")
        self.assertContains(response, "2.00")

    def test_admin_abre_formulario_de_novo_emprestimo_sem_datas(self):
        usuario = get_user_model().objects.create_superuser(
            username="admin-novo-emprestimo",
            email="admin-novo@example.com",
            password="senha-segura-de-teste",
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("admin:biblioteca_emprestimo_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dias_atraso")
        self.assertContains(response, "multa")

    def test_tela_do_membro_exibe_badge_de_atraso(self):
        Emprestimo.objects.create(
            livro=self.livro,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate() - timedelta(days=2),
        )

        response = self.client.get(
            reverse("meus_emprestimos", args=[self.membro.pk])
        )

        self.assertContains(response, "Atrasado")

    def test_relacionamentos_e_ranking_de_emprestimos(self):
        self.assertEqual(self.autor.livros.count(), 2)
        for _ in range(3):
            Emprestimo.objects.create(
                livro=self.livro,
                membro=self.membro,
                data_prevista_devolucao=timezone.localdate(),
            )
        Emprestimo.objects.create(
            livro=self.sem_copia,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate(),
        )

        ranking = list(
            Livro.objects.annotate(total=Count("emprestimo")).order_by("-total")
        )

        self.assertEqual(ranking[0].titulo, "Dom Casmurro")
        self.assertEqual(ranking[0].total, 3)
        self.assertEqual(
            self.client.get(reverse("relatorio_livros")).status_code,
            200,
        )
        response = self.client.get(reverse("lista_livros"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "R$ 0,00")

    def test_models_sao_registrados_no_admin(self):
        for model in (Autor, Livro, Membro, Emprestimo):
            self.assertIn(model, admin.site._registry)

    def test_cadastro_de_demonstracao_pode_ser_reexecutado_sem_duplicar(self):
        call_command("seed_biblioteca", verbosity=0)
        livro = Livro.objects.get(isbn="DEMO-IESB-001")
        Emprestimo.objects.create(
            livro=livro,
            membro=self.membro,
            data_prevista_devolucao=timezone.localdate(),
        )
        livro.copias_totais = 10
        livro.copias_disponiveis = 9
        livro.save(update_fields=["copias_totais", "copias_disponiveis"])

        call_command("seed_biblioteca", verbosity=0)

        self.assertEqual(Livro.objects.count(), 12)
        self.assertEqual(Autor.objects.count(), 8)
        self.assertEqual(Membro.objects.count(), 6)
        livro.refresh_from_db()
        self.assertEqual(livro.copias_totais, 10)
        self.assertEqual(livro.copias_disponiveis, 9)
        self.assertEqual(str(livro.preco), "34.90")
        self.assertEqual(livro.capa, "biblioteca/capas/dom-casmurro.svg")
        o_cortico = Livro.objects.get(isbn="DEMO-IESB-003")
        self.assertEqual(o_cortico.copias_totais, 10)
        self.assertEqual(o_cortico.copias_disponiveis, 10)
        self.assertEqual(o_cortico.emprestimo_set.count(), 0)
        self.assertEqual(
            Livro.objects.filter(
                isbn__startswith="DEMO-IESB",
                copias_totais__gte=10,
            ).count(),
            10,
        )
        self.assertEqual(
            Membro.objects.filter(email__endswith="@example.com").count(),
            6,
        )
        response = self.client.get(reverse("lista_livros"))
        self.assertContains(
            response,
            "/static/biblioteca/capas/dom-casmurro.svg",
        )
        self.assertContains(response, "/static/biblioteca/css/style.css")
        self.assertContains(response, "/static/biblioteca/js/loading.js")
        self.assertContains(response, "/static/biblioteca/js/theme.js")
        self.assertContains(response, 'id="theme-select"')
        self.assertContains(response, '<option value="claro">Claro</option>')
        self.assertContains(response, '<option value="escuro">Escuro</option>')
        self.assertContains(response, '<option value="sepia">Sépia</option>')
        self.assertContains(response, "Nosso acervo")
        self.assertContains(response, "book-card")
        self.assertContains(response, "Biblioteca")
        self.assertContains(response, "Eduarda Lima")
