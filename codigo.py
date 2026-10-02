import os
from datetime import datetime
from html import escape
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ARQUIVO = "base_lava_jato.csv"

COLUNAS = [
    "data",
    "nome_cliente",
    "placa",
    "ano_veiculo",
    "telefone_whatsapp",
    "modelo_veiculo",
    "cor",
    "tipo_servico",
    "tipo_lavagem",
    "data_servico",
    "valor_cobrado",
    "hora",
    "observacoes",
    "produtos_utilizados",
    "status_registro",
    "excluido_por",
    "motivo_exclusao",
    "data_exclusao",
]


def carregar_dados():
    """Carrega o CSV ou cria uma tabela vazia quando o arquivo não existe."""
    if os.path.exists(ARQUIVO):
        dados = pd.read_csv(ARQUIVO, dtype=str).fillna("")
    else:
        dados = pd.DataFrame(columns=COLUNAS)

    # Acrescenta colunas que possam faltar em uma base antiga.
    for coluna in COLUNAS:
        if coluna not in dados.columns:
            dados[coluna] = ""

    # Registros antigos, sem status, são considerados ativos.
    dados["status_registro"] = dados["status_registro"].replace("", "Ativo")

    return dados[COLUNAS]


def moeda(valor):
    try:
        valor_numero = float(valor)
    except (TypeError, ValueError):
        valor_numero = 0.0

    valor_formatado = f"{valor_numero:,.2f}"
    valor_formatado = valor_formatado.replace(",", "X")
    valor_formatado = valor_formatado.replace(".", ",")
    valor_formatado = valor_formatado.replace("X", ".")

    return f"R$ {valor_formatado}"


def data_br(texto):
    try:
        return datetime.strptime(str(texto)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return str(texto or "")


def texto_pdf(valor):
    texto = str(valor or "").strip()
    if not texto:
        return "Não informado"

    return escape(texto).replace("\n", "<br/>")


def gerar_fatura_pdf(registro, numero):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    estilos = getSampleStyleSheet()
    estilo_celula = estilos["BodyText"]
    estilo_celula.leading = 15

    story = [
        Paragraph("VT Lava Jato", estilos["Title"]),
        Spacer(1, 5 * mm),
        Paragraph(
            f"Comprovante de Serviço Nº {numero + 1}",
            estilos["Heading2"],
        ),
        Spacer(1, 5 * mm),
    ]

    dados_tabela = [
        [
            Paragraph("<b>Campo</b>", estilo_celula),
            Paragraph("<b>Informação</b>", estilo_celula),
        ],
        [
            "Cliente",
            Paragraph(texto_pdf(registro.get("nome_cliente")), estilo_celula),
        ],
        [
            "Telefone",
            Paragraph(texto_pdf(registro.get("telefone_whatsapp")), estilo_celula),
        ],
        [
            "Placa",
            Paragraph(texto_pdf(registro.get("placa")), estilo_celula),
        ],
        [
            "Veículo",
            Paragraph(texto_pdf(registro.get("modelo_veiculo")), estilo_celula),
        ],
        [
            "Ano",
            Paragraph(texto_pdf(registro.get("ano_veiculo")), estilo_celula),
        ],
        [
            "Cor",
            Paragraph(texto_pdf(registro.get("cor")), estilo_celula),
        ],
        [
            "Tipo de serviço",
            Paragraph(texto_pdf(registro.get("tipo_servico")), estilo_celula),
        ],
        [
            "Tipo de lavagem",
            Paragraph(texto_pdf(registro.get("tipo_lavagem")), estilo_celula),
        ],
        [
            "Data do serviço",
            Paragraph(data_br(registro.get("data_servico")), estilo_celula),
        ],
        [
            "Valor",
            Paragraph(moeda(registro.get("valor_cobrado")), estilo_celula),
        ],
        [
            "Produtos utilizados",
            Paragraph(
                texto_pdf(registro.get("produtos_utilizados")),
                estilo_celula,
            ),
        ],
        [
            "Observações",
            Paragraph(texto_pdf(registro.get("observacoes")), estilo_celula),
        ],
    ]

    tabela = Table(
        dados_tabela,
        colWidths=[45 * mm, 115 * mm],
        repeatRows=1,
    )

    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#167D4A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F2F7F4")],
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(tabela)
    doc.build(story)

    return buffer.getvalue()


st.set_page_config(
    page_title="VT Lava Jato",
    page_icon="🚘",
    layout="wide",
)

st.title("VT Lava Jato")

tabela_clientes = carregar_dados()

# ---------- Cadastrar cliente e registrar serviço ----------
st.header("Cadastrar Cliente / Registrar Serviço")

with st.form("form_cadastro", clear_on_submit=True):
    nome = st.text_input("Nome do cliente")
    placa = st.text_input("Placa do veículo")
    ano_veiculo = st.text_input("Ano do veículo")
    telefone_whatsapp = st.text_input("Telefone (WhatsApp)")
    modelo_veiculo = st.text_input("Modelo do veículo")
    cor = st.text_input("Cor")

    tipo_servico = st.selectbox(
        "Tipo de serviço",
        ["Lavagem", "Polimento", "Higienização Interna"],
    )

    tipo_lavagem = st.selectbox(
        "Tipo de lavagem",
        ["Simples", "Completa", "Não se aplica"],
    )

    data_servico = st.date_input("Data do serviço")
    valor_cobrado = st.number_input(
        "Valor cobrado",
        min_value=0.0,
        step=0.01,
        format="%.2f",
    )
    produtos_utilizados = st.text_input("Produtos utilizados")
    observacoes = st.text_area("Observações")

    enviado = st.form_submit_button("Cadastrar Cliente / Serviço")

# A criação do registro e o pd.concat ficam neste mesmo bloco.
if enviado:
    if not nome.strip() or not placa.strip():
        st.error("Preencha pelo menos o nome do cliente e a placa do veículo.")
    else:
        agora = datetime.now()

        novo_registro = {
            "data": agora.strftime("%Y-%m-%d"),
            "nome_cliente": nome.strip(),
            "placa": placa.strip().upper(),
            "ano_veiculo": ano_veiculo.strip(),
            "telefone_whatsapp": telefone_whatsapp.strip(),
            "modelo_veiculo": modelo_veiculo.strip(),
            "cor": cor.strip(),
            "tipo_servico": tipo_servico,
            "tipo_lavagem": tipo_lavagem,
            "data_servico": data_servico.strftime("%Y-%m-%d"),
            "valor_cobrado": str(valor_cobrado),
            "hora": agora.strftime("%H:%M"),
            "observacoes": observacoes.strip(),
            "produtos_utilizados": produtos_utilizados.strip(),
            "status_registro": "Ativo",
            "excluido_por": "",
            "motivo_exclusao": "",
            "data_exclusao": "",
        }

        tabela_clientes = pd.concat(
            [
                tabela_clientes,
                pd.DataFrame([novo_registro]),
            ],
            ignore_index=True, # type: ignore
        ) # type: ignore

        tabela_clientes.to_csv(ARQUIVO, index=False)
        st.success("Cliente e serviço cadastrados com sucesso!")

# Separa registros ativos dos que foram marcados como excluídos.
registros_ativos = tabela_clientes[
    tabela_clientes["status_registro"] != "Excluído"
].copy()

registros_excluidos = tabela_clientes[
    tabela_clientes["status_registro"] == "Excluído"
].copy()

# ---------- Pesquisar cliente e ver histórico ----------
st.header("Histórico")

nome_pesquisa = st.text_input("Pesquisar cliente pelo nome")

if nome_pesquisa:
    resultado = registros_ativos[
        registros_ativos["nome_cliente"].str.contains(
            nome_pesquisa,
            case=False,
            na=False,
            regex=False,
        )
    ]
    st.dataframe(resultado, use_container_width=True)
else:
    st.dataframe(registros_ativos, use_container_width=True)

# ---------- Excluir registro com justificativa ----------
st.header("Excluir registro do histórico")

if not registros_ativos.empty:
    indices_ativos = registros_ativos.index.tolist()

    with st.form("form_exclusao"):
        indice_exclusao = st.selectbox(
            "Selecione o registro que deseja excluir",
            options=indices_ativos,
            format_func=lambda indice: (
                f"{tabela_clientes.at[indice, 'nome_cliente']} — "
                f"{tabela_clientes.at[indice, 'placa']} — "
                f"{data_br(tabela_clientes.at[indice, 'data_servico'])}"
            ),
        )

        excluido_por = st.text_input(
            "Nome de quem está excluindo (obrigatório)"
        )
        motivo_exclusao = st.text_area(
            "Motivo da exclusão (obrigatório)"
        )

        confirmar_exclusao = st.form_submit_button(
            "Excluir do histórico"
        )

    if confirmar_exclusao:
        if not excluido_por.strip() or not motivo_exclusao.strip():
            st.error(
                "Informe quem está excluindo e o motivo. "
                "Os dois campos são obrigatórios."
            )
        else:
            agora = datetime.now()

            tabela_clientes.at[
                indice_exclusao, "status_registro"
            ] = "Excluído"
            tabela_clientes.at[
                indice_exclusao, "excluido_por"
            ] = excluido_por.strip()
            tabela_clientes.at[
                indice_exclusao, "motivo_exclusao"
            ] = motivo_exclusao.strip()
            tabela_clientes.at[
                indice_exclusao, "data_exclusao"
            ] = agora.strftime("%Y-%m-%d %H:%M:%S")

            tabela_clientes.to_csv(ARQUIVO, index=False)

            st.success(
                "Registro ocultado do histórico e mantido na base de dados."
            )
            st.rerun()
else:
    st.info("Não há registros ativos para excluir.")

# ---------- Consultar registros excluídos ----------
if not registros_excluidos.empty:
    with st.expander("Ver registros excluídos e motivos"):
        colunas_auditoria = [
            "nome_cliente",
            "placa",
            "data_servico",
            "status_registro",
            "excluido_por",
            "motivo_exclusao",
            "data_exclusao",
        ]

        st.dataframe(
            registros_excluidos[colunas_auditoria],
            use_container_width=True,
        )

# ---------- Dashboard: considera somente registros ativos ----------
st.header("Dashboard")

df = registros_ativos.copy()
df["valor_cobrado"] = pd.to_numeric(
    df["valor_cobrado"],
    errors="coerce",
).fillna(0)

col1, col2, col3 = st.columns(3)
col1.metric("Total de Clientes", df["nome_cliente"].nunique())
col2.metric("Total de Lavagens/Serviços", len(df))
col3.metric("Total Faturado", moeda(df["valor_cobrado"].sum()))

if not df.empty:
    por_tipo = df["tipo_lavagem"].value_counts().reset_index()
    por_tipo.columns = ["tipo_lavagem", "quantidade"]

    st.plotly_chart(
        px.bar(
            por_tipo,
            x="tipo_lavagem",
            y="quantidade",
            title="Serviços por tipo de lavagem",
        ),
        use_container_width=True,
    )

    df["mes"] = pd.to_datetime(
        df["data_servico"],
        errors="coerce",
    ).dt.strftime("%Y-%m")

    por_mes = (
        df.dropna(subset=["mes"])
        .groupby("mes", as_index=False)["valor_cobrado"]
        .sum()
    )

    if not por_mes.empty:
        st.plotly_chart(
            px.pie(
                por_mes,
                names="mes",
                values="valor_cobrado",
                title="Faturamento por mês",
            ),
            use_container_width=True,
        )

# ---------- Gerar e baixar PDF ----------
st.header("Gerar PDF")

if not registros_ativos.empty:
    indices_pdf = registros_ativos.index.tolist()

    registro_selecionado = st.selectbox(
        "Selecione um serviço para gerar o PDF",
        options=indices_pdf,
        format_func=lambda indice: (
            f"{tabela_clientes.at[indice, 'nome_cliente']} — "
            f"{data_br(tabela_clientes.at[indice, 'data_servico'])} — "
            f"{tabela_clientes.at[indice, 'placa']}"
        ),
    )

    registro = tabela_clientes.loc[registro_selecionado]

    pdf_bytes = gerar_fatura_pdf(
        registro,
        int(registro_selecionado),
    )

    nome_arquivo = (
        f"comprovante_{registro.get('placa', 'veiculo')}_"
        f"{registro.get('data_servico', 'servico')}.pdf"
    )
    nome_arquivo = nome_arquivo.replace("/", "-").replace("\\", "-")

    st.download_button(
        label="Baixar PDF do serviço selecionado",
        data=pdf_bytes,
        file_name=nome_arquivo,
        mime="application/pdf",
    )
else:
    st.info("Não há registros ativos para gerar um PDF.")