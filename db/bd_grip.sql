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
(1, 'Ana Silva', 'DRT1234', '111.111.111-11', '1990-05-14', 'ana@grip.com', 'pbkdf2_sha256$390000$7188f3e8fb43d9fc1d6c2089dd0b05c7$duEK1OPDZWRSymqg2Y/Roi8heXSu6vsas20fo6ivDfM=', 1),
(2, 'Bruno Costa', 'DRT5678', '222.222.222-22', '1988-10-22', 'bruno@grip.com', 'pbkdf2_sha256$390000$e899f4db2ef7c596239e6123d82110c0$oJeYQDDH0x5uHP/wgeGU4WPa5v/Ggqdal7/yO/XtghE=', 2),
(3, 'Carla Mendes', 'DRT9012', '333.333.333-33', '1995-02-10', 'carla@grip.com', 'pbkdf2_sha256$390000$f66377143b1899c6d0aa6f4337564d23$ZOYqEn4BbK68UtGoEtlNZscbKzRNY5dh4bh97zvfTCQ=', 3),
(4, 'Diego Rocha', 'DRT3456', '444.444.444-44', '1985-07-30', 'diego@grip.com', 'pbkdf2_sha256$390000$94fe64466d4f683a1e0e0c50141d9920$ypq7bwiXVVEdSeCtfj2f1XO7+c/H/gU0XBXYb4iSqhA=', 4),
(5, 'Elena Souza', 'DRT7890', '555.555.555-55', '1992-12-05', 'elena@grip.com', 'pbkdf2_sha256$390000$1bf1d4813b22b7c055e6aee519337a12$wlgaytXuuDMv1Z9jwqkOLcdfsfbZD3EB1MFlzi6dcIE=', 5);

INSERT INTO Aluno (id, nome, cpf, data_nascimento, telefone, email, senha) VALUES
(1, 'Fernanda Lima', '666.666.666-66', '2000-01-15', '41999999999', 'fernanda@email.com', 'pbkdf2_sha256$390000$00323569dcc4d97eb66243483622c103$tUuvdsMd1K/Zbx/va9pWmV7/2Yos6Y442PpxKR5Tllo='),
(2, 'Gabriel Martins', '777.777.777-77', '1998-04-20', '41988888888', 'gabriel@email.com', 'pbkdf2_sha256$390000$5d61e567edbb220a3249ac1662358e34$go3/IiNeQM4pU5Dp25hH93NCtMVznQ+Lv9Du1YnsFEo='),
(3, 'Helena Bastos', '888.888.888-88', '1996-08-11', '41977777777', 'helena@email.com', 'pbkdf2_sha256$390000$a65a783263d47531de3b008655521e2d$DFgtvsA1ZvggIDbVniW3kuToF2OlYg19Ysh67d0QuEo='),
(4, 'Igor Nunes', '999.999.999-99', '2001-11-25', '41966666666', 'igor@email.com', 'pbkdf2_sha256$390000$3a7a9354a5703d470cf30f4f7a6f0ca2$k9E9d0+ooJ/k6mT32n6BPbtaVsQXZHv2ebDIfIcF+LI='),
(5, 'Julia Castro', '000.000.000-00', '1999-03-08', '41955555555', 'julia@email.com', 'pbkdf2_sha256$390000$2e577e376374425e4c0b46efac685f79$3g3SrZ9wbVhMwKQgMlbarMCUOTCYM/jQOwu3qGDnfVQ=');

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
