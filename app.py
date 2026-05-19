import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================

st.set_page_config(
    page_title="Sistema Escolas",
    layout="wide"
)
st.markdown("""
<style>

/* Fundo geral */
.stApp {
    background-color: #f5f7fa;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Títulos */
h1 {
    color: #111827;
    font-weight: 800;
}

h2, h3 {
    color: #1f2937;
    font-weight: 700;
}

/* Cards e containers */
div[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

/* Botões */
.stButton > button {
    background-color: #111827;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 18px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #1f2937;
    color: white;
}

/* Inputs */
input, textarea {
    border-radius: 10px !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-weight: 700;
    color: #111827;
}

/* Tabelas */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Alertas */
div[data-testid="stAlert"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# BANCO DE DADOS
# =========================

conn = sqlite3.connect("sistema_escolas.db", check_same_thread=False)
cursor = conn.cursor()

def gerar_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")

    output.seek(0)
    return output
    
def gerar_pdf(servicos, escola_nome):

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)

    largura, altura = A4

    # ==========================================
    # TÍTULO
    # ==========================================

    pdf.setFont("Helvetica-Bold", 18)

    pdf.drawString(
        50,
        altura - 50,
        f"Relatório - {escola_nome}"
    )

    # ==========================================
    # CABEÇALHO
    # ==========================================

    pdf.setFont("Helvetica-Bold", 10)

    y = altura - 100

    pdf.drawString(50, y, "Funcionário")
    pdf.drawString(180, y, "Data")
    pdf.drawString(280, y, "Descrição")
    pdf.drawString(500, y, "Valor")

    y -= 20

    total_geral = 0

    pdf.setFont("Helvetica", 9)

    # ==========================================
    # SERVIÇOS
    # ==========================================

    for _, row in servicos.iterrows():

        pdf.drawString(
            50,
            y,
            str(row["funcionario"])
        )

        pdf.drawString(
            180,
            y,
            str(row["data"])
        )

        descricao = str(row["descricao"])[:35]

        pdf.drawString(
            280,
            y,
            descricao
        )

        valor = float(row["valor"])

        pdf.drawString(
            500,
            y,
            f"R$ {valor:.2f}"
        )

        total_geral += valor

        y -= 18

        # Nova página
        if y < 60:

            pdf.showPage()

            y = altura - 50

    # ==========================================
    # TOTAL
    # ==========================================

    y -= 20

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(
        50,
        y,
        f"Valor Total: R$ {total_geral:.2f}"
    )

    pdf.save()

    buffer.seek(0)

    return buffer

# =========================
# TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS escolas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    ativo INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    ativo INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS configuracoes (
    id INTEGER PRIMARY KEY,
    valor_dia_util REAL,
    valor_final_semana REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS servicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escola_id INTEGER,
    funcionario_id INTEGER,
    data TEXT,
    descricao TEXT,
    valor REAL
)
""")

# Inserir configuração padrão
cursor.execute("SELECT * FROM configuracoes WHERE id = 1")
config = cursor.fetchone()

if not config:
    cursor.execute("""
    INSERT INTO configuracoes (
        id,
        valor_dia_util,
        valor_final_semana
    ) VALUES (1, 160, 250)
    """)
    conn.commit()

    
# =========================
# MENU LATERAL
# =========================

st.sidebar.markdown("## Sistema Escolas")
st.sidebar.markdown("Gestão de serviços escolares")
st.sidebar.divider()

