import streamlit as st
import pandas as pd
from Asset import Asset
from Strat import Strategy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import base64

# Configuration de la page
st.set_page_config(
    page_title="SOAGA Asset Management - Backtesting",
    page_icon="📈",
    layout="wide"
)

# Top bar
st.markdown("""
    <div style='background-color: maroon; padding: 1em; color: white; text-align: center; margin-bottom: 2em;'>
        <h1>SOAGA Asset Management</h1>
        <p>Plateforme de Backtesting des Stratégies d'Investissement sur la BRVM</p>
    </div>
""", unsafe_allow_html=True)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .main {
        background-color: white;
    }
    .stApp header {
        background-color: maroon;
        color: white;
    }
    .stApp footer {
        background-color: maroon;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: white;
    }
    .st-emotion-cache-1v0mbdj.e115fcil1 {
        border: 1px solid maroon;
        border-radius: 5px;
        padding: 10px;
    }
    .st-table {
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    .st-table thead tr {
        background-color: maroon;
        color: white;
        text-align: left;
    }
    .st-table th,
    .st-table td {
        padding: 12px 15px;
    }
    .st-table tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    .st-table tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    </style>
    """, unsafe_allow_html=True)

# Fonction pour charger le logo
def load_logo():
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"

# Sidebar
with st.sidebar:
    # Logo
    try:
        st.image(load_logo(), width=200)
    except:
        st.title("SOAGA AM")
    
    st.markdown("---")
    
    # Formulaire
    with st.form("backtest_form"):
        uploaded_file = st.file_uploader("Données historiques", type=['xlsx'])
        
        strategy_type = st.selectbox(
            "Stratégie",
            ["Stratégie de Base"]  # Ajouter d'autres stratégies ici
        )
        
        initial_nav = st.number_input(
            "Valeur Liquidative Initiale",
            min_value=1.0,
            value=100.0
        )
        
        initial_cash = st.number_input(
            "Cash Initial",
            min_value=1000000.0,
            value=90000000.0
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Date de début")
        with col2:
            end_date = st.date_input("Date de fin")
        
        submit_button = st.form_submit_button("Backtester")

# Zone principale
if not submit_button:
    # Affichage par défaut
    st.markdown("""
    ### Guide d'utilisation
    1. Chargez vos données historiques (format Excel)
    2. Sélectionnez la stratégie à tester
    3. Définissez les paramètres initiaux
    4. Lancez le backtest
    
    ### À propos de la stratégie de base
    La stratégie de base consiste à :
    - Maintenir ORAC et SNTS à 20% chacun
    - Sélectionner les 18 meilleures performances sur 6 mois
    - Rééquilibrer le portefeuille selon les conditions définies
    
    ### Fonctionnement du Backtesting
    Le backtest permet de :
    - Simuler la gestion du portefeuille sur une période historique
    - Comparer la performance avec le benchmark (BRVM-C)
    - Analyser les transactions et l'évolution du portefeuille
    - Mesurer la surperformance de la stratégie
    """)
else:
    try:
        # Chargement des données et exécution du backtest
        asset = Asset(uploaded_file)
        
        strategy = Strategy(
            initial_cash=initial_cash,
            initial_nav=initial_nav,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            asset=asset
        )
        
        history = strategy.display_portfolio_history()
        
        # Affichage des résultats
        st.title("Résultats du Backtest")
        
        # Premier et dernier jour
        for day, title in [(history.iloc[0], "Premier Jour"), (history.iloc[-1], "Dernier Jour")]:
            st.markdown(f"### {title}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Date:** {day['Date'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**VL:** {day['NAV']:,.2f}")
            with col3:
                st.write(f"**Valorisation:** {day['Total_Value']:,.2f} XOF")
            
            # État du portefeuille
            st.markdown("#### État du Portefeuille")
            state_df = pd.DataFrame.from_dict(day['State'])
            st.dataframe(
                state_df.style.format({
                    'Quantity': '{:,.2f}',
                    'Price': '{:,.2f}',
                    'Value': '{:,.2f}',
                    'Weight': '{:.2%}'
                }).background_gradient(cmap='RdYlGn', subset=['Weight']),
                hide_index=False
            )
            
            # Transactions
            if not day['Transactions'].empty:
                st.markdown("#### Transactions")
                st.dataframe(
                    day['Transactions'].style.format({
                        'Quantity': '{:,.2f}',
                        'Price': '{:,.2f}',
                        'Value': '{:,.2f}'
                    }).background_gradient(cmap='RdYlGn', subset=['Value']),
                    hide_index=True
                )
        
        # Graphique de performance
        st.markdown("### Performance Comparée")
        
        nav_series = strategy.get_nav_series()
        nav_rebased = 100 * nav_series / nav_series.iloc[0]
        
        benchmark_data = asset.data.loc[strategy.start_date:strategy.end_date, 'BRVM C']
        benchmark_rebased = 100 * benchmark_data / benchmark_data.iloc[0]
        
        fig = make_subplots(rows=1, cols=1)
        
        fig.add_trace(
            go.Scatter(
                x=nav_rebased.index,
                y=nav_rebased.values,
                name='Portefeuille',
                line=dict(color='maroon', width=2),
                hovertemplate='Date: %{x}<br>Performance: %{y:.2f}%<extra></extra>'
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=benchmark_rebased.index,
                y=benchmark_rebased.values,
                name='BRVM-C',
                line=dict(color='black', width=2, dash='dash'),
                hovertemplate='Date: %{x}<br>Performance: %{y:.2f}%<extra></extra>'
            )
        )
        
        fig.update_layout(
            title={
                'text': 'Performance Comparée (Base 100)',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title='Date',
            yaxis_title='Performance (%)',
            hovermode='x unified',
            template='plotly_white',
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255, 255, 255, 0.8)'
            )
        )
        
        # Ajout d'une ligne de base à 100
        fig.add_hline(
            y=100,
            line_dash="dot",
            line_color="gray",
            annotation_text="Base 100",
            annotation_position="bottom right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Résumé des performances
        st.markdown("### Résumé des Performances")
        
        # Calcul des performances
        initial_nav = nav_series.iloc[0]
        final_nav = nav_series.iloc[-1]
        total_return = ((final_nav - initial_nav) / initial_nav) * 100
        
        benchmark_return = ((benchmark_rebased.iloc[-1] - 100) / 100) * 100
        surperf = total_return - benchmark_return
        
        # Affichage des métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Performance Portefeuille",
                f"{total_return:.2f}%",
                delta=f"{total_return:.2f}%"
            )
        with col2:
            st.metric(
                "Performance BRVM-C",
                f"{benchmark_return:.2f}%",
                delta=f"{benchmark_return:.2f}%"
            )
        with col3:
            st.metric(
                "Surperformance",
                f"{surperf:.2f}%",
                delta=f"{surperf:.2f}%",
                delta_color="normal" if surperf > 0 else "inverse"
            )
        
        # Recherche par date avec validation
        st.markdown("### Recherche par Date")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_date = st.date_input(
                "Sélectionnez une date",
                min_value=pd.Timestamp(start_date).date(),
                max_value=pd.Timestamp(end_date).date()
            )
        with col2:
            search_button = st.button("Rechercher", type="primary")
        
        if search_button and search_date:
            search_date = pd.Timestamp(search_date)
            # Trouver la date la plus proche dans l'historique
            closest_date = min(history['Date'], key=lambda x: abs(x - search_date))
            day_data = history[history['Date'] == closest_date]
            
            if not day_data.empty:
                day = day_data.iloc[0]
                st.success(f"Données trouvées pour le {closest_date.strftime('%d/%m/%Y')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Date:** {day['Date'].strftime('%d/%m/%Y')}")
                with col2:
                    st.write(f"**VL:** {day['NAV']:,.2f}")
                with col3:
                    st.write(f"**Valorisation:** {day['Total_Value']:,.2f} XOF")
                
                # État du portefeuille
                st.markdown("#### État du Portefeuille")
                state_df = pd.DataFrame.from_dict(day['State'])
                st.dataframe(
                    state_df.style.format({
                        'Quantity': '{:,.2f}',
                        'Price': '{:,.2f}',
                        'Value': '{:,.2f}',
                        'Weight': '{:.2%}'
                    }).background_gradient(cmap='RdYlGn', subset=['Weight']),
                    hide_index=False
                )
                
                # Transactions
                if not day['Transactions'].empty:
                    st.markdown("#### Transactions")
                    st.dataframe(
                        day['Transactions'].style.format({
                            'Quantity': '{:,.2f}',
                            'Price': '{:,.2f}',
                            'Value': '{:,.2f}'
                        }).background_gradient(cmap='RdYlGn', subset=['Value']),
                        hide_index=True
                    )
            else:
                st.warning(f"Aucune donnée disponible pour le {search_date.strftime('%d/%m/%Y')}")
                
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")