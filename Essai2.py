import streamlit as st
import pandas as pd
from Asset import Asset
from Strat import Strategy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import base64
import numpy as np

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
    .dataframe {
        width: 100% !important;
    }
    .dataframe th {
        background-color: maroon !important;
        color: white !important;
        padding: 8px !important;
        text-align: left !important;
        font-weight: bold !important;
    }
    .dataframe td:first-child {
        font-weight: bold !important;
    }
    .dataframe td {
        padding: 8px !important;
        border: 1px solid #ddd !important;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .search-section {
        margin-top: 2rem;
        padding: 1.5rem;
        border: 2px solid maroon;
        border-radius: 5px;
    }
    /* Styles pour les métriques */
    [data-testid="stMetricDelta"] svg {
        stroke: currentColor !important;
    }
    
    [data-testid="stMetricDelta"].negative {
        color: #ff4b4b !important;
    }
    
    [data-testid="stMetricDelta"].positive {
        color: #28a745 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
            ["Stratégie de Base"]
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
        
        # Création des onglets
        tab1, tab2 = st.tabs(["Résultats du Backtest", "Recherche par Date"])
        
        with tab1:
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
                    }),
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
                        }),
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
                    line=dict(color='maroon', width=3),
                    hovertemplate='Date: %{x}<br>Performance: %{y:.2f}%<extra></extra>'
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=benchmark_rebased.index,
                    y=benchmark_rebased.values,
                    name='BRVM-C',
                    line=dict(color='black', width=3, dash='dash'),
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
            
            
            # Modification de l'affichage des métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                "Performance Portefeuille",
                f"{total_return:.2f}%",
                delta=f"{total_return:.2f}%",
                delta_color="normal" if total_return > 0 else "inverse"
           )
                if total_return < 0:
                    st.markdown('<style>[data-testid="stMetricDelta"]:last-child { color: #ff4b4b !important; }</style>', unsafe_allow_html=True)

            with col2:
                st.metric(
                "Performance BRVM-C",
                f"{benchmark_return:.2f}%",
                delta=f"{benchmark_return:.2f}%",
                delta_color="normal" if benchmark_return > 0 else "inverse"
           )
                if benchmark_return < 0:
                   st.markdown('<style>[data-testid="stMetricDelta"]:nth-last-child(2) { color: #ff4b4b !important; }</style>', unsafe_allow_html=True)

            with col3:
                st.metric(
                "Performance",
                f"{surperf:.2f}%",
                delta=f"{surperf:.2f}%",
                delta_color="normal" if surperf > 0 else "inverse"
        )
                if surperf < 0:
                    st.markdown('<style>[data-testid="stMetricDelta"]:nth-last-child(3) { color: #ff4b4b !important; }</style>', unsafe_allow_html=True)
            
            
        
            # Après le résumé des performances, ajoutez :

            # Indicateurs de risque
            st.markdown("""
                <div style='background-color: #f8f9f9; padding: 20px; border-radius: 5px; margin-top: 30px;'>
                    <h3 style='color: maroon; text-align: center; margin-bottom: 20px;'>Indicateurs de Risque</h3>
                </div>
            """, unsafe_allow_html=True)
            
            nav_weekly = nav_series.resample('W').last()
            benchmark_weekly = benchmark_data.resample('W').last()
            
            portfolio_returns = nav_weekly.pct_change().dropna()
            benchmark_returns = benchmark_weekly.pct_change().dropna()
            
            # Calcul des indicateurs (ajustement pour données hebdomadaires)
            volatility_portfolio = portfolio_returns.std() * np.sqrt(52) * 100  # Annualisée en %
            volatility_benchmark = benchmark_returns.std() * np.sqrt(52) * 100  # Annualisée en %
            correlation = portfolio_returns.corr(benchmark_returns)
            beta = portfolio_returns.cov(benchmark_returns) / benchmark_returns.var()
            
            # Taux sans risque (hypothèse : 6% annuel)
            risk_free_rate = 0.06
            risk_free_weekly = (1 + risk_free_rate) ** (1/52) - 1  # Conversion en taux hebdomadaire
            excess_return = portfolio_returns.mean() * 52 - risk_free_rate
            sharpe_ratio = excess_return / (portfolio_returns.std() * np.sqrt(52))
            
            # Affichage des indicateurs en deux colonnes
            risk_col1, risk_col2 = st.columns(2)
            
            with risk_col1:
                st.markdown("""
                    <div style='background-color: white; padding: 15px; border: 1px solid maroon; border-radius: 5px;'>
                        <h4 style='color: maroon; margin-bottom: 15px;'>Volatilité</h4>
                        <table style='width: 100%;'>
                            <tr>
                                <td style='padding: 8px; font-weight: bold;'>Portefeuille</td>
                                <td style='padding: 8px; text-align: right;'>{:.2f}%</td>
                            </tr>
                            <tr style='background-color: #f9f9f9;'>
                                <td style='padding: 8px; font-weight: bold;'>BRVM-C</td>
                                <td style='padding: 8px; text-align: right;'>{:.2f}%</td>
                            </tr>
                        </table>
                    </div>
                """.format(volatility_portfolio, volatility_benchmark), unsafe_allow_html=True)
            
            with risk_col2:
                st.markdown("""
                    <div style='background-color: white; padding: 15px; border: 1px solid maroon; border-radius: 5px;'>
                        <h4 style='color: maroon; margin-bottom: 15px;'>Corrélation & Beta</h4>
                        <table style='width: 100%;'>
                            <tr>
                                <td style='padding: 8px; font-weight: bold;'>Corrélation</td>
                                <td style='padding: 8px; text-align: right;'>{:.2f}</td>
                            </tr>
                            <tr style='background-color: #f9f9f9;'>
                                <td style='padding: 8px; font-weight: bold;'>Beta</td>
                                <td style='padding: 8px; text-align: right;'>{:.2f}</td>
                            </tr>
                        </table>
                    </div>
                """.format(correlation, beta), unsafe_allow_html=True)
            
            # Affichage du ratio de Sharpe dans une boîte spéciale
            st.markdown("""
                <div style='background-color: white; padding: 15px; border: 1px solid maroon; border-radius: 5px; margin-top: 20px;'>
                    <h4 style='color: maroon; margin-bottom: 15px; text-align: center;'>Ratio de Sharpe</h4>
                    <p style='text-align: center; font-size: 24px; font-weight: bold; color: {};'>{:.2f}</p>
                    <p style='text-align: center; font-size: 12px; color: gray;'>Taux sans risque : 6%</p>
                </div>
            """.format('green' if sharpe_ratio > 0 else 'red', sharpe_ratio), unsafe_allow_html=True)
            
            
            
        with tab2:
            st.markdown("### Recherche par Date")
            with st.form("search_form"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_date = st.date_input(
                        "Sélectionnez une date",
                        min_value=pd.Timestamp(start_date).date(),
                        max_value=pd.Timestamp(end_date).date()
                    )
                search_button = st.form_submit_button("Rechercher", type="primary")
            
            if search_button:
                search_date = pd.Timestamp(search_date)
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
                        }),
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
                            }),
                            hide_index=True
                        )
                else:
                    st.warning(f"Aucune donnée disponible pour le {search_date.strftime('%d/%m/%Y')}")
                    
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")