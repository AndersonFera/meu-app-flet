import os  # 💥 CORREÇÃO 1: Adicionado para o Railway conseguir ler o os.environ
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Para liberar o acesso do Flet
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

# 💥 CORREÇÃO 2: Liberar CORS para que seu app Flet web consiga falar com a API sem bloqueios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# 🟢 1. ROTA DE LOGIN (Atualizada para aceitar tanto POST quanto parâmetros na URL se o Flet enviar errado)
@app.post("/validar-paciente")
@app.get("/validar-paciente")  # 💥 CORREÇÃO 3: Aceita requisições GET também para evitar erros no Flet
def validar_paciente(dados: LoginSchema = None, cpf: str = None, data_nascimento: str = None):
    try:
        # Identifica se os dados vieram pelo corpo (POST) ou pela URL (GET)
        v_cpf = dados.cpf if dados else cpf
        v_data = dados.data_nascimento if dados else data_nascimento

        if not v_cpf or not v_data:
            raise HTTPException(status_code=400, detail="CPF e Data de Nascimento são obrigatórios.")

        cpf_limpo = "".join(filter(str.isdigit, v_cpf))
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)

        query = "SELECT id, nome_completo FROM pacientes_ubs WHERE cpf = %s AND data_nascimento = %s"
        cursor.execute(query, (cpf_limpo, v_data))
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
        raise HTTPException(status_code=500, detail=f"Erro no banco: {e}")


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
