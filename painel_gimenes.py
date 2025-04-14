import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Laboratorial GIMENES",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Injetar CSS para alterar a cor dos widgets (por exemplo, azul)
# Estilo personalizado para mudar a cor das seleções nos filtros
st.markdown("""
    <style>
        /* Estilo para as opções selecionadas nos filtros */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #007EDB !important; /* azul */
            color: white !important;
            border-radius: 15px !important;
            font-weight: bold;
            padding: 1px 12px;
        }

        .stSelectbox [data-baseweb="select"] div[role="option"][aria-selected="true"] {
            background-color: #007BFF !important;
            color: white !important;
            font-weight: bold;
        }

        /* Bordas azuis e hover azul claro nos dropdowns */
        .stMultiSelect div[data-baseweb="select"] {
            border: 2px solid #7D7D7D !important;
            border-radius: 10px;
        }

        .stMultiSelect div[data-baseweb="select"]:hover {
            border-color: #66B2FF !important;
        }
    </style>
""", unsafe_allow_html=True)

# Tentar importar st_aggrid (opcional)
AGGRID_ENABLED = False
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_ENABLED = True
except ImportError:
    st.warning("Para uma tabela mais interativa, instale st-aggrid: pip install st-aggrid")


# Tentar importar st_aggrid (opcional)
AGGRID_ENABLED = False
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    AGGRID_ENABLED = True
except ImportError:
    st.warning("Para uma tabela mais interativa, instale st-aggrid: pip install st-aggrid")

# Função para carregar os dados
@st.cache_data
def load_data():
    try:
        df = pd.read_excel(".streamlit/0012.xlsx", sheet_name="Planilha")

        # Verificar colunas disponíveis
        # st.sidebar.write("Colunas disponíveis:", df.columns.tolist())

        # Convertendo colunas de data
        date_cols = ['Data Requisição', 'Data Execução']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

# Carregar dados
df = load_data()

if df.empty:
    st.warning("Nenhum dado foi carregado. Verifique o arquivo de entrada.")
    st.stop()

# Sidebar com filtros
st.sidebar.header("Filtros Interativos")

# Criar filtros dinamicamente baseado nas colunas disponíveis
available_columns = df.columns.tolist()

# Filtro por período temporal
if 'Data Requisição' in available_columns:
    min_date = df['Data Requisição'].min()
    max_date = df['Data Requisição'].max()
    date_range = st.sidebar.date_input(
        "Selecione o período",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['Data Requisição'] >= pd.to_datetime(start_date)) &
                (df['Data Requisição'] <= pd.to_datetime(end_date))]

# Filtro por "Número Autorização"
if 'Número Autorização' in available_columns:
    autorizacao_options = ['Todos'] + sorted(df['Número Autorização'].unique().tolist())
    selected_autorizacao = st.sidebar.multiselect(
        "Filtrar por Número Autorização",
        autorizacao_options,
        default='Todos'
    )

    if 'Todos' not in selected_autorizacao:
        df = df[df['Número Autorização'].isin(selected_autorizacao)]

# Filtro por categoria
categorical_cols = [col for col in ['Prestador', 'Nome Usuário', 'Unidade Origem', 'Crítica']
                   if col in available_columns]

for col in categorical_cols:
    options = ['Todos'] + sorted(df[col].unique().tolist())
    selected = st.sidebar.multiselect(
        f"Filtrar por {col}",
        options,
        default='Todos'
    )

    if 'Todos' not in selected:
        df = df[df[col].isin(selected)]

# Filtro por Código Procedimento
if 'Código Procedimento' in available_columns:
    codigos_proced = ['Todos'] + sorted(df['Código Procedimento'].astype(str).unique().tolist())
    selected_codigos = st.sidebar.multiselect(
        "Filtrar por Código Procedimento",
        codigos_proced,
        default='Todos'
    )

    if 'Todos' not in selected_codigos:
        df = df[df['Código Procedimento'].astype(str).isin(selected_codigos)]

# Seletor de colunas a serem exibidas
colunas_selecionadas = st.sidebar.multiselect(
    "Selecionar colunas para exibir na tabela",
    options=df.columns.tolist(),
    default=df.columns.tolist()  # todas visíveis por padrão
)
# Tabela Interativa (AgGrid ou padrão)
if AGGRID_ENABLED:
    gb = GridOptionsBuilder.from_dataframe(df[colunas_selecionadas])
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=False)
    gridOptions = gb.build()

    grid_response = AgGrid(
        df[colunas_selecionadas],
        gridOptions=gridOptions,
        height=400,
        width='100%',
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode='FILTERED_AND_SORTED',
        fit_columns_on_grid_load=True
    )

    filtered_df = pd.DataFrame(grid_response['data'])
else:
    filtered_df = df.copy()
    st.dataframe(filtered_df)

# Título do dashboard
st.title("📊 Dashboard Laboratorial GIMENES")
st.markdown("Visualizações interativas dos dados laboratoriais")

