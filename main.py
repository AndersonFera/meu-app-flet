import flet as ft
import requests
import nest_asyncio

# Permitir loops aninhados no ambiente do Colab/Notebook se necessário
nest_asyncio.apply()

# --- URL da sua API no Railway ---
# Enquanto testa no PyCharm, mantenha o localhost. Quando subir a API no Railway, mude para o link dela.
API_URL = "http://127.0.0.1:8000"


def main(page: ft.Page):
    page.title = "Sistema de Agendamento UBS"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Variável global do app para lembrar quem está logado
    paciente_id_salvo = None

    # ==========================================
    # COMPONENTES DA TELA 1: LOGIN
    # ==========================================
    input_cpf = ft.TextField(label="Digite seu CPF", max_length=11, keyboard_type=ft.KeyboardType.NUMBER)
    input_nasc = ft.TextField(label="Data de Nascimento", hint_text="AAAA-MM-DD")
    status_login = ft.Text()

    # ==========================================
    # COMPONENTES DA TELA 2: AGENDAMENTO
    # ==========================================
    texto_boas_vindas = ft.Text(size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
    input_data_consulta = ft.TextField(label="Data da Consulta (DD/MM/AAAA)", hint_text="Ex: 15/01/2025")
    dropdown_servico = ft.Dropdown(
        label="Escolha o Serviço",
        options=[
            ft.dropdown.Option("Consulta Geral"),
            ft.dropdown.Option("Retorno"),
            ft.dropdown.Option("Exame"),
        ],
    )
    status_agendamento = ft.Text()

    # ==========================================
    # LÓGICA DE TRANSIÇÃO DE TELAS
    # ==========================================
    def mostrar_tela_agendamento(nome_paciente):
        """Limpa a tela de login e desenha a tela de agendamento"""
        page.clean()
        texto_boas_vindas.value = f"Olá, {nome_paciente}!"
        page.add(
            ft.Icon(ft.Icons.LOCAL_HOSPITAL, color=ft.Colors.BLUE_600, size=40),
            texto_boas_vindas,
            ft.Text("Preencha os dados abaixo para agendar:", size=14, color=ft.Colors.GREY_600),
            ft.Divider(),
            input_data_consulta,
            dropdown_servico,
            ft.ElevatedButton("Confirmar Agendamento", on_click=acao_agendar, width=250),
            status_agendamento
        )
        page.update()

    # ==========================================
    # AÇÕES DOS BOTÕES (COMUNICAÇÃO COM A API)
    # ==========================================
    def acao_login(e):
        nonlocal paciente_id_salvo  # Permite alterar a variável que criamos no início

        if not input_cpf.value or not input_nasc.value:
            status_login.value = "Por favor, preencha todos os campos!"
            status_login.color = ft.Colors.RED
            page.update()
            return

        payload = {
            "cpf": input_cpf.value,
            "data_nascimento": input_nasc.value
        }

        try:
            # Envia para a rota de login da API
            resposta = requests.post(f"{API_URL}/validar-paciente", json=payload)

            if resposta.status_code == 200:
                dados = resposta.json()
                # 💾 SALVA O ID DO PACIENTE NA MEMÓRIA DO APP
                paciente_id_salvo = dados["paciente_id"]

                # Avança para a próxima tela passando o nome do paciente
                mostrar_tela_agendamento(dados["nome"])
                page.update()
            else:
                erro = resposta.json()
                status_login.value = erro.get("detail", "Dados incorretos.")
                status_login.color = ft.Colors.RED
        except requests.exceptions.ConnectionError:
            status_login.value = "Erro: Não foi possível conectar ao servidor da API."
            status_login.color = ft.Colors.ORANGE_800
        page.update()

    def acao_agendar(e):
        if not input_data_consulta.value or not dropdown_servico.value:
            status_agendamento.value = "Preencha a data e o serviço!"
            status_agendamento.color = ft.Colors.RED
            page.update()
            return

        # Prepara os dados incluindo o ID que guardamos no login
        payload = {
            "paciente_id": paciente_id_salvo,  # Envia o ID guardado
            "data_consulta": input_data_consulta.value,
            "servico": dropdown_servico.value
        }

        try:
            # Envia para a rota de agendamento da API
            resposta = requests.post(f"{API_URL}/agendar", json=payload)

            if resposta.status_code == 200:
                status_agendamento.value = "Agendamento realizado com sucesso!"
                status_agendamento.color = ft.Colors.GREEN
                input_data_consulta.value = ""
                dropdown_servico.value = None
            else:
                status_agendamento.value = "Erro ao registrar o agendamento."
                status_agendamento.color = ft.Colors.RED
        except requests.exceptions.ConnectionError:
            status_agendamento.value = "Erro de conexão com o servidor."
            status_agendamento.color = ft.Colors.ORANGE_800
        page.update()

    # ==========================================
    # INICIALIZAÇÃO DO APP (TELA DE LOGIN)
    # ==========================================
    page.add(
        ft.Icon(ft.Icons.LOCK_PERSON, color=ft.Colors.BLUE_600, size=50),
        ft.Text("Identificação do Paciente", size=22, weight=ft.FontWeight.BOLD),
        ft.Text("Acesso exclusivo para moradores do bairro", size=12, color=ft.Colors.GREY_600),
        ft.Divider(),
        input_cpf,
        input_nasc,
        ft.ElevatedButton("Verificar Cadastro", on_click=acao_login, width=250),
        status_login
    )


if __name__ == "__main__":
    import os

    # Captura a porta que o Railway libera para o seu app
    porta = int(os.environ.get("PORT", 8080))
    # Inicia o Flet exclusivamente como servidor Web seguro
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=porta, host="0.0.0.0")