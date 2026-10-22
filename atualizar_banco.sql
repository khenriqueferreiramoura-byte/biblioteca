-- Execute no MySQL Workbench, selecionando o banco BIBLIOTECA_INTELIGENTE.
-- A aplicação usa as tabelas LIVROS, AUTORES, ALUNOS e EMPRESTIMO existentes.
-- Esta coluna opcional guarda o endereço de uma imagem de capa para cada livro.
USE BIBLIOTECA_INTELIGENTE;

ALTER TABLE LIVROS
ADD COLUMN CAPA_URL VARCHAR(500) NULL;
