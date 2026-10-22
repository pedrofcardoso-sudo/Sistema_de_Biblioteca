# Sistema de Biblioteca — Projeto 2

Projeto da disciplina Construção de Backend (IESB), feito com Django. Gerencia
autores, livros, membros e empréstimos, com controle de estoque e identificação
de empréstimos atrasados. O projeto segue a estrutura do guia, acrescentando
arquivos para capas locais e cadastro de dados de demonstração.

## Estrutura do projeto

```text
config/
  settings.py
  urls.py
  wsgi.py
biblioteca/
  migrations/
  management/commands/seed_biblioteca.py
  static/biblioteca/css/style.css
  static/biblioteca/js/loading.js
  static/biblioteca/capas/
  templates/biblioteca/
  admin.py
  models.py
  tests.py
  urls.py
  views.py
manage.py
requirements.txt
```

## Funcionalidades

- Cadastro e consulta de autores, livros, membros e empréstimos pelo Django Admin.
- Empréstimos com prazo de 14 dias e redução segura do estoque.
- Devoluções com reposição de estoque, sem duplicar a devolução.
- Consulta de empréstimos por membro e indicação de atraso.
- Multa de R$ 2,00 por dia de atraso, com total acumulado por membro.
- Relatório de livros mais emprestados usando `annotate()` e `Count()`.
- Preços e capas SVG locais criadas para os livros de demonstração.
- Interface responsiva com navegação, cartões de livros, mensagens e indicador
  de carregamento, inspirada no guia da Pizzaria Roma.
- Temas claro, escuro e sépia selecionáveis, com preferência salva no navegador.
- Banco PostgreSQL do Supabase ou SQLite para desenvolvimento local.

## Requisitos

- Python 3.10 ou superior.
- Windows PowerShell, Prompt de Comando ou terminal equivalente.

## Como executar no Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure o arquivo `.env` na raiz do projeto com `SECRET_KEY`, `DEBUG` e as
variáveis `SUPABASE_DB_NAME`, `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD`,
`SUPABASE_DB_HOST` e `SUPABASE_DB_PORT` fornecidas pelo Supabase. O `.env` já
está no `.gitignore`; nunca o publique nem compartilhe sua senha do banco.
Quando as variáveis do Supabase estiverem definidas, o projeto usará PostgreSQL
com SSL. Sem elas, usará o SQLite local.

```powershell
python manage.py migrate
python manage.py seed_biblioteca
python manage.py createsuperuser
python manage.py runserver
```

Abra <http://127.0.0.1:8000/> para acessar o acervo e
<http://127.0.0.1:8000/admin/> para cadastrar autores, livros e membros.
O comando `seed_biblioteca` cadastra dez livros de exemplo, cada um com dez
cópias totais, preços em reais, capas SVG locais, autores e seis membros. O
estoque disponível é ajustado para descontar os empréstimos ativos, então um
livro sem empréstimos não fica indisponível indevidamente. Os ISBNs iniciados
por `DEMO-IESB` são identificadores de demonstração, não ISBNs comerciais. O
comando pode ser executado novamente sem duplicar registros.

A multa diária é de R$ 2,00. O cálculo começa no dia seguinte ao vencimento e
vai até a data de devolução; se o empréstimo continuar aberto, o cálculo usa a
data atual. Os valores são calculados pelo Model e não alteram o esquema do banco.

## Testes

```powershell
python manage.py test
```

Os testes usam SQLite, mesmo quando o `.env` está apontando para o Supabase,
para não alterar os dados do banco remoto.

## Configuração para produção

Antes de publicar em um servidor, substitua a chave de desenvolvimento por uma
chave `SECRET_KEY` forte, defina `DEBUG=false` e configure
`DJANGO_ALLOWED_HOSTS` com os domínios do servidor. Nunca publique chaves,
senhas, o arquivo `.env` ou o banco local (`db.sqlite3`).

## Autor

Projeto acadêmico IESB — 2026. Atualize esta seção com seu nome antes de publicar
o repositório.
