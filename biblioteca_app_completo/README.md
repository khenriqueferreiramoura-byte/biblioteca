# Biblioteca Inteligente — Flask + MySQL

## Funcionalidades
- Login demonstrativo
- Painel com totais e movimentações recentes
- CRUD de livros, autores e alunos (cadastrar, consultar, editar, excluir)
- Registrar empréstimos sem permitir emprestar novamente um livro já ativo
- Registrar devolução via UPDATE e guardar data de devolução
- Histórico completo de empréstimos

## 1. Atualize o banco
No MySQL Workbench, execute `atualizar_banco.sql`. Ele adiciona as colunas `STATUS` e `DATA_DEVOLUCAO` se não existirem. Seu banco e as tabelas existentes devem se chamar `BIBLIOTECA_INTELIGENTE`, `LIVROS`, `AUTORES`, `ALUNOS` e `EMPRESTIMO`.

## 2. Instale e execute
No terminal do VS Code, na pasta extraída:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000 no navegador.

Login demonstrativo: `admin` / `biblioteca123`.

## Configuração MySQL padrão
Host `localhost`, banco `BIBLIOTECA_INTELIGENTE`, usuário `root`, senha vazia, porta `3307`. Se necessário, altere as variáveis `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`.

## Observações
O login é demonstrativo e não deve ser usado em produção sem implementar autenticação real e proteção adicional. Como os registros iniciais de empréstimo receberão `STATUS='Emprestado'` ao adicionar a coluna, esses livros serão considerados emprestados. A exclusão de livros/alunos com histórico é bloqueada para preservar os relacionamentos.