menu = st.sidebar.radio(
    "Menu",
    [
        "Dashboard Geral",
        "Página Principal",
        "Painel Administrativo"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Versão 1.0 - Sistema local")

# =========================================================
# DASHBOARD GERAL
# =========================================================

if menu == "Dashboard Geral":

    st.title("Dashboard Geral")
    st.caption("Visão consolidada dos serviços, valores e produtividade.")

    total_escolas = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM escolas",
        conn
    ).iloc[0]["total"]

    total_funcionarios = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM funcionarios",
        conn
    ).iloc[0]["total"]

    total_servicos = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM servicos",
        conn
    ).iloc[0]["total"]

    valor_total = pd.read_sql_query(
        "SELECT COALESCE(SUM(valor), 0) AS total FROM servicos",
        conn
    ).iloc[0]["total"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Escolas Cadastradas", int(total_escolas))
    c2.metric("Funcionários Cadastrados", int(total_funcionarios))
    c3.metric("Serviços Executados", int(total_servicos))
    c4.metric("Valor Total Pago", f"R$ {valor_total:,.2f}")

    st.divider()

    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:

        st.subheader("Valor Pago por Escola")

        valor_por_escola = pd.read_sql_query("""
        SELECT
            escolas.nome AS Escola,
            COALESCE(SUM(servicos.valor), 0) AS Total
        FROM escolas
        LEFT JOIN servicos
            ON servicos.escola_id = escolas.id
        GROUP BY escolas.nome
        ORDER BY Total DESC
        """, conn)

        if valor_por_escola.empty:
            st.info("Nenhuma informação disponível.")
        else:
            st.bar_chart(
                valor_por_escola.set_index("Escola")["Total"]
            )

    with col_graf2:

        st.subheader("Serviços por Funcionário")

        servicos_por_funcionario = pd.read_sql_query("""
        SELECT
            funcionarios.nome AS Funcionário,
            COUNT(servicos.id) AS Total
        FROM funcionarios
        LEFT JOIN servicos
            ON servicos.funcionario_id = funcionarios.id
        GROUP BY funcionarios.nome
        ORDER BY Total DESC
        """, conn)

        if servicos_por_funcionario.empty:
            st.info("Nenhuma informação disponível.")
        else:
            st.bar_chart(
                servicos_por_funcionario.set_index("Funcionário")["Total"]
            )

    st.divider()

    col_tab1, col_tab2 = st.columns(2)

    with col_tab1:

        st.subheader("Ranking de Escolas")

        ranking_escolas = pd.read_sql_query("""
        SELECT
            escolas.nome AS Escola,
            COUNT(servicos.id) AS Total_Serviços,
            COALESCE(SUM(servicos.valor), 0) AS Valor_Total
        FROM escolas
        LEFT JOIN servicos
            ON servicos.escola_id = escolas.id
        GROUP BY escolas.nome
        ORDER BY Valor_Total DESC
        """, conn)

        st.dataframe(
            ranking_escolas,
            use_container_width=True
        )

    with col_tab2:

        st.subheader("Ranking de Funcionários")

        ranking_funcionarios = pd.read_sql_query("""
        SELECT
            funcionarios.nome AS Funcionário,
            COUNT(servicos.id) AS Total_Serviços,
            COALESCE(SUM(servicos.valor), 0) AS Valor_Total
        FROM funcionarios
        LEFT JOIN servicos
            ON servicos.funcionario_id = funcionarios.id
        GROUP BY funcionarios.nome
        ORDER BY Valor_Total DESC
        """, conn)

        st.dataframe(
            ranking_funcionarios,
            use_container_width=True
        )

# =========================================================
# PAINEL ADMINISTRATIVO
# =========================================================

if menu == "Painel Administrativo":

    st.title("Painel Administrativo")
    st.caption("Gerencie escolas, funcionários e valores padrão dos serviços.")

    aba1, aba2, aba3 = st.tabs([
        "Escolas",
        "Funcionários",
        "Valores"
    ])

    # =====================================================
    # ESCOLAS
    # =====================================================

    with aba1:

        st.subheader("Cadastro de Escolas")

        with st.form("form_escola"):

            nome_escola = st.text_input("Nome da Escola")

            ativo_escola = st.checkbox(
                "Escola Ativa",
                value=True
            )

            salvar_escola = st.form_submit_button(
                "Salvar Escola"
            )

            if salvar_escola:

                cursor.execute("""
                INSERT INTO escolas (
                    nome,
                    ativo
                ) VALUES (?, ?)
                """, (
                    nome_escola,
                    int(ativo_escola)
                ))

                conn.commit()

                st.success("Escola cadastrada!")

        st.divider()

        escolas = pd.read_sql_query(
            "SELECT * FROM escolas",
            conn
        )

        st.dataframe(escolas)
    
        if not escolas.empty:

            with st.expander("Editar ou Excluir Escola", expanded=False):

                escola_id_editar = st.selectbox(
                    "Selecione a escola pelo ID",
                    escolas["id"].tolist(),
                    key="select_escola_admin"
                )

                escola_selecionada = escolas[
                    escolas["id"] == escola_id_editar
                ].iloc[0]

                with st.form("form_editar_escola"):

                    novo_nome_escola = st.text_input(
                        "Nome da Escola",
                        value=escola_selecionada["nome"]
                    )

                    novo_status_escola = st.checkbox(
                        "Escola Ativa",
                        value=bool(escola_selecionada["ativo"])
                    )

                    col_salvar, col_excluir = st.columns(2)

                    with col_salvar:
                        salvar_edicao_escola = st.form_submit_button(
                            "Salvar Alterações"
                        )

                    with col_excluir:
                        excluir_escola = st.form_submit_button(
                            "Excluir Escola"
                        )

                    if salvar_edicao_escola:

                        cursor.execute("""
                        UPDATE escolas
                        SET nome = ?, ativo = ?
                        WHERE id = ?
                        """, (
                            novo_nome_escola,
                            int(novo_status_escola),
                            int(escola_id_editar)
                        ))

                        conn.commit()

                        st.success("Escola atualizada com sucesso!")
                        st.rerun()

                    if excluir_escola:

                        verifica_servicos = pd.read_sql_query("""
                        SELECT COUNT(*) AS total
                        FROM servicos
                        WHERE escola_id = ?
                        """, conn, params=(int(escola_id_editar),))

                        total_servicos = verifica_servicos.iloc[0]["total"]

                        if total_servicos > 0:

                            st.error(
                                "Não é possível excluir esta escola porque existem serviços cadastrados. "
                                "Utilize a opção Inativar."
                            )

                        else:

                            cursor.execute("""
                            DELETE FROM escolas
                            WHERE id = ?
                            """, (
                                int(escola_id_editar),
                            ))

                            conn.commit()

                            st.success("Escola excluída com sucesso!")
                            st.rerun()

    # =====================================================
    # FUNCIONÁRIOS
    # =====================================================

    with aba2:

        st.subheader("Cadastro de Funcionários")

        with st.form("form_funcionario"):

            nome_funcionario = st.text_input(
                "Nome do Funcionário"
            )

            ativo_funcionario = st.checkbox(
                "Funcionário Ativo",
                value=True
            )

            salvar_funcionario = st.form_submit_button(
                "Salvar Funcionário"
            )

            if salvar_funcionario:

                cursor.execute("""
                INSERT INTO funcionarios (
                    nome,
                    ativo
                ) VALUES (?, ?)
                """, (
                    nome_funcionario,
                    int(ativo_funcionario)
                ))

                conn.commit()

                st.success("Funcionário cadastrado!")

        st.divider()

        funcionarios = pd.read_sql_query(
            "SELECT * FROM funcionarios",
            conn
        )

        st.dataframe(funcionarios)

        if not funcionarios.empty:

            with st.expander("Editar ou Excluir Funcionário", expanded=False):

                funcionario_id_editar = st.selectbox(
                    "Selecione o funcionário pelo ID",
                    funcionarios["id"].tolist(),
                    key="select_funcionario_admin"
                )

                funcionario_selecionado = funcionarios[
                    funcionarios["id"] == funcionario_id_editar
                ].iloc[0]

                with st.form("form_editar_funcionario"):

                    novo_nome_funcionario = st.text_input(
                        "Nome do Funcionário",
                        value=funcionario_selecionado["nome"]
                    )

                    novo_status_funcionario = st.checkbox(
                        "Funcionário Ativo",
                        value=bool(funcionario_selecionado["ativo"])
                    )

                    col_salvar_func, col_excluir_func = st.columns(2)

                    with col_salvar_func:
                        salvar_edicao_funcionario = st.form_submit_button(
                            "Salvar Alterações"
                        )

                    with col_excluir_func:
                        excluir_funcionario = st.form_submit_button(
                            "Excluir Funcionário"
                        )

                    if salvar_edicao_funcionario:

                        cursor.execute("""
                        UPDATE funcionarios
                        SET nome = ?, ativo = ?
                        WHERE id = ?
                        """, (
                            novo_nome_funcionario,
                            int(novo_status_funcionario),
                            int(funcionario_id_editar)
                        ))

                        conn.commit()

                        st.success("Funcionário atualizado com sucesso!")
                        st.rerun()

                    if excluir_funcionario:

                        verifica_servicos = pd.read_sql_query("""
                        SELECT COUNT(*) AS total
                        FROM servicos
                        WHERE funcionario_id = ?
                        """, conn, params=(int(funcionario_id_editar),))

                        total_servicos = verifica_servicos.iloc[0]["total"]

                        if total_servicos > 0:

                            st.error(
                                "Não é possível excluir este funcionário porque existem serviços cadastrados. "
                                "Utilize a opção Inativar."
                            )

                        else:

                            cursor.execute("""
                            DELETE FROM funcionarios
                            WHERE id = ?
                            """, (
                                int(funcionario_id_editar),
                            ))

                            conn.commit()

                            st.success("Funcionário excluído com sucesso!")
                            st.rerun()

    # =====================================================
    # VALORES
    # =====================================================

    with aba3:

        st.subheader("Configuração de Valores")

        config = pd.read_sql_query(
            "SELECT * FROM configuracoes",
            conn
        )

        valor_util = config.iloc[0]["valor_dia_util"]
        valor_fim = config.iloc[0]["valor_final_semana"]

        with st.form("form_valores"):

            novo_util = st.number_input(
                "Valor Dia Útil",
                value=float(valor_util)
            )

            novo_fim = st.number_input(
                "Valor Final de Semana",
                value=float(valor_fim)
            )

            salvar_valores = st.form_submit_button(
                "Salvar Valores"
            )

            if salvar_valores:

                cursor.execute("""
                UPDATE configuracoes
                SET
                    valor_dia_util = ?,
                    valor_final_semana = ?
                WHERE id = 1
                """, (
                    novo_util,
                    novo_fim
                ))

                conn.commit()

                st.success("Valores atualizados!")

# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

if menu == "Página Principal":

    st.title("Gestão de Serviços por Escola")
    st.caption("Selecione uma escola para cadastrar, consultar e resumir os serviços.")

    col1, col2 = st.columns([1, 3])

    # =====================================================
    # COLUNA ESCOLAS
    # =====================================================

    with col1:

        st.subheader("Escolas")

        escolas = pd.read_sql_query("""
        SELECT * FROM escolas
        WHERE ativo = 1
        """, conn)

        for index, escola in escolas.iterrows():

            if st.button(
                escola["nome"],
                use_container_width=True
                ):

                st.session_state["escola_id"] = escola["id"]
                st.session_state["escola_nome"] = escola["nome"]

    # =====================================================
    # COLUNA DIREITA
    # =====================================================

    with col2:

        st.subheader("Serviços da Escola")

        if "escola_id" not in st.session_state:

            st.info(
                "Clique em uma escola para visualizar os serviços."
            )

        else:

            escola_id = st.session_state["escola_id"]
            escola_nome = st.session_state["escola_nome"]

            st.success(f"Escola Selecionada: {escola_nome}")

            # ==========================================
            # CADASTRO DE SERVIÇO
            # ==========================================

            with st.expander("Cadastrar Serviço", expanded=False):

                funcionarios = pd.read_sql_query("""
                SELECT * FROM funcionarios
                WHERE ativo = 1
                ORDER BY nome
                """, conn)

                if funcionarios.empty:
                    st.warning("Cadastre ao menos um funcionário ativo.")
                else:
                    nomes_funcionarios = funcionarios["nome"].tolist()

                    with st.form("form_servico"):

                        funcionario_nome = st.selectbox(
                            "Funcionário",
                            nomes_funcionarios
                        )

                        data_servico = st.date_input(
                            "Data do Serviço"
                        )

                        descricao = st.text_area(
                            "Descrição do Serviço"
                        )

                        config = pd.read_sql_query("""
                        SELECT * FROM configuracoes
                        WHERE id = 1
                        """, conn)

                        valor_util = config.iloc[0]["valor_dia_util"]
                        valor_fim = config.iloc[0]["valor_final_semana"]

                        if data_servico.weekday() >= 5:
                            valor_padrao = valor_fim
                        else:
                            valor_padrao = valor_util

                        valor = st.number_input(
                            "Valor",
                            value=float(valor_padrao),
                            step=10.0
                        )

                        salvar_servico = st.form_submit_button(
                            "Salvar Serviço"
                        )

                        if salvar_servico:

                            funcionario_id = funcionarios[
                                funcionarios["nome"] == funcionario_nome
                            ]["id"].iloc[0]

                            cursor.execute("""
                            INSERT INTO servicos (
                                escola_id,
                                funcionario_id,
                                data,
                                descricao,
                                valor
                            ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                int(escola_id),
                                int(funcionario_id),
                                data_servico.strftime("%Y-%m-%d"),
                                descricao,
                                float(valor)
                            ))

                            conn.commit()

                            st.success("Serviço cadastrado com sucesso!")
                            st.rerun()

            # ==========================================
            # BOTÃO RESUMO
            # ==========================================

            # abrir_resumo = st.button("Resumo")

            # ==========================================
            # LISTA SERVIÇOS
            # ==========================================

            st.divider()

            filtro = st.selectbox(
                "Ordenar Serviços",
                [
                    "Mais recente",
                    "Mais antigo"
                ]
            )

            if filtro == "Mais recente":
                ordem = "DESC"
            else:
                ordem = "ASC"

            servicos = pd.read_sql_query(f"""
            SELECT
                servicos.id,
                funcionarios.nome AS funcionario,
                servicos.data,
                servicos.descricao,
                servicos.valor
            FROM servicos
            INNER JOIN funcionarios
                ON funcionarios.id = servicos.funcionario_id
            WHERE servicos.escola_id = ?
            ORDER BY servicos.data {ordem}
            """, conn, params=(int(escola_id),))

            st.dataframe(
                servicos,
                use_container_width=True
            )

            if not servicos.empty:

                excel_file = gerar_excel(servicos)

                pdf_file = gerar_pdf(
                    servicos,
                    escola_nome
                )

                col_excel, col_pdf = st.columns(2)

                with col_excel:

                    st.download_button(
                        label="Baixar Excel",
                        data=excel_file,
                        file_name=f"servicos_{escola_nome}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                with col_pdf:

                    st.download_button(
                        label="Baixar PDF",
                        data=pdf_file,
                        file_name=f"relatorio_{escola_nome}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

            # ==========================================
            # EDITAR / EXCLUIR SERVIÇO
            # ==========================================

            if not servicos.empty:

                with st.expander("Editar ou Excluir Serviço", expanded=False):

                    servico_id = st.selectbox(
                        "Selecione o ID do serviço",
                        servicos["id"].tolist()
                    )

                    servico_selecionado = servicos[
                        servicos["id"] == servico_id
                    ].iloc[0]

                    funcionarios_ativos = pd.read_sql_query("""
                    SELECT * FROM funcionarios
                    WHERE ativo = 1
                    ORDER BY nome
                    """, conn)

                    lista_funcionarios = funcionarios_ativos["nome"].tolist()

                    funcionario_atual = servico_selecionado["funcionario"]

                    if funcionario_atual in lista_funcionarios:
                        indice_funcionario = lista_funcionarios.index(funcionario_atual)
                    else:
                        indice_funcionario = 0

                    with st.form("form_editar_servico"):

                        novo_funcionario = st.selectbox(
                            "Funcionário",
                            lista_funcionarios,
                            index=indice_funcionario
                        )

                        nova_data = st.date_input(
                            "Data",
                            value=pd.to_datetime(servico_selecionado["data"]).date()
                        )

                        nova_descricao = st.text_area(
                            "Descrição",
                            value=servico_selecionado["descricao"]
                        )

                        novo_valor = st.number_input(
                            "Valor",
                            value=float(servico_selecionado["valor"]),
                            step=10.0
                        )

                        col_editar, col_excluir = st.columns(2)

                        with col_editar:
                            salvar_edicao = st.form_submit_button(
                                "Salvar Alterações"
                            )

                        with col_excluir:
                            excluir_servico = st.form_submit_button(
                                "Excluir Serviço"
                            )

                        if salvar_edicao:

                            novo_funcionario_id = funcionarios_ativos[
                                funcionarios_ativos["nome"] == novo_funcionario
                            ]["id"].iloc[0]

                            cursor.execute("""
                            UPDATE servicos
                            SET
                                funcionario_id = ?,
                                data = ?,
                                descricao = ?,
                                valor = ?
                            WHERE id = ?
                            """, (
                                int(novo_funcionario_id),
                                nova_data.strftime("%Y-%m-%d"),
                                nova_descricao,
                                float(novo_valor),
                                int(servico_id)
                            ))

                            conn.commit()

                            st.success("Serviço atualizado com sucesso!")
                            st.rerun()

                        if excluir_servico:

                            cursor.execute("""
                            DELETE FROM servicos
                            WHERE id = ?
                            """, (
                                int(servico_id),
                            ))

                            conn.commit()

                            st.success("Serviço excluído com sucesso!")
                            st.rerun()

            # ==========================================
            # RESUMO
            # ==========================================

            with st.expander("Resumo da Escola", expanded=False):
                        
                    resumo = pd.read_sql_query("""
                    SELECT
                        funcionarios.nome AS Funcionário,
                        COUNT(servicos.id) AS Total_Serviços,
                        SUM(servicos.valor) AS Total_Recebido
                    FROM servicos

                    INNER JOIN funcionarios
                        ON funcionarios.id = servicos.funcionario_id

                    WHERE servicos.escola_id = ?

                    GROUP BY funcionarios.nome

                    ORDER BY Total_Recebido DESC
                    """, conn, params=(int(escola_id),))

                    if resumo.empty:

                        st.warning("Nenhum serviço cadastrado nesta escola.")

                    else:

                        # ==============================
                        # CARDS RESUMO
                        # ==============================

                        total_servicos = resumo["Total_Serviços"].sum()
                        total_pago = resumo["Total_Recebido"].sum()

                        c1, c2 = st.columns(2)

                        with c1:
                            st.metric(
                                "Total de Serviços",
                                total_servicos
                            )

                        with c2:
                            st.metric(
                                "Valor Total Pago",
                                f"R$ {total_pago:,.2f}"
                            )

                        st.divider()

                        # ==============================
                        # TABELA
                        # ==============================

                        st.dataframe(
                            resumo,
                            use_container_width=True
                        )

                        st.divider()

                        # ==============================
                        # GRÁFICO VALORES
                        # ==============================

                        st.subheader("Valores por Funcionário")

                        grafico_valores = resumo.set_index(
                            "Funcionário"
                        )["Total_Recebido"]

                        st.bar_chart(grafico_valores)

                        st.divider()

                        # ==============================
                        # GRÁFICO SERVIÇOS
                        # ==============================

                        st.subheader("Quantidade de Serviços")

                        grafico_servicos = resumo.set_index(
                            "Funcionário"
                        )["Total_Serviços"]

                        st.bar_chart(grafico_servicos)