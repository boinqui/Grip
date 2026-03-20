DROP DATABASE IF EXISTS grip;
CREATE DATABASE grip;
USE grip;

/* ===========================
   CRIANDO AS TABELAS
=========================== */

CREATE TABLE Professor (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    registro_drt VARCHAR(50),
    cpf VARCHAR(15),
    data_nascimento DATE,
    email VARCHAR(50),
    senha VARCHAR(255),
    fk_Aula_id INTEGER
);

CREATE TABLE Aluno (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    cpf VARCHAR(15),
    data_nascimento DATE,
    telefone VARCHAR(50),
    email VARCHAR(50),
    senha VARCHAR(255)
);

CREATE TABLE Movimento (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    descricao VARCHAR(255),
    dificuldade VARCHAR(50),
    video_url VARCHAR(255)
);

CREATE TABLE Aula (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    data DATE,
    descricao VARCHAR(255)
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
/* Mantivemos os IDs manuais apenas aqui no INSERT para garantir que 
   as relações entre as tabelas continuem funcionando perfeitamente */

INSERT INTO Aula (id, nome, data, descricao) VALUES
(1, 'Pole Dance Iniciante', '2026-03-25', 'Introdução aos giros básicos e posturas'),
(2, 'Pole Coreografia', '2026-03-26', 'Coreografia fluida no mastro fixo e giratório'),
(3, 'Pole Sport', '2026-03-27', 'Foco em força, condicionamento e inversões'),
(4, 'Flexibilidade', '2026-03-28', 'Mobilidade, abertura de espacate e coluna'),
(5, 'Pole Exotic', '2026-03-29', 'Foco em fluidez no chão e uso de salto alto');

INSERT INTO Professor (id, nome, registro_drt, cpf, data_nascimento, email, senha, fk_Aula_id) VALUES
(1, 'Ana Silva', 'DRT1234', '111.111.111-11', '1990-05-14', 'ana@grip.com', 'senha123', 1),
(2, 'Bruno Costa', 'DRT5678', '222.222.222-22', '1988-10-22', 'bruno@grip.com', 'senha123', 2),
(3, 'Carla Mendes', 'DRT9012', '333.333.333-33', '1995-02-10', 'carla@grip.com', 'senha123', 3),
(4, 'Diego Rocha', 'DRT3456', '444.444.444-44', '1985-07-30', 'diego@grip.com', 'senha123', 4),
(5, 'Elena Souza', 'DRT7890', '555.555.555-55', '1992-12-05', 'elena@grip.com', 'senha123', 5);

INSERT INTO Aluno (id, nome, cpf, data_nascimento, telefone, email, senha) VALUES
(1, 'Fernanda Lima', '666.666.666-66', '2000-01-15', '41999999999', 'fernanda@email.com', 'aluno123'),
(2, 'Gabriel Martins', '777.777.777-77', '1998-04-20', '41988888888', 'gabriel@email.com', 'aluno123'),
(3, 'Helena Bastos', '888.888.888-88', '1996-08-11', '41977777777', 'helena@email.com', 'aluno123'),
(4, 'Igor Nunes', '999.999.999-99', '2001-11-25', '41966666666', 'igor@email.com', 'aluno123'),
(5, 'Julia Castro', '000.000.000-00', '1999-03-08', '41955555555', 'julia@email.com', 'aluno123');

INSERT INTO Movimento (id, nome, descricao, dificuldade, video_url) VALUES
(1, 'Bombeiro', 'Giro básico de descida com as pernas presas no mastro', 'Iniciante', 'https://video.url/bombeiro'),
(2, 'Inversão Básica', 'Elevação do quadril acima da cabeça (Crucifixo invertido)', 'Intermediário', 'https://video.url/inversao'),
(3, 'Scorpio', 'Trava de perna interna no mastro', 'Intermediário', 'https://video.url/scorpio'),
(4, 'Iron X', 'Sustentação lateral do corpo segurando apenas com as mãos', 'Avançado', 'https://video.url/ironx'),
(5, 'Chair Spin', 'Giro sentado em posição de cadeira', 'Iniciante', 'https://video.url/chair');

INSERT INTO Professor_Aluno (fk_Professor_id, fk_Aluno_id) VALUES
(1, 1), (1, 2), (2, 3), (3, 4), (5, 5);

INSERT INTO Aula_Movimento (fk_Aula_id, fk_Movimento_id) VALUES
(1, 1), (1, 5), (3, 2), (3, 3), (3, 4);


SELECT * FROM Professor;