from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector

app = FastAPI()


# --- Conexão Direta e Segura com o MySQL do Railway ---
def conectar_banco():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE", "sistema_agendamento"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )


# --- Modelo 1: Dados para fazer o Login ---
class LoginSchema(BaseModel):
    cpf: str
    data_nascimento: str


# --- Modelo 2: Dados para fazer o Agendamento ---
class AgendamentoSchema(BaseModel):
    paciente_id: int
    data_consulta: str
    servico: str


# 🟢 1. ROTA DE LOGIN (Espera receber CPF e Data de Nascimento)
@app.post("/validar-paciente")
def validar_paciente(dados: LoginSchema):
    try:
        cpf_limpo = "".join(filter(str.isdigit, dados.cpf))
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        query = "SELECT id, nome_completo FROM pacientes_ubs WHERE cpf = %s AND data_nascimento = %s"
        cursor.execute(query, (cpf_limpo, dados.data_nascimento))
        paciente = cursor.fetchone()

        if not paciente:
            cursor.close()
            conexao.close()
            raise HTTPException(status_code=401, detail="Cadastro não encontrado na UBS.")

        query_usuario = "INSERT IGNORE INTO usuarios_app (paciente_ubs_id) VALUES (%s)"
        cursor.execute(query_usuario, (paciente['id'],))
        conexao.commit()

        cursor.close()
        conexao.close()

        return {
            "status": "sucesso",
            "paciente_id": paciente['id'],
            "nome": paciente['nome_completo']
        }
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no banco local: {e}")


# 🟢 2. ROTA DE AGENDAMENTO (Espera receber paciente_id, data_consulta e servico)
@app.post("/agendar")
def criar_agendamento(dados: AgendamentoSchema):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        sql = "INSERT INTO agendamentos (paciente_ubs_id, data_consulta, servico) VALUES (%s, %s, %s)"
        cursor.execute(sql, (dados.paciente_id, dados.data_consulta, dados.servico))

        conexao.commit()
        cursor.close()
        conexao.close()

        return {"status": "sucesso", "mensagem": "Agendamento realizado!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar consulta: {e}")


@app.get("/")
def home():
    return {"status": "API Local Online"}