# Seção de Resumo de Valores
if not filtered_df.empty and 'Valor Total' in filtered_df.columns and 'Quantidade' in filtered_df.columns:
    total_valor = filtered_df['Valor Total'].sum()
    total_quantidade = filtered_df['Quantidade'].sum()

    st.subheader("Resumo de Valores")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Valor Total (R$)", value=f"{total_valor:,.2f}")

    with col2:
        st.metric(label="Procedimentos Realizados", value=f"{total_quantidade:,}")

# Gráfico de Barras Interativo
if 'NomeProcedimento' in available_columns:
    st.subheader("Top Procedimentos")
    top_n = st.slider("Selecione quantos procedimentos mostrar:", 5, 100, 20)

    proc_counts = filtered_df['NomeProcedimento'].value_counts().nlargest(top_n).reset_index()
    proc_counts.columns = ['Procedimento', 'Quantidade']

    fig = px.bar(
        proc_counts,
        x='Quantidade',
        y='Procedimento',
        orientation='h',
        color='Quantidade',
        color_continuous_scale='Viridis',
        title=f'Top {top_n} Procedimentos Mais Realizados'
    )

    fig.update_layout(
        hovermode='y unified',
        yaxis={'categoryorder': 'total ascending'},
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

# Gráfico de Linha por Data Execução
if 'Data Execução' in filtered_df.columns:
    st.subheader("Tendência por Data de Execução")

    exec_group = st.radio(
        "Agrupar Execuções por:",
        ['Dia', 'Semana', 'Mês', 'Ano'],
        horizontal=True,
        key='execucao_grouping'
    )

    if exec_group == 'Dia':
        filtered_df['PeriodoExec'] = filtered_df['Data Execução'].dt.date
    elif exec_group == 'Semana':
        filtered_df['PeriodoExec'] = filtered_df['Data Execução'].dt.to_period('W').dt.start_time.dt.date
    elif exec_group == 'Mês':
        filtered_df['PeriodoExec'] = filtered_df['Data Execução'].dt.to_period('M').dt.start_time.dt.date
    elif exec_group == 'Ano':
        filtered_df['PeriodoExec'] = filtered_df['Data Execução'].dt.to_period('Y').dt.start_time.dt.date

    exec_data = filtered_df.groupby('PeriodoExec').size().reset_index(name='Contagem')

    fig = px.line(
        exec_data,
        x='PeriodoExec',
        y='Contagem',
        title=f'Execuções por {exec_group}',
        markers=True
    )

    fig.update_layout(
        hovermode='x unified',
        xaxis_title=f'Período ({exec_group})',
        yaxis_title='Número de Execuções'
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Execuções: %{y}",
        line_width=2.5
    )

    st.plotly_chart(fig, use_container_width=True)

# Gráfico Temporal Interativo
if 'Data Requisição' in available_columns:
    st.subheader("Evolução Temporal")

    time_group = st.radio(
        "Agrupar por:",
        ['Dia', 'Semana', 'Mês', 'Ano'],
        horizontal=True
    )

    if time_group == 'Dia':
        filtered_df['Periodo'] = filtered_df['Data Requisição'].dt.date
    elif time_group == 'Semana':
        filtered_df['Periodo'] = filtered_df['Data Requisição'].dt.to_period('W').dt.start_time.dt.date
    elif time_group == 'Mês':
        filtered_df['Periodo'] = filtered_df['Data Requisição'].dt.to_period('M').dt.start_time.dt.date
    elif time_group == 'Ano':
        filtered_df['Periodo'] = filtered_df['Data Requisição'].dt.to_period('Y').dt.start_time.dt.date

    time_data = filtered_df.groupby('Periodo').size().reset_index(name='Contagem')

    fig = px.line(
        time_data,
        x='Periodo',
        y='Contagem',
        title=f'Requisição por {time_group}',
        markers=True
    )

    fig.update_layout(
        hovermode='x unified',
        xaxis_title=f'Período ({time_group})',
        yaxis_title='Número de Procedimentos'
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Procedimentos: %{y}",
        line_width=2.5
    )

    st.plotly_chart(fig, use_container_width=True)


# Boxplot Interativo
if 'Valor Total' in available_columns and 'NomeProcedimento' in available_columns:
    st.subheader("Distribuição de Valores por Procedimento")

    top_procs = st.slider("Selecione quantos procedimentos analisar:", 5, 50, 20, key="boxplot_slider")
    procs_list = filtered_df['NomeProcedimento'].value_counts().nlargest(top_procs).index.tolist()

    fig = px.box(
        filtered_df[filtered_df['NomeProcedimento'].isin(procs_list)],
        x='NomeProcedimento',
        y='Valor Total',
        color='NomeProcedimento',
        points="all",
        hover_data=['Número Autorização', 'Data Requisição']
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Procedimento",
        yaxis_title="Valor Total",
        height=600
    )

    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown("Dashboard desenvolvido com Streamlit e Plotly")
st.markdown("Dashboard desenvolvido Por Jaime Jose Cardozo Junior")
