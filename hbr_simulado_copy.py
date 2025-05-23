#########################################################################
# Em caso de dúvidas, entrar em contato com marcos.trindade@hidrobr.com #
#########################################################################

import streamlit as st
import pandas as pd
import geopandas
import folium
from streamlit_folium import st_folium
import plotly.express as px
import zipfile
import tempfile
import os

# --- Paleta de Cores da Empresa ---
COLOR_PRIMARY = "#135D79"
COLOR_SECONDARY = "#169674"
COLOR_WHITE = "#FFFFFF"

# --- Definindo alturas fixas para as seções ---
MAP_SECTION_HEIGHT_PX = 365 # Mude conforme o tamanho do monitor
TOP_DATA_ROW_CONTENT_HEIGHT_PX = 270 # Mude conforme o tamanho do monitor


# --- Funções Auxiliares ---
def parse_pe_data(data_string: str) -> pd.DataFrame:
    """
    Analisa dados de Ponto de Encontro (PE) inseridos manualmente.

    Argumentos:
    data_string: Uma string onde cada linha representa um PE
    no formato "Nome | Latitude | Longitude".

    Retorna:
    Um DataFrame Pandas com colunas ['Nome', 'Latitude', 'Longitude'].
    """
    pes_list = []
    for line in data_string.strip().split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) == 3:
                try:
                    name = parts[0].strip()
                    lat = float(parts[1].strip().replace(',', '.'))
                    lon = float(parts[2].strip().replace(',', '.'))
                    pes_list.append({'Nome': name, 'Latitude': lat, 'Longitude': lon})
                except ValueError:
                    st.sidebar.warning(f"A linha '{line}' não pôde ser processada. Verifique o formato.")
            else:
                st.sidebar.warning(f"A linha '{line}' não tem o formato esperado (Nome | Lat | Lon).")
        else:
            st.sidebar.warning(f"A linha '{line}' não contém '|' como delimitador.")
    return pd.DataFrame(pes_list)

def load_pe_from_file(uploaded_file, file_type: str) -> pd.DataFrame:
    """
    Carrega dados de Ponto de Encontro (PE) de um arquivo enviado (XLSX ou Shapefile ZIP).

    Argumentos:
    uploaded_file: O arquivo enviado pelo usuário via st.file_uploader.
    file_type: Uma string que indica o tipo de arquivo ("xlsx" ou "shp").

    Retorna:
    Um DataFrame Pandas contendo dados de PE. Retorna um DataFrame vazio em caso de erro.
    """
    try:
        if file_type == "xlsx":
            df = pd.read_excel(uploaded_file)
        elif file_type == "shp":
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_zip_path = os.path.join(tmpdir, uploaded_file.name)
                with open(temp_zip_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                shp_file_path = None
                for item in os.listdir(tmpdir):
                    if item.endswith(".shp"):
                        shp_file_path = os.path.join(tmpdir, item)
                        break
                if not shp_file_path:
                    st.sidebar.error("Nenhum arquivo .shp encontrado no .zip.")
                    return pd.DataFrame()
                gdf = geopandas.read_file(shp_file_path)
                if gdf.crs is None:
                    st.sidebar.warning("Shapefile dos PEs não possui CRS definido. Assumindo WGS84 (EPSG:4326).")
                    gdf.set_crs("EPSG:4326", inplace=True, allow_override=True)
                elif gdf.crs.to_string() != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")
                df = pd.DataFrame()
                df['geometry'] = gdf.geometry
                df['Longitude'] = gdf.geometry.x
                df['Latitude'] = gdf.geometry.y
                for col in gdf.columns:
                    if col not in ['geometry', 'Longitude', 'Latitude']:
                        df[col] = gdf[col]
        else:
            return pd.DataFrame()

        st.session_state.uploaded_pe_df_columns = df.columns.tolist()
        return df

    except Exception as e:
        st.sidebar.error(f"Erro ao carregar o arquivo de PEs: {e}")
        return pd.DataFrame()

# --- Configurações Iniciais da Página ---
st.set_page_config(
    page_title=st.session_state.get("app_title", "Dashboard de Simulado PAE"),
    page_icon="📊",
    layout="wide"
)

# --- Sidebar para Inputs ---
st.sidebar.header("⚙️ Configurações e Entradas")

# 1. Configurações Gerais do Dashboard
st.sidebar.subheader("Identidade Visual e Títulos")
st.session_state.app_title = st.sidebar.text_input("Título Principal do Dashboard", st.session_state.get("app_title", "Painel de Acompanhamento de Simulado PAE"))
st.session_state.organizer_name = st.sidebar.text_input("Nome da Empresa Organizadora", st.session_state.get("organizer_name", "HIDROBR"))
st.session_state.organizer_logo_url = st.sidebar.text_input("URL do Logo da Organizadora", st.session_state.get("organizer_logo_url", "https://www.hidrobr.com/wp-content/uploads/2023/09/HidroBR_logo2.png"))
st.session_state.client_name = st.sidebar.text_input("Nome da Empresa Cliente", st.session_state.get("client_name", "Cliente Exemplo"))
st.session_state.client_logo_url = st.sidebar.text_input("URL do Logo do Cliente", st.session_state.get("client_logo_url", ""))


# 2. Definição dos Pontos de Encontro (PEs)
st.sidebar.subheader("Dados dos Pontos de Encontro (PEs)")
pe_input_method = st.sidebar.radio(
    "Origem dos dados dos PEs:",
    ("Digitar manualmente", "Upload de arquivo XLSX", "Upload de Shapefile (.zip)"),
    key="pe_input_method_key",
    index=st.session_state.get("pe_input_method_idx", 0)
)
st.session_state.pe_input_method_idx = ("Digitar manualmente", "Upload de arquivo XLSX", "Upload de Shapefile (.zip)").index(pe_input_method)


df_pe_initial = pd.DataFrame(columns=['Nome', 'Latitude', 'Longitude'])

if 'df_pe_configured' not in st.session_state:
    st.session_state.df_pe_configured = False

pe_data_processed = False

if pe_input_method == "Digitar manualmente":
    pe_data_raw_input = st.sidebar.text_area(
        "Insira os dados (Nome | Latitude | Longitude), um PE por linha:",
        st.session_state.get("pe_data_raw_input_val",
        """PE-01 | -18.47014348844529 |-48.00084814228885
PE-02 | -18.50159450324902 |-48.0039083745878
PE-03 | -18.47864034601005 |-48.01282682623281
PE-04 | -18.48928712436707 |-48.01440873625845
PE-05 | -18.48335530825562 |-48.02426248069505
PE-06 | -18.49047390337081 |-48.02520297845516
PE-07 | -18.47154420309602 |-48.03109044453952
PE-08 | -18.46368219065322 |-48.03398303645682
PE-09 | -18.4572357394792  |-48.04723660013522
PE-10 | -18.44340972401394 |-48.05247803717019
PE-11 | -18.42150573075635 |-48.03805226404172
PE-12 | -18.42031646572566 |-48.03021995399006
PE-13 | -18.4003536523609  |-48.00273004018321
PE-14 | -18.39917184805854 |-47.99555666899462
PE-15 | -18.41029250212749 |-47.98904858724354
PE-16 | -18.36797733633896 |-48.05208954154255"""),
        height=200,
        key="pe_data_raw_text_area"
    )
    st.session_state.pe_data_raw_input_val = pe_data_raw_input
    if st.sidebar.button("Processar PEs Manuais") or not st.session_state.df_pe_configured :
        if pe_data_raw_input:
            df_pe_initial = parse_pe_data(pe_data_raw_input)
            st.session_state.df_pe_initial_backup = df_pe_initial.copy()
            st.session_state.df_pe_configured = not df_pe_initial.empty
            pe_data_processed = True
            if not df_pe_initial.empty:
                st.sidebar.success(f"{len(df_pe_initial)} PEs processados manualmente.")
            else:
                 st.sidebar.warning("Nenhum PE processado. Verifique os dados e o formato.")


elif pe_input_method in ["Upload de arquivo XLSX", "Upload de Shapefile (.zip)"]:
    file_type_ext = "xlsx" if "XLSX" in pe_input_method else "shp"
    uploaded_pe_file = st.sidebar.file_uploader(
        f"Selecione o arquivo {file_type_ext.upper()}",
        type=["xlsx", "zip"] if file_type_ext == "shp" else ["xlsx"],
        key=f"pe_file_uploader_{file_type_ext}"
    )
    if uploaded_pe_file:
        raw_uploaded_df = load_pe_from_file(uploaded_pe_file, file_type_ext)
        if not raw_uploaded_df.empty:
            cols = raw_uploaded_df.columns.tolist()
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Mapeamento de Colunas do Arquivo de PEs:**")

            default_name_col_idx = cols.index("Nome") if "Nome" in cols else (cols.index("Name") if "Name" in cols else 0)
            default_lat_col_idx = cols.index("Latitude") if "Latitude" in cols else (cols.index("Lat") if "Lat" in cols else (1 if len(cols)>1 else 0) )
            default_lon_col_idx = cols.index("Longitude") if "Longitude" in cols else (cols.index("Lon") if "Lon" in cols else (cols.index("Lng") if "Lng" in cols else (2 if len(cols)>2 else 0)))

            name_col = st.sidebar.selectbox("Coluna para 'Nome' do PE:", cols, index=default_name_col_idx, key="pe_name_col_select")
            lat_col = st.sidebar.selectbox("Coluna para 'Latitude':", cols, index=default_lat_col_idx, key="pe_lat_col_select")
            lon_col = st.sidebar.selectbox("Coluna para 'Longitude':", cols, index=default_lon_col_idx, key="pe_lon_col_select")

            if st.sidebar.button("Processar PEs do Arquivo") or not st.session_state.df_pe_configured:
                try:
                    df_pe_initial = pd.DataFrame({
                        'Nome': raw_uploaded_df[name_col].astype(str),
                        'Latitude': pd.to_numeric(raw_uploaded_df[lat_col]),
                        'Longitude': pd.to_numeric(raw_uploaded_df[lon_col])
                    })
                    df_pe_initial.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                    st.session_state.df_pe_initial_backup = df_pe_initial.copy()
                    st.session_state.df_pe_configured = not df_pe_initial.empty
                    pe_data_processed = True
                    if not df_pe_initial.empty:
                        st.sidebar.success(f"{len(df_pe_initial)} PEs processados do arquivo.")
                    else:
                        st.sidebar.warning("Nenhum PE válido encontrado no arquivo após mapeamento.")
                except Exception as e:
                    st.sidebar.error(f"Erro ao mapear colunas: {e}")
                    st.session_state.df_pe_configured = False


if not pe_data_processed and 'df_pe_initial_backup' in st.session_state:
    df_pe_initial = st.session_state.df_pe_initial_backup.copy()

if df_pe_initial.empty and 'pe_data_raw_input_val' in st.session_state and not st.session_state.get('df_pe_configured', False):
    df_pe_initial = parse_pe_data(st.session_state.pe_data_raw_input_val)


current_pe_names = frozenset(df_pe_initial['Nome'].tolist()) if not df_pe_initial.empty else frozenset()
previous_pe_names = st.session_state.get('previous_pe_names_for_inputs', frozenset())

if current_pe_names != previous_pe_names:
    keys_to_delete = []
    for k in st.session_state.keys():
        if k.startswith('participantes_') or k.startswith('esperadas_') or k.startswith('widget_'):
            keys_to_delete.append(k)
    for k_del in keys_to_delete:
        del st.session_state[k_del]
    st.session_state.previous_pe_names_for_inputs = current_pe_names


if not df_pe_initial.empty:
    df_pe_initial.set_index('Nome', inplace=True)
    df_pe = df_pe_initial.copy()

    st.sidebar.markdown("---")
    st.sidebar.subheader("Contagem por Ponto de Encontro")
    for pe_name in df_pe.index:
        with st.sidebar.expander(f"PE: {pe_name}", expanded=False):
            participantes_key_ss = f'participantes_{pe_name}'
            esperadas_key_ss = f'esperadas_{pe_name}'
            participantes_key_widget = f'widget_participantes_{pe_name}'
            esperadas_key_widget = f'widget_esperadas_{pe_name}'

            if participantes_key_ss not in st.session_state:
                st.session_state[participantes_key_ss] = 0
            if esperadas_key_ss not in st.session_state:
                st.session_state[esperadas_key_ss] = 1

            current_participantes = st.number_input(
                f"Total de Participantes",
                min_value=0,
                value=st.session_state[participantes_key_ss],
                key=participantes_key_widget,
                help=f"Número de participantes que chegaram ao PE {pe_name}"
            )
            st.session_state[participantes_key_ss] = current_participantes

            current_esperadas = st.number_input(
                f"Número de Pessoas Esperadas",
                min_value=0,
                value=st.session_state[esperadas_key_ss],
                key=esperadas_key_widget,
                help=f"Número de pessoas que eram esperadas no PE {pe_name}"
            )
            st.session_state[esperadas_key_ss] = current_esperadas

            df_pe.loc[pe_name, 'Total de Participantes'] = st.session_state[participantes_key_ss]
            df_pe.loc[pe_name, 'Número de Pessoas Esperadas'] = st.session_state[esperadas_key_ss]
    
    def calcular_efetividade(row):
        """Calcula a eficácia com base nos participantes e nas pessoas esperadas."""
        if row['Número de Pessoas Esperadas'] > 0:
            return (row['Total de Participantes'] / row['Número de Pessoas Esperadas']) * 100
        return 0.0
    df_pe['Efetividade (%)'] = df_pe.apply(calcular_efetividade, axis=1)

else:
    df_pe = pd.DataFrame(columns=['Latitude', 'Longitude', 'Total de Participantes', 'Número de Pessoas Esperadas', 'Efetividade (%)'])


st.sidebar.markdown("---")
st.sidebar.subheader("Upload da Zona de Autossalvamento (ZAS)")
uploaded_zas_file = st.sidebar.file_uploader(
    "Selecione o arquivo Shapefile (.zip contendo .shp, .dbf, .shx, etc.)",
    type=["zip"],
    key="zas_uploader"
)


# --- Layout Principal da Página ---

row1_col1, row1_col2, row1_col3 = st.columns([1, 3, 1])
with row1_col1:
    if st.session_state.get("organizer_logo_url"):
        st.image(st.session_state.organizer_logo_url, width=100)
    st.caption(st.session_state.get("organizer_name", ""))

with row1_col2:
    st.title(st.session_state.get("app_title", "Painel de Acompanhamento"))

with row1_col3:
    if st.session_state.get("client_logo_url"):
        st.image(st.session_state.client_logo_url, width=100)
    st.caption(st.session_state.get("client_name", ""))


if not df_pe.empty:
    col_geral_metrics, col_single_pe, col_chart = st.columns([0.07, 0.13, 0.5])

    with col_geral_metrics:
        st.markdown("###### Visão Geral")
        total_participantes_geral = df_pe['Total de Participantes'].sum()
        total_esperados_geral = df_pe['Número de Pessoas Esperadas'].sum()
        efetividade_geral = (total_participantes_geral / total_esperados_geral * 100) if total_esperados_geral > 0 else 0

        st.metric(label="Total Participantes", value=f"{total_participantes_geral:,.0f}")
        st.metric(label="Total Esperado", value=f"{total_esperados_geral:,.0f}")
        st.metric(label="Efetividade Geral", value=f"{efetividade_geral:.2f}%")

    with col_single_pe:
        st.markdown("###### Visão Detalhada - Ponto de Encontro")
        if not df_pe.empty:
            pe_names_list = df_pe.index.tolist()
            if not pe_names_list:
                st.info("Nenhum PE disponível para seleção.")
            else:
                current_selection_idx = 0
                if 'selected_pe_name_dashboard' in st.session_state and st.session_state.selected_pe_name_dashboard in pe_names_list:
                    current_selection_idx = pe_names_list.index(st.session_state.selected_pe_name_dashboard)
                else:
                    st.session_state.selected_pe_name_dashboard = pe_names_list[0]

                selected_pe_name = st.selectbox(
                    "Selecione o Ponto de Encontro:",
                    options=pe_names_list,
                    index=current_selection_idx,
                    key="selected_pe_name_dashboard_selectbox"
                )
                st.session_state.selected_pe_name_dashboard = selected_pe_name

                if selected_pe_name:
                    row_pe_data = df_pe.loc[selected_pe_name]
                    st.markdown(f"<div class='pe-card'><h6>{selected_pe_name}</h6>", unsafe_allow_html=True)
                    efetividade_val = row_pe_data['Efetividade (%)']
                    st.progress(int(efetividade_val))
                    st.caption(f"Efetividade: {efetividade_val:.2f}%")

                    card_metric_col1, card_metric_col2 = st.columns(2)
                    with card_metric_col1:
                        st.markdown(f"<p class='pe-card-metric-label'>Participantes</p>"
                                    f"<p class='pe-card-metric-value'>{row_pe_data['Total de Participantes']:,.0f}</p>",
                                    unsafe_allow_html=True)
                    with card_metric_col2:
                        st.markdown(f"<p class='pe-card-metric-label'>Esperados</p>"
                                    f"<p class='pe-card-metric-value pe-card-metric-value-alt'>{row_pe_data['Número de Pessoas Esperadas']:,.0f}</p>",
                                    unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Pontos de Encontro não configurados.")


    with col_chart:
        st.markdown("###### Participantes: Realizado vs. Esperado (Todos PEs)")
        df_melted = df_pe.reset_index().melt(
            id_vars=['Nome'],
            value_vars=['Total de Participantes', 'Número de Pessoas Esperadas'],
            var_name='Métrica', value_name='Quantidade'
        )
        fig_participantes_esperados = px.bar(
            df_melted, x='Nome', y='Quantidade', color='Métrica', barmode='group',
            color_discrete_map={
                'Total de Participantes': COLOR_SECONDARY,
                'Número de Pessoas Esperadas': COLOR_PRIMARY
            },
            labels={'Nome': 'Ponto de Encontro', 'Quantidade': 'Número de Pessoas'}
        )
        fig_participantes_esperados.update_layout(
            height=TOP_DATA_ROW_CONTENT_HEIGHT_PX,
            xaxis_title=None, yaxis_title="Número de Pessoas",
            plot_bgcolor=COLOR_WHITE, paper_bgcolor=COLOR_WHITE,
            font_color=COLOR_PRIMARY,
            xaxis=dict(tickfont=dict(color=COLOR_PRIMARY)),
            yaxis=dict(tickfont=dict(color=COLOR_PRIMARY)),
            legend_title_text='',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=COLOR_PRIMARY)),
            margin=dict(t=20, b=0, l=0, r=0)
        )
        fig_participantes_esperados.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='LightGrey')
        st.plotly_chart(fig_participantes_esperados, use_container_width=True)

    st.markdown("---")

    st.subheader("🗺️ Mapa Interativo dos Pontos de Encontro")
    if not df_pe.empty:
        map_center_lat = df_pe['Latitude'].mean()
        map_center_lon = df_pe['Longitude'].mean()
        zoom_start = 11
    else:
        map_center_lat = -18.45 
        map_center_lon = -48.00 
        zoom_start = 11

    m = folium.Map(
        location=[map_center_lat, map_center_lon],
        zoom_start=zoom_start,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
    )

    gdf_zas = None
    if uploaded_zas_file is not None:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_zip_path = os.path.join(tmpdir, uploaded_zas_file.name)
                with open(temp_zip_path, "wb") as f:
                    f.write(uploaded_zas_file.getvalue())

                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                   zip_ref.extractall(tmpdir)

                shp_file_path = None
                for item in os.listdir(tmpdir):
                     if item.endswith(".shp"):
                        shp_file_path = os.path.join(tmpdir, item)
                        break
                
                if shp_file_path:
                   gdf_zas = geopandas.read_file(shp_file_path)
                   if gdf_zas.crs is None:
                        st.sidebar.warning("Shapefile da ZAS não possui CRS definido. Assumindo WGS84 (EPSG:4326).")
                        gdf_zas.set_crs("EPSG:4326", inplace=True, allow_override=True)
                   elif gdf_zas.crs.to_string() != "EPSG:4326":
                        try:
                            gdf_zas = gdf_zas.to_crs("EPSG:4326")
                        except Exception as e_crs:
                            st.sidebar.error(f"Erro ao reprojetar ZAS para EPSG:4326: {e_crs}")
                            gdf_zas = None
                   if gdf_zas is not None and isinstance(gdf_zas, geopandas.GeoDataFrame) and not gdf_zas.empty:
                        attribute_columns = [col for col in gdf_zas.columns if col != gdf_zas.geometry.name]
                        style_zas = {'fillColor': '#00c5ff', 'color': '#e41a1c', 'weight': 0.7, 'fillOpacity': 0.5}
                        folium.GeoJson(
                            gdf_zas, name='Zona de Autossalvamento (ZAS)', style_function=lambda x: style_zas,
                            tooltip=folium.GeoJsonTooltip(fields=attribute_columns, aliases=[f"{col}:" for col in attribute_columns], sticky=False)
                        ).add_to(m)
                elif uploaded_zas_file and (gdf_zas is None or (isinstance(gdf_zas, geopandas.GeoDataFrame) and gdf_zas.empty)):
                     st.sidebar.warning("O GeoDataFrame da ZAS está vazio, não é válido ou não pôde ser processado.")

        except Exception as e:
            st.sidebar.error(f"Erro ao processar o shapefile da ZAS: {e}")
            gdf_zas = None

    for idx_name, row_pe_map in df_pe.iterrows():
        popup_html = f"""<div style="font-family: Arial, sans-serif; font-size: 12px;">
            <strong>PE:</strong> {idx_name}<br>
            <strong>Participantes:</strong> {row_pe_map['Total de Participantes']:,.0f}<br>
            <strong>Esperados:</strong> {row_pe_map['Número de Pessoas Esperadas']:,.0f}<br>
            <strong>Efetividade:</strong> {row_pe_map['Efetividade (%)']:.2f}%</div>"""
        efetividade_valor = row_pe_map['Efetividade (%)']
        pe_icon_color = 'gray'
        pe_icon_symbol = 'minus-sign' 
        if row_pe_map['Número de Pessoas Esperadas'] > 0 or row_pe_map['Total de Participantes'] > 0 :
            if efetividade_valor >= 80: pe_icon_color, pe_icon_symbol = 'green', 'ok-sign'
            elif efetividade_valor >= 50: pe_icon_color, pe_icon_symbol = 'orange', 'info-sign'
            else: pe_icon_color, pe_icon_symbol = 'red', 'remove-sign'

        folium.Marker(
            location=[row_pe_map['Latitude'], row_pe_map['Longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{idx_name} | Efetividade: {row_pe_map['Efetividade (%)']:.1f}%",
            icon=folium.Icon(color=pe_icon_color, icon=pe_icon_symbol, prefix='glyphicon')
        ).add_to(m)

    if gdf_zas is not None and isinstance(gdf_zas, geopandas.GeoDataFrame) and not gdf_zas.empty:
        folium.LayerControl().add_to(m)
    
    # Pass MAP_SECTION_HEIGHT_PX to st_folium. CSS will also enforce this.
    st_folium(m, width=None, height=MAP_SECTION_HEIGHT_PX, use_container_width=True)

else:
    st.info("👈 Configure os Pontos de Encontro na barra lateral para visualizar o dashboard.")

custom_css = f"""
<style>
    .main .block-container {{
        padding-top: 1.06rem; 
        padding-bottom: 1rem;
    }}
    div[data-testid="stVerticalBlock"] div[data-testid="stMarkdownContainer"] h6 {{
        margin-top: 0rem; 
        margin-bottom: 0.1rem; 
        color: {COLOR_PRIMARY}; 
        font-size: 1.05em; 
    }}
    div[data-testid="stVerticalBlock"] div.stMetric {{ 
        padding: 8px 10px; 
        margin-bottom: 8px; 
    }}
    div[data-testid="stVerticalBlock"] div.stMetric label {{ 
        font-size: 0.85em; 
    }}
     div[data-testid="stVerticalBlock"] div.stMetric div[data-testid="stMetricValue"] {{ 
        font-size: 1.5em; 
    }}
    .pe-card {{
        border: 1px solid #e0e0e0; 
        border-left: 5px solid {COLOR_PRIMARY};
        border-radius: 5px;
        padding: 10px 12px;
        margin-bottom: 10px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05); 
        background-color: {COLOR_WHITE};
    }}
    .pe-card h6 {{ 
        margin-top: 0; 
        margin-bottom: 0.4rem;
        font-size: 1em; 
        font-weight: bold; 
        color: {COLOR_PRIMARY};
    }}
    .pe-card .stProgress {{
        margin-bottom: 0.3rem; 
    }}
    .pe-card p.caption {{
        font-size: 0.8em;
        margin-bottom: 0.5rem; 
    }}
    .pe-card-metric-label {{
        font-size: 0.85em;
        color: #495057;
        margin-bottom: 0.1rem; 
        line-height: 1.2;
    }}
    .pe-card-metric-value {{
        font-size: 1.15em;
        font-weight: bold; 
        color: {COLOR_SECONDARY};
        margin-bottom: 0;
        line-height: 1.2;
    }}
    .pe-card-metric-value-alt {{
        color: {COLOR_PRIMARY}; 
    }}
    h1, h2, h4, h5 {{ color: {COLOR_PRIMARY}; }}
    div[data-testid="stExpander"] summary {{ font-weight: bold; color: {COLOR_PRIMARY}; }}
    div[data-testid="stImage"] img {{
        object-fit: contain !important;
        max-height: 50px; 
    }}
    h3 {{ 
        color: {COLOR_PRIMARY}; 
        font-size: 1.2em !important; 
        margin-bottom: -0.1rem !important; 
    }}
    div[data-testid="stImage"] {{
        display: flex; 
        align-items: center;
        justify-content: center;
        min-height: 25px;
        padding-top: 30px;
        padding-bottom: 0.1px;
    }}
    h2, h3 {{ margin-bottom: 0.1rem; }}
    
    hr {{
        margin: 0.5rem 0 !important; 
        height: 1px;
        background-color: #e0e0e0;
        border: none;
    }}
    .main .block-container hr {{
        margin: 0.3rem 0 !important; 
    }}
    
    /* CSS para controlar a altura e o espaçamento do contêiner do mapa */
    /* Isso tem como alvo o elemento do bloco Streamlit que contém o mapa st_folium */
    /* Pode ser um que tenha diretamente um iframe ou um que tenha uma div com a classe .folium-map */
    div[data-testid="element-container"]:has(> iframe), 
    div[data-testid="element-container"]:has(> div.folium-map) {{
        height: {MAP_SECTION_HEIGHT_PX}px !important; /* Use variable to set fixed height */
        overflow: hidden !important; /* Prevent content from spilling */
        margin-bottom: -1.6rem !important; /* Adjusted to pull footer up, fine-tune if needed */
        padding-bottom: 0 !important;
    }}

    /* Garanta que o próprio iframe/div do mapa preencha o contêiner definido acima */
    div[data-testid="element-container"]:has(> iframe) > iframe,
    div[data-testid="element-container"]:has(> div.folium-map) > div.folium-map {{
        height: 100% !important;
        width: 100% !important;
    }}
    
    /* Regra geral para .folium-map remover sua própria margem se tiver uma */
    .folium-map {{
         margin-bottom: 0rem !important;
    }}

    

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# REMOVIDO: st.markdown("---") que estava aqui para reduzir o espaço antes do rodapé.
st.markdown("---")
st.markdown(f"<p style='text-align:center; color:{COLOR_PRIMARY}; font-size:0.9em; margin-top: 0rem !important; margin-bottom: 0rem !important;'>{st.session_state.get('app_title', 'Painel de Simulado PAE')} | Desenvolvido para visualização otimizada de dados.</p>", unsafe_allow_html=True)