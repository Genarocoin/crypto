import streamlit as st
import pandas as pd
import numpy as np
import ccxt
import mplfinance as mpf
import matplotlib.pyplot as plt
from PIL import Image

def obtener_datos_binance(par, intervalo='1h'):
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    velas = exchange.fetch_ohlcv(par, timeframe=intervalo, limit=100)
    columnas = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pd.DataFrame(velas, columns=columnas)
    df['Date'] = pd.to_datetime(df['Date'], unit='ms')
    df.set_index('Date', inplace=True)
    return df

def obtener_libro_ordenes(par):
    exchange = ccxt.binance({'options': {'defaultType': 'future'}})
    try:
        order_book = exchange.fetch_order_book(par)
        bids = pd.DataFrame(order_book['bids'], columns=['Precio', 'Volumen'])
        asks = pd.DataFrame(order_book['asks'], columns=['Precio', 'Volumen'])
        asks['Volumen'] *= -1
        return bids, asks
    except Exception as e:
        st.error(f"Error al obtener el libro de órdenes: {e}")
        return pd.DataFrame(columns=['Precio', 'Volumen']), pd.DataFrame(columns=['Precio', 'Volumen'])

def obtener_open_interest(par):
    fechas = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='H')
    open_interest = np.random.randint(1000, 5000, size=len(fechas))
    df = pd.DataFrame({'Date': fechas, 'Open Interest': open_interest})
    df.set_index('Date', inplace=True)
    return df

def agregar_logo(fig, logo_path):
    logo = Image.open(logo_path)
    fig.figimage(logo, xo=850, yo=600, alpha=0.8, zorder=1)
    return fig

def analizar_direccion(df_velas, df_open_interest):
    if df_velas.empty or df_open_interest.empty:
        return "neutral", "Datos insuficientes para determinar la dirección del mercado."

    cambio_precio = df_velas['Close'].iloc[-1] - df_velas['Close'].iloc[-2]
    cambio_open_interest = df_open_interest['Open Interest'].iloc[-1] - df_open_interest['Open Interest'].iloc[-2]

    if cambio_precio > 0 and cambio_open_interest > 0:
        return "alcista", "Posible tendencia alcista (Long Build-up)", "Un incremento tanto en el precio como en el Open Interest sugiere acumulación de posiciones largas."
    elif cambio_precio > 0 and cambio_open_interest < 0:
        return "alcista", "Posible tendencia alcista (Short Covering)", "El precio sube mientras el Open Interest disminuye, lo que indica cierre de posiciones cortas."
    elif cambio_precio < 0 and cambio_open_interest > 0:
        return "bajista", "Posible tendencia bajista (Short Build-up)", "Una caída en el precio junto con un aumento del Open Interest indica acumulación de posiciones cortas."
    elif cambio_precio < 0 and cambio_open_interest < 0:
        return "bajista", "Posible tendencia bajista (Long Unwinding)", "El precio baja mientras el Open Interest disminuye, indicando cierre de posiciones largas."
    else:
        return "neutral", "Tendencia neutral, no se pudo determinar un patrón claro.", "No hay un patrón definido en el comportamiento del precio y el Open Interest."

st.title("📈Escaner de Acción Crypto | GENAROCOIN📉")
par = st.text_input("Par de trading (Ej: BTC/USDT)", "BTC/USDT")
intervalo = st.selectbox("Intervalo del gráfico", ["1m", "5m", "15m", "1h", "4h", "1d", "1w"])

logo_path = "/PERSONA_BASE_1.png"

if st.button("Obtener Datos y Generar Gráficos"):
    df_velas = obtener_datos_binance(par, intervalo)
    df_open_interest = obtener_open_interest(par)

    if not df_velas.empty:
        st.subheader("Gráfico de Velas con Líneas del Libro de Órdenes")
        fig, ax = plt.subplots(figsize=(12, 8))
        mpf.plot(df_velas, type='candle', style='binance', ax=ax)

        bids, asks = obtener_libro_ordenes(par)
        if not bids.empty and not asks.empty:
            for _, row in bids.nlargest(3, 'Volumen').iterrows():
                ax.axhline(y=row['Precio'], color='green', linestyle='--', linewidth=1, label=f"Compra: {row['Precio']:.4f}")
            for _, row in asks.nsmallest(3, 'Volumen').iterrows():
                ax.axhline(y=row['Precio'], color='red', linestyle='--', linewidth=1, label=f"Venta: {row['Precio']:.4f}")

        fig = agregar_logo(fig, logo_path)
        st.pyplot(fig)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Puntos de Compras")
            top_bids = bids.nlargest(3, 'Volumen').to_dict('records')
            for i, fila in enumerate(top_bids, 1):
                st.markdown(f"- **Posición {i}:** Precio: {fila['Precio']:.4f}, Volumen: {fila['Volumen']:.2f}")
        with col2:
            st.subheader("Puntos de Ventas")
            top_asks = asks.nsmallest(3, 'Volumen').to_dict('records')
            for i, fila in enumerate(top_asks, 1):
                st.markdown(f"- **Posición {i}:** Precio: {fila['Precio']:.4f}, Volumen: {abs(fila['Volumen']):.2f}")

        st.subheader("Gráfico del Open Interest")
        if not df_open_interest.empty:
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(df_open_interest.index, df_open_interest['Open Interest'], label='Open Interest', color='blue')
            ax.set_title(f"Open Interest para {par}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Open Interest")
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)

        tendencia, mensaje, interpretacion = analizar_direccion(df_velas, df_open_interest)
        color = "green" if tendencia == "alcista" else "red" if tendencia == "bajista" else "gray"
        st.markdown(f"<h3 style='color: {color};'>{mensaje}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: black;'>{interpretacion}</p>", unsafe_allow_html=True)
    else:
        st.error("No se encontraron datos de velas para el par seleccionado.")
