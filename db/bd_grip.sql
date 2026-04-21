DROP DATABASE IF EXISTS grip;
CREATE DATABASE grip;
USE grip;

CREATE TABLE Professor (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    registro_drt VARCHAR(50),
    cpf VARCHAR(15),
    email VARCHAR(50),
    senha VARCHAR(255)
);

CREATE TABLE Aluno (
    nome VARCHAR(50),
    cpf VARCHAR(15),
    telefone VARCHAR(50),
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(50),
    senha VARCHAR(255)
);

CREATE TABLE Aula (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    data DATE,
    descricao VARCHAR(255),
    fk_Professor_id INTEGER
);

CREATE TABLE Professor_Aluno (
    fk_Professor_id INTEGER,
    fk_Aluno_id INTEGER
);


ALTER TABLE Aula ADD CONSTRAINT FK_Aula_2
    FOREIGN KEY (fk_Professor_id)
    REFERENCES Professor (id);
 
ALTER TABLE Professor_Aluno ADD CONSTRAINT FK_Professor_Aluno_1
    FOREIGN KEY (fk_Professor_id)
    REFERENCES Professor (id)
    ON DELETE SET NULL;
 
ALTER TABLE Professor_Aluno ADD CONSTRAINT FK_Professor_Aluno_2
    FOREIGN KEY (fk_Aluno_id)
    REFERENCES Aluno (id)
    ON DELETE SET NULL;

/* Dados fake para testar */
INSERT INTO Professor (id, nome, registro_drt, cpf, email, senha) 
VALUES (1, 'Professor Diretor', 'DRT-1234', '11122233344', 'admin@escola.com', '123456');

INSERT INTO Aula (id, nome, data, descricao, fk_Professor_id) VALUES
(1, 'Pole Dance Iniciante', '2026-03-25', 'Introdução aos giros básicos e posturas', 1),
(2, 'Pole Coreografia', '2026-03-26', 'Coreografia fluida no mastro fixo e giratório', 1),
(3, 'Pole Sport', '2026-03-27', 'Foco em força, condicionamento e inversões', 1),
(4, 'Flexibilidade', '2026-03-28', 'Mobilidade, abertura de espacate e coluna', 1),
(5, 'Pole Exotic', '2026-03-29', 'Foco em fluidez no chão e uso de salto alto', 1);

INSERT INTO Aluno (id, nome, cpf, telefone, email, senha) VALUES
(1, 'Fernanda Lima', '666.666.666-66', '41999999999', 'fernanda@email.com', 'pbkdf2_sha256$390000$00323569dcc4d97eb66243483622c103$tUuvdsMd1K/Zbx/va9pWmV7/2Yos6Y442PpxKR5Tllo='),
(2, 'Gabriel Martins', '777.777.777-77', '41988888888', 'gabriel@email.com', 'pbkdf2_sha256$390000$5d61e567edbb220a3249ac1662358e34$go3/IiNeQM4pU5Dp25hH93NCtMVznQ+Lv9Du1YnsFEo='),
(3, 'Helena Bastos', '888.888.888-88', '41977777777', 'helena@email.com', 'pbkdf2_sha256$390000$a65a783263d47531de3b008655521e2d$DFgtvsA1ZvggIDbVniW3kuToF2OlYg19Ysh67d0QuEo='),
(4, 'Igor Nunes', '999.999.999-99', '41966666666', 'igor@email.com', 'pbkdf2_sha256$390000$3a7a9354a5703d470cf30f4f7a6f0ca2$k9E9d0+ooJ/k6mT32n6BPbtaVsQXZHv2ebDIfIcF+LI='),
(5, 'Julia Castro', '000.000.000-00', '41955555555', 'julia@email.com', 'pbkdf2_sha256$390000$2e577e376374425e4c0b46efac685f79$3g3SrZ9wbVhMwKQgMlbarMCUOTCYM/jQOwu3qGDnfVQ=');

INSERT INTO Professor_Aluno (fk_Professor_id, fk_Aluno_id) VALUES
(1, 1);

SELECT * FROM Professor;

