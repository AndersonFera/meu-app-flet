import flet as ft
import mysql.connector
import nest_asyncio
import os # Importar o módulo OS para acessar variáveis de ambiente

# Aplicar nest_asyncio para permitir loops aninhados no Colab
nest_asyncio.apply()

# --- Configuração do Banco de Dados ---
def salvar_no_banco(data, servico):
    try:
        # Usar os.environ.get() para pegar as variáveis do ambiente do Railway
        conexao = mysql.connector.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=os.environ.get("MYSQLPORT") # Adicionado a porta, que é importante
        )
        cursor = conexao.cursor()
        sql = "INSERT INTO agendamentos (data_consulta, servico) VALUES (%s, %s)"
        cursor.execute(sql, (data, servico))
        conexao.commit()
        cursor.close()
        conexao.close()
        return True
    except Exception as e:
        # A mensagem de erro agora mostrará um erro de autenticação, se houver um problema com as credenciais
        print(f"Erro: {e}")
        return False

# --- Interface com Flet ---
def main(page: ft.Page):
    page.title = "App de Agendamento 2025"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 600

    # Campos de entrada
    input_data = ft.TextField(label="Data (DD/MM/AAAA)", hint_text="Ex: 15/01/2025")
    dropdown_servico = ft.Dropdown(
        label="Escolha o Serviço",
        options=[
            ft.dropdown.Option("Consulta Geral"),
            ft.dropdown.Option("Retorno"),
            ft.dropdown.Option("Exame"),
        ],
    )
    texto_status = ft.Text()

    def agendar_clique(e):
        if not input_data.value or not dropdown_servico.value:
            texto_status.value = "Por favor, preencha todos os campos!"
            texto_status.color = "red"
        else:
            sucesso = salvar_no_banco(input_data.value, dropdown_servico.value)
            if sucesso:
                texto_status.value = "Agendamento realizado com sucesso!"
                texto_status.color = "green"
                input_data.value = ""
            else:
                texto_status.value = "Erro ao conectar com o banco de dados."
                texto_status.color = "red"
        page.update()

    # Layout da página
    page.add(
        ft.Text("Marcar Consulta", size=25, weight="bold"),
        input_data,
        dropdown_servico,
        ft.ElevatedButton("Confirmar Agendamento", on_click=agendar_clique),
        texto_status
    )

# Para rodar como App Desktop/Mobile: ft.app(target=main)
# Para rodar como Web: ft.app(target=main, view=ft.AppView.WEB_BROWSER)
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
