import streamlit as st
import pandas as pd
from Asset import Asset
from Strat import Strategy
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import base64
import numpy as np
import io

# Configuration de la page
st.set_page_config(
    page_title="SOAGA - Backtesting",
    page_icon="📈",
    layout="wide"
)


# Top bar fixe
st.markdown("""
    <style>
        [data-testid="stHeader"] {
            display: none;
        }
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: maroon;
            color: white;
            padding: 8px 16px;
            z-index: 999;
            text-align: center;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .main {
            margin-top: 40px;
        }
    </style>
    <div class="fixed-header">
       <h3> Plateforme de Backtesting SOAGA - BRVM </h3>
    </div>
""", unsafe_allow_html=True)





# Top bar fixée en haut
#st.markdown("""
#    <style>
#        .top-bar {
#            background-color: maroon;
#            padding: 1em;
#            color: white;
#           text-align: center;
#            position: -webkit-sticky;
#            position: sticky;
#            top: 0;
#            z-index: 999;
#            width: 100%;
#        }
#    </style>
#    <div class='top-bar'>
#        <h3>Plateforme de Backtesting des Stratégies d'Investissement sur la BRVM</h3>
#    </div>
#""", unsafe_allow_html=True)

# Styles CSS personnalisés
st.markdown("""
    <style>
    /* Styles généraux */
    .section-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid maroon;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(128, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .section-container:hover {
        box-shadow: 0 4px 8px rgba(128, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    /* Tableaux */
    .dataframe {
        width: 100% !important;
        border-collapse: collapse;
        margin: 15px 0;
    }
    .dataframe th {
        background-color: maroon !important;
        color: white !important;
        padding: 12px !important;
        text-align: left !important;
        font-weight: bold !important;
    }
    .dataframe td:first-child {
        font-weight: bold !important;
    }
    .dataframe td {
        padding: 10px !important;
        border: 1px solid #ddd !important;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    /* Cartes métriques */
    .metric-container {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid maroon;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(128, 0, 0, 0.1);
    }
    
    /* Métriques */
    [data-testid="stMetricDelta"] svg {
        stroke: currentColor !important;
    }
    [data-testid="stMetricDelta"].negative {
        color: #ff4b4b !important;
    }
    [data-testid="stMetricDelta"].positive {
        color: #28a745 !important;
    }
    
    /* Animation des transitions */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stTab {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Section recherche */
    .search-section {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid maroon;
        margin: 20px 0;
        animation: fadeIn 0.5s ease-out;
    }
    </style>
""", unsafe_allow_html=True)
# Fonction pour charger le logo
def load_logo():
    with open("img/logo_soaga.png", "rb") as f:
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
                st.markdown(f"""
                    <div class='section-container'>
                        <h3 style='color: maroon; text-align: center;'>{title}</h3>
                """, unsafe_allow_html=True)
                
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
                #if not day['Transactions'].empty:
                #    st.markdown("#### Transactions")
                #    st.dataframe(
                #        day['Transactions'].style.format({
                #            'Quantity': '{:,.2f}',
                #            'Price': '{:,.2f}',
                #            'Value': '{:,.2f}'
                #        }),
                #        hide_index=True
                #   )
                #st.markdown("</div>", unsafe_allow_html=True)
            
            # Graphique de performance
            st.markdown("""
                <div class='section-container'>
                    <h3 style='color: maroon; text-align: center;'>Performance Comparée</h3>
            """, unsafe_allow_html=True)
                        # Calcul des données pour le graphique
            nav_series = strategy.get_nav_series()
            nav_rebased = 100 * nav_series / nav_series.iloc[0]
            
            benchmark_data = asset.data.loc[strategy.start_date:strategy.end_date, 'BRVM C']
            benchmark_rebased = 100 * benchmark_data / benchmark_data.iloc[0]
            
            # Configuration du graphique
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
                    line=dict(color='black', width=3),
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
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Calcul des indicateurs de performance et de risque
            #nav_weekly = nav_series.resample('W').last()
            #benchmark_weekly = benchmark_data.resample('W').last()
            
            nav_weekly = nav_series.resample('W').last()
            benchmark_weekly = benchmark_data.resample('W').last()
            
        
            
            #Performance journalière
            nav_daily = nav_series.pct_change().dropna()
            benchmark_return1 = ((benchmark_data.iloc[-1] - 100) / 100) * 100
            
            
            portfolio_returns = nav_weekly.pct_change().dropna()
            benchmark_returns = benchmark_weekly.pct_change().dropna()
            
            # Indicateurs de performance
            initial_nav = nav_series.iloc[0]
            final_nav = nav_series.iloc[-1]
            total_return = ((final_nav - initial_nav) / initial_nav) * 100
            
            benchmark_return = ((benchmark_rebased.iloc[-1] - 100) / 100) * 100
            surperf = total_return - benchmark_return
            
            # Indicateurs de risque
            volatility_portfolio = portfolio_returns.std() * np.sqrt(52) * 100
            volatility_benchmark = benchmark_returns.std() * np.sqrt(52) * 100
            correlation = portfolio_returns.corr(benchmark_returns)
            beta = portfolio_returns.cov(benchmark_returns) / benchmark_returns.var()
            
            # Ratio de Sharpe (taux sans risque de 6%)
            risk_free_rate = 0.06
            excess_return = portfolio_returns.mean() * 52 - risk_free_rate
            sharpe_ratio = excess_return / (portfolio_returns.std() * np.sqrt(52))
            
                        # Affichage des métriques de performance
            st.markdown("""
                <div class='section-container'>
                    <h3 style='color: maroon; text-align: center;'>Résumé des Performances</h3>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Performance Portefeuille",
                    f"{total_return:.2f}%",
                    delta=f"{total_return:.2f}%",
                    delta_color="normal" if total_return > 0 else "inverse"
                )
            with col2:
                st.metric(
                    "Performance BRVM-C",
                    f"{benchmark_return:.2f}%",
                    delta=f"{benchmark_return:.2f}%",
                    delta_color="normal" if benchmark_return > 0 else "inverse"
                )
            with col3:
                st.metric(
                    "Surperformance",
                    f"{surperf:.2f}%",
                    delta=f"{surperf:.2f}%",
                    delta_color="normal" if surperf > 0 else "inverse"
                )
            st.markdown("</div>", unsafe_allow_html=True)

            # Affichage des indicateurs de risque
            st.markdown("""
                <div class='section-container'>
                    <h3 style='color: maroon; text-align: center;'>Indicateurs de Risque</h3>
                    <div style='display: flex; justify-content: space-around; flex-wrap: wrap;'>
            """, unsafe_allow_html=True)

            # Volatilité
            risk_col1, risk_col2 = st.columns(2)
            with risk_col1:
                st.markdown("""
                    <div class='metric-container'>
                        <h4 style='color: maroon; margin-bottom: 15px;'>Volatilité (annualisée)</h4>
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
                    <div class='metric-container'>
                        <h4 style='color: maroon; margin-bottom: 15px;'>Mesures de Risque</h4>
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

            # Ratio de Sharpe
            st.markdown("""
                <div class='metric-container' style='margin-top: 20px;'>
                    <h4 style='color: maroon; margin-bottom: 15px; text-align: center;'>Ratio de Sharpe</h4>
                    <p style='text-align: center; font-size: 24px; font-weight: bold; color: {};'>{:.2f}</p>
                    <p style='text-align: center; font-size: 12px; color: gray;'>Taux sans risque : 6.00%</p>
                </div>
            """.format('green' if sharpe_ratio > 0 else 'red', sharpe_ratio), unsafe_allow_html=True)

            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Après st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Export des données
            st.markdown("""
                <div class='section-container'>
                    <h3 style='color: maroon; text-align: center;'>Export des Données</h3>
                </div>
            """, unsafe_allow_html=True)

            # Préparation des données pour l'export
            def prepare_export_data(history):
                # Création d'un writer Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Feuille pour les états de portefeuille
                    all_states = []
                    for _, row in history.iterrows():
                        state_df = pd.DataFrame.from_dict(row['State'])
                        state_df['Date'] = row['Date']
                        state_df['NAV'] = row['NAV']
                        state_df['Total_Value'] = row['Total_Value']
                        all_states.append(state_df)
                    
                    states_df = pd.concat(all_states, axis=0)
                    states_df = states_df.reset_index()
                    states_df = states_df.rename(columns={'index': 'Ticker'})
                    states_df.to_excel(writer, sheet_name='États du Portefeuille', index=False)
                    
                    # Feuille pour les transactions
                    all_transactions = []
                    for _, row in history.iterrows():
                        if isinstance(row['Transactions'], pd.DataFrame) and not row['Transactions'].empty:
                            trans_df = row['Transactions'].copy()
                            trans_df['Date'] = row['Date']
                            all_transactions.append(trans_df)
                    
                    if all_transactions:
                        transactions_df = pd.concat(all_transactions, axis=0)
                        transactions_df = transactions_df.reset_index(drop=True)
                        transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    # Mise en forme
                    workbook = writer.book
                    number_format = workbook.add_format({'num_format': '#,##0.00'})
                    percent_format = workbook.add_format({'num_format': '0.00%'})
                    
                    # Formatage des colonnes pour les états
                    states_worksheet = writer.sheets['États du Portefeuille']
                    states_worksheet.set_column('C:E', 12, number_format)  # Quantity, Price, Value
                    states_worksheet.set_column('F:F', 10, percent_format)  # Weight
                    
                    # Formatage des colonnes pour les transactions si elles existent
                    if all_transactions:
                        trans_worksheet = writer.sheets['Transactions']
                        trans_worksheet.set_column('B:D', 12, number_format)  # Quantity, Price, Value

                return output.getvalue()

            # Bouton de téléchargement
            export_data = prepare_export_data(history)
            st.download_button(
                label="📥 Télécharger les données",
                data=export_data,
                file_name=f"backtest_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel",
            )
        # Dans l'onglet recherche (remplacer le code existant de tab2)
        # Remplacer la section du tab2 par :
        with tab2:
            if 'history' not in st.session_state:
                st.session_state.history = history

            st.markdown("""
                 <div class='section-container'>
                     <h3 style='color: maroon; text-align: center;'>Recherche par Date</h3>
                </div>
            """, unsafe_allow_html=True)

            # Recherche par date
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_date = st.date_input(
                    "Sélectionnez une date",
                    min_value=pd.Timestamp(start_date).date(),
                    max_value=pd.Timestamp(end_date).date()
                )
            
            with search_col2:
                search_button = st.button(
                   "Rechercher", 
                    type="primary",
                    key="search_button"  # Ajout d'une clé unique
           )


            if search_button:
                
                st.session_state.search_active = True
                st.session_state.search_date = search_date
                
                search_date = pd.Timestamp(search_date)
                closest_date = min(pd.to_datetime(history['Date']), key=lambda x: abs(x - search_date))
                day_data = history[history['Date'] == closest_date]

                if not day_data.empty:
                    day = day_data.iloc[0]
                    
                    # Affichage des résultats dans un conteneur stylisé
                    st.markdown("""
                        <div class='search-section'>
                            <h4 style='color: maroon; margin-bottom: 20px;'>Résultats de la recherche</h4>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Informations principales
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Date", day['Date'].strftime('%d/%m/%Y'))
                    with col2:
                        st.metric("Valeur Liquidative", f"{day['NAV']:,.2f}")
                    with col3:
                        st.metric("Valorisation", f"{day['Total_Value']:,.2f} XOF")

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

                    # Transactions du jour
                    if isinstance(day['Transactions'], pd.DataFrame) and not day['Transactions'].empty:
                        st.markdown("#### Transactions du Jour")
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