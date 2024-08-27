import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# URL del servicio web
url = os.getenv("SERVICE_URL")

# Filtros en la sidebar
st.sidebar.header("Filtros")

tipo_vta = st.sidebar.selectbox(
    "Elija el tipo de Venta:",
    ["001 Publico", "002 Distribuidores", "003 Usados", "004 Flotilla", "999 TODOS"]
)

# Solicitar los datos del servidor
response = requests.post(url, json={"TipoVta": tipo_vta[:3]})

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)

    # Filtro por rango de años
    years = df['Año'].unique()
    selected_years = st.sidebar.multiselect("Seleccionar años:", options=years, default=years)
    df_filtered = df[df['Año'].isin(selected_years)]
    
    if df_filtered.empty:
        st.write("No hay datos para los años seleccionados.")
    else:
        st.write("### Datos de ventas")
        st.write(df_filtered)

        # Excluir la columna 'Total' para las gráficas de ventas mensuales
        df_no_total = df_filtered.drop(columns=['Total'])

        # Total de ventas por año
        st.write("### Total de ventas por año")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_filtered['Año'],
            y=df_filtered['Total'],
            text=df_filtered['Total'],
            textposition='outside',  # Posicionar etiquetas fuera de las barras
            marker_color='indianred'  # Color de las barras
        ))
        
        # Añadir línea de promedio (opcional)
        average_sales = df_filtered['Total'].mean()
        fig_bar.add_trace(go.Scatter(
            x=df_filtered['Año'],
            y=[average_sales] * len(df_filtered['Año']),
            mode='lines',
            line=dict(color='blue', dash='dash'),
            name='Promedio Anual'
        ))

        # Actualizar el diseño del gráfico
        fig_bar.update_layout(
            title="Total de Ventas por Año",
            xaxis_title="Año",
            yaxis_title="Total",
            xaxis=dict(
                tickmode='linear',  # Asegurar que cada año sea visible en el eje X
                tickvals=df_filtered['Año'],
                ticktext=[str(year) for year in df_filtered['Año']]
            ),
            yaxis=dict(
                title="Total de Ventas",
                title_font_size=16,
                ##tickprefix='$',  # Formato monetario (opcional)
                showgrid=True
            ),
            ##plot_bgcolor='rgba(240, 240, 240, 0.1)',  # Fondo del gráfico
            ##paper_bgcolor='white',  # Fondo del lienzo
            margin=dict(l=40, r=40, t=40, b=40)  # Márgenes del gráfico
        )

        st.plotly_chart(fig_bar)

        # Gráfico de ventas por mes
        st.write("### Gráfico de ventas por mes")
        df_melt = df_no_total.melt(id_vars=["Año"], var_name="Mes", value_name="Ventas")
        fig_line = px.line(df_melt, x='Mes', y='Ventas', color='Año', 
                           title="Ventas por Mes", 
                           labels={'Ventas': 'Ventas', 'Mes': 'Mes'},
                           template='plotly_dark')
        st.plotly_chart(fig_line)

        # Selector de año para distribución de ventas por mes
        st.write("### Distribución de ventas por mes")
        last_year = st.selectbox("Seleccionar año para distribución de ventas por mes:", options=selected_years, index=len(selected_years)-1)
        
        if last_year:
            ultimo_ano = df_filtered[df_filtered['Año'] == last_year]
            ultimo_ano = ultimo_ano.melt(id_vars=["Año"], var_name="Mes", value_name="Ventas")
            ultimo_ano = ultimo_ano[ultimo_ano['Mes'] != 'Total']  # Excluye la fila 'Total'
            fig_pie = px.pie(ultimo_ano, names='Mes', values='Ventas', 
                            title=f"Distribución de Ventas por Mes ({last_year})", 
                            template='plotly_dark')
            st.plotly_chart(fig_pie)

        # Gráfico de áreas apiladas (Stacked Area Chart)
        st.write("### Evolución de ventas acumuladas por mes")
        df_cumulative = df_no_total.copy()
        df_cumulative = df_cumulative.cumsum(axis=1)  # Cálculo acumulado
        df_melt_cumulative = df_cumulative.melt(id_vars=["Año"], var_name="Mes", value_name="Ventas")
        fig_area = px.area(df_melt_cumulative, x='Mes', y='Ventas', color='Año', 
                           title="Ventas Acumuladas por Mes", 
                           labels={'Ventas': 'Ventas', 'Mes': 'Mes'},
                           template='plotly_dark')
        st.plotly_chart(fig_area)

        # Gráfico de dispersión (Scatter Plot)
        st.write("### Ventas por mes vs. Total anual")
        df_melt_scatter = df_filtered.melt(id_vars=["Año", "Total"], var_name="Mes", value_name="Ventas")
        df_melt_scatter = df_melt_scatter[df_melt_scatter['Mes'] != 'Total']  # Excluye la fila 'Total'

        # Crear el gráfico de dispersión con Plotly
        fig_scatter = px.scatter(df_melt_scatter, x='Ventas', y='Total', color='Año',
                                title="Ventas por Mes vs. Total Anual",
                                labels={'Ventas': 'Ventas Mensuales', 'Total': 'Total Anual'})

        # Personalizar el gráfico
        fig_scatter.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=2, color='DarkSlateGrey')), 
                                selector=dict(mode='markers+text'))

        fig_scatter.update_layout(
            xaxis_title="Ventas Mensuales",
            yaxis_title="Total Anual",
            title_font_size=20,
            xaxis=dict(
                title_font_size=16,
                tickfont_size=14,
            ),
            yaxis=dict(
                title_font_size=16,
                tickfont_size=14,
            ),
            ##plot_bgcolor='rgba(240, 240, 240, 0.1)',  # Fondo del gráfico
            ##paper_bgcolor='white',  # Fondo del lienzo
            margin=dict(l=40, r=40, t=40, b=40)  # Márgenes del gráfico
        )

        st.plotly_chart(fig_scatter)


        # Gráfico de calor (Heatmap)
        st.write("### Matriz de calor de ventas por mes y año")
        df_heatmap = df_no_total.set_index('Año').T  # Transponer para heatmap
        fig_heatmap = px.imshow(df_heatmap, labels=dict(x="Año", y="Mes", color="Ventas"), 
                                title="Ventas por Mes y Año",
                                ##template='plotly_dark')
        )
        st.plotly_chart(fig_heatmap)

        

else:
    st.error("Error al obtener los datos del servidor")
