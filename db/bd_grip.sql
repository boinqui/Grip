DROP DATABASE IF EXISTS grip;
CREATE DATABASE grip;
USE grip;

/* ===========================
   CRIANDO AS TABELAS
=========================== */

CREATE TABLE Professor (
    nome VARCHAR(50),
    registro_drt VARCHAR(50),
    cpf VARCHAR(15),
    id INTEGER PRIMARY KEY,
    email VARCHAR(50),
    senha VARCHAR(255),
    fk_Aula_id INTEGER
);

CREATE TABLE Aluno (
    nome VARCHAR(50),
    cpf VARCHAR(15),
    telefone VARCHAR(50),
    id INTEGER PRIMARY KEY,
    email VARCHAR(50),
    senha VARCHAR(255)
);

CREATE TABLE Movimento (
    nome VARCHAR(50),
    descricao VARCHAR(255),
    dificuldade VARCHAR(50),
    video_url VARCHAR(255),
    id INTEGER PRIMARY KEY
);

CREATE TABLE Aula (
    nome VARCHAR(50),
    data DATE,
    descricao VARCHAR(255),
    id INTEGER PRIMARY KEY
);

CREATE TABLE Professor_Aluno (
    fk_Professor_id INTEGER,
    fk_Aluno_id INTEGER
);

CREATE TABLE Aula_Movimento (
    fk_Aula_id INTEGER,
    fk_Movimento_id INTEGER
);
 
/* ===========================
   ADICIONANDO AS CONSTRAINTS
=========================== */

ALTER TABLE Professor ADD CONSTRAINT FK_Professor_2
    FOREIGN KEY (fk_Aula_id)
    REFERENCES Aula (id)
    ON DELETE RESTRICT;
 
ALTER TABLE Professor_Aluno ADD CONSTRAINT FK_Professor_Aluno_1
    FOREIGN KEY (fk_Professor_id)
    REFERENCES Professor (id)
    ON DELETE SET NULL;
 
ALTER TABLE Professor_Aluno ADD CONSTRAINT FK_Professor_Aluno_2
    FOREIGN KEY (fk_Aluno_id)
    REFERENCES Aluno (id)
    ON DELETE SET NULL;
 
ALTER TABLE Aula_Movimento ADD CONSTRAINT FK_Aula_Movimento_1
    FOREIGN KEY (fk_Aula_id)
    REFERENCES Aula (id)
    ON DELETE RESTRICT;
 
ALTER TABLE Aula_Movimento ADD CONSTRAINT FK_Aula_Movimento_2
    FOREIGN KEY (fk_Movimento_id)
    REFERENCES Movimento (id)
    ON DELETE RESTRICT;


/* ===========================
   INSERINDO OS DADOS (POPULANDO)
=========================== */

-- 1. Inserindo 5 Aulas PRIMEIRO (necessário para a Foreign Key de Professor)
INSERT INTO Aula (id, nome, data, descricao) VALUES
(1, 'Pole Dance Iniciante', '2026-03-25', 'Introdução aos giros básicos e posturas'),
(2, 'Pole Coreografia', '2026-03-26', 'Coreografia fluida no mastro fixo e giratório'),
(3, 'Pole Sport', '2026-03-27', 'Foco em força, condicionamento e inversões'),
(4, 'Flexibilidade', '2026-03-28', 'Mobilidade, abertura de espacate e coluna'),
(5, 'Pole Exotic', '2026-03-29', 'Foco em fluidez no chão e uso de salto alto');

-- 2. Inserindo 5 Professores
INSERT INTO Professor (id, nome, registro_drt, cpf, email, senha, fk_Aula_id) VALUES
(1, 'Ana Silva', 'DRT1234', '111.111.111-11', 'ana@grip.com', 'senha123', 1),
(2, 'Bruno Costa', 'DRT5678', '222.222.222-22', 'bruno@grip.com', 'senha123', 2),
(3, 'Carla Mendes', 'DRT9012', '333.333.333-33', 'carla@grip.com', 'senha123', 3),
(4, 'Diego Rocha', 'DRT3456', '444.444.444-44', 'diego@grip.com', 'senha123', 4),
(5, 'Elena Souza', 'DRT7890', '555.555.555-55', 'elena@grip.com', 'senha123', 5);

-- 3. Inserindo 5 Alunos
INSERT INTO Aluno (id, nome, cpf, telefone, email, senha) VALUES
(1, 'Fernanda Lima', '666.666.666-66', '41999999999', 'fernanda@email.com', 'aluno123'),
(2, 'Gabriel Martins', '777.777.777-77', '41988888888', 'gabriel@email.com', 'aluno123'),
(3, 'Helena Bastos', '888.888.888-88', '41977777777', 'helena@email.com', 'aluno123'),
(4, 'Igor Nunes', '999.999.999-99', '41966666666', 'igor@email.com', 'aluno123'),
(5, 'Julia Castro', '000.000.000-00', '41955555555', 'julia@email.com', 'aluno123');

-- 4. Inserindo 5 Movimentos
INSERT INTO Movimento (id, nome, descricao, dificuldade, video_url) VALUES
(1, 'Bombeiro', 'Giro básico de descida com as pernas presas no mastro', 'Iniciante', 'https://video.url/bombeiro'),
(2, 'Inversão Básica', 'Elevação do quadril acima da cabeça (Crucifixo invertido)', 'Intermediário', 'https://video.url/inversao'),
(3, 'Scorpio', 'Trava de perna interna no mastro', 'Intermediário', 'https://video.url/scorpio'),
(4, 'Iron X', 'Sustentação lateral do corpo segurando apenas com as mãos', 'Avançado', 'https://video.url/ironx'),
(5, 'Chair Spin', 'Giro sentado em posição de cadeira', 'Iniciante', 'https://video.url/chair');

-- 5. Inserindo relações na tabela Professor_Aluno (Opcional, mas recomendado)
INSERT INTO Professor_Aluno (fk_Professor_id, fk_Aluno_id) VALUES
(1, 1), (1, 2), (2, 3), (3, 4), (5, 5);

-- 6. Inserindo relações na tabela Aula_Movimento (Opcional, mas recomendado)
INSERT INTO Aula_Movimento (fk_Aula_id, fk_Movimento_id) VALUES
(1, 1), (1, 5), (3, 2), (3, 3), (3, 4);


SELECT * FROM Professor;

