import streamlit as st
import pandas as pd
import numpy as np
from Asset2 import Asset2
from Strategy2 import Strategy2
from Strategy3 import Strategy3
from Strategy4 import Strategy4
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import base64
import io
import plotly.express as px
import xlsxwriter





SECTORS = {
    'SERVICES PUBLICS': ['SNTS', 'ORAC', 'SDCC', 'ONTBF', 'CIEC'],
    'FINANCES': ['BOAB', 'BOABF', 'BOAC', 'BOAM', 'BOAN', 'BOAS', 'CBIBF', 'ECOC', 'ETIT', 
                'NSBC', 'ORGT', 'SAFC', 'SGBC', 'SIBC', 'BICB'],
    'INDUSTRIE': ['SIVC', 'SEMC', 'FTSC', 'NEIC', 'NTLC', 'CABC', 'STBC', 'SMBC', 'SLBC', 
                 'UNLC', 'UNXC'],
    'DISTRIBUTIONS': ['BNBC', 'CFAC', 'ABJC', 'TTLC', 'TTLS', 'PRSC', 'SHEC'],
    'AGRICULTURE': ['PALC', 'SPHC', 'SICC', 'SOGC', 'SCRC'],
    'AUTRES SECTEURS': ['STAC', 'LNBB'],
    'TRANSPORT': ['SDSC', 'SVOC']
}

SECTOR_METRICS = {
    'SERVICES PUBLICS': {'market_weight': 0.464, 'target': 0.50, 'deviation': 0.20},
    'FINANCES': {'market_weight': 0.363, 'target': 0.30, 'deviation': 0.15},
    'INDUSTRIE': {'market_weight': 0.078, 'target': 0.10, 'deviation': 0.05},
    'DISTRIBUTIONS': {'market_weight': 0.045, 'target': 0.025, 'deviation': 0.05},
    'AGRICULTURE': {'market_weight': 0.035, 'target': 0.025, 'deviation': 0.05},
    'AUTRES SECTEURS': {'market_weight': 0.009, 'target': 0.025, 'deviation': 0.05},
    'TRANSPORT': {'market_weight': 0.007, 'target': 0.025, 'deviation': 0.05}
}






# Configuration de la page
st.set_page_config(
    page_title="SOAGA - Backtesting",
    page_icon="📈",
    layout="wide"
)

# Style header fixe
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
       <h3>Plateforme de Backtesting SOAGA - BRVM</h3>
    </div>
""", unsafe_allow_html=True)

# Styles CSS personnalisés
st.markdown("""
    <style>
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
    .dataframe td {
        padding: 10px !important;
        border: 1px solid #ddd !important;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
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
    </style>
""", unsafe_allow_html=True)

# Fonction pour charger le logo
def load_logo():
    with open("img/logo_soaga.png", "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{data}"


def calculate_sector_weights(portfolio_state):
    """Calcule les poids sectoriels du portefeuille"""
    sector_weights = {}
    
    for sector, stocks in SECTORS.items():
        sector_weight = sum(
            portfolio_state.loc[stock, 'Weight'] 
            for stock in stocks 
            if stock in portfolio_state.index
        )
        sector_weights[sector] = sector_weight
        
    return sector_weights


# Sidebar
with st.sidebar:
    try:
        st.image(load_logo(), width=200)
    except:
        st.title("SOAGA AM")
    
    st.markdown("---")
    
    # Formulaire
    with st.form("backtest_form"):
        # Choix de la stratégie
        strategy_type = st.selectbox(
            "Stratégie",
            options=["High return & Low Vol.", "Stratégie interne T1 2025"],
            help="""
            Stratégie V2: Allocation fixe avec 16 meilleurs dividendes
            Stratégie V3: Allocation multi-groupes avec limites variables
            """
        )
        
     
        uploaded_prices = st.file_uploader("Cours historiques", type=['xlsx'])
        uploaded_dividends = st.file_uploader("Données dividendes", type=['xlsx'])
        
        initial_nav = st.number_input(
            "VL Initiale",
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
            start_date = st.date_input(
                "Date de début",
                min_value=datetime(2024, 1, 1),
                max_value=datetime(2024, 12, 31),
                value=datetime(2024, 1, 1)
            )
        with col2:
            end_date = st.date_input(
                "Date de fin",
                min_value=datetime(2024, 1, 1),
                max_value=datetime(2024, 12, 31),
                value=datetime(2024, 12, 31)
            )
        
        submit_button = st.form_submit_button("Backtester")

# Zone principale
if not submit_button:
    
        st.markdown("""
        ### Description de la stratégie à rendement et à faible volatilité
        - Maintenir ORAC et SNTS à 18% chacun (36%)
        - Maintenir SGBC et ECOC à 5% chacun (10%)
        - Sélectionner les 16 meilleures actions à dividendes (54%)
        - Rééquilibrage si :
          - Cash ≥ 10% de l'actif total
          - Déviation des poids > ±2%
        
   
        
        ### Description de la stratégie Interne T1 2023
        1. **Titres à poids fixes** (49% du portefeuille)
           - STNS et ORAC : 15% chacun
           - SGBC et ECOC : 5% chacun
           - SIBC, ONTBF et CBIBF : 3% chacun
        
        2. **Titres avec limite à 10%**
           - Groupe 1 (13 titres à 2%) : BOAB, BOAC, BOABF, BOAN, CIEC, SDCC, PALC, SDSC, SOGC, CFAC, PRSC, TTLC, TTLS
           - Groupe 2 (8 titres à 1.25%) : NTLC, STBC, NSBC, SMBC, NEIC, BICC, BOAS, SHEC
           - Groupe 3 (14 titres à 1.07%) : ETIT, UNLC, FTSC, BOAM, SCRC, SPHC, BNBC, SICC, CABC, SIVC, SLBC, UNXC, SAFC, STAC
        
        3. **Conditions de rééquilibrage**
           - Si un titre à poids fixe dévie de plus de 2%
           - Si un titre libre dépasse 10%
        """)

else:
    try:
        # Chargement des données
        asset = Asset2(uploaded_prices, uploaded_dividends)
        
        # Création de la stratégie selon le choix
        if strategy_type == "High return & Low Vol.":
            strategy = Strategy2(
                initial_cash=initial_cash,
                initial_nav=initial_nav,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                asset=asset
            )
            strategy_name = "V2"
        else:
            strategy = Strategy3(
                initial_cash=initial_cash,
                initial_nav=initial_nav,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                asset=asset
            )
            strategy_name = "V3"
        
        history = strategy.get_portfolio_history()
        
        # Affichage des états initial et final
        for day, title in [(history.iloc[0], "État Initial"), (history.iloc[-1], "État Final")]:
            st.markdown(f"""
                <div class='section-container'>
                    <h3 style='color: maroon; text-align: center;'>{title}</h3>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**Date:** {day['Date'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**VL:** {day['NAV']:,.2f}")
            with col3:
                st.write(f"**Valorisation:** {day['Total_Value']:,.2f} XOF")
            with col4:
                st.write(f"**Cash:** {day['Cash']:,.2f} XOF")
            
            st.markdown("#### Composition du Portefeuille")
            state_df = day['State']
            st.dataframe(
                state_df.style.format({
                    'Quantity': '{:,.2f}',
                    'Price': '{:,.2f}',
                    'Value': '{:,.2f}',
                    'Weight': '{:.2%}'
                })
            )
            
            # if isinstance(day['Transactions'], pd.DataFrame) and not day['Transactions'].empty:
            #     st.markdown("#### Transactions")
            #     st.dataframe(
            #         day['Transactions'].style.format({
            #             'Quantity': '{:,.2f}',
            #             'Price': '{:,.2f}',
            #             'Value': '{:,.2f}'
            #         })
            #     )
            # st.markdown("</div>", unsafe_allow_html=True)
        
        # Graphiques de composition
        st.markdown("""
            <div class='section-container'>
                <h3 style='color: maroon; text-align: center;'>Composition du Portefeuille</h3>
        """, unsafe_allow_html=True)
        
        weight_col1, weight_col2 = st.columns(2)
        
        # État initial
        with weight_col1:
            initial_state = history.iloc[0]['State']
            fig_initial = px.bar(
                initial_state,
                x=initial_state.index,
                y=initial_state['Weight'] * 100,
                title='Composition Initiale',
                labels={'x': 'Titre', 'y': 'Poids (%)'},
            )
            fig_initial.update_traces(marker_color='maroon')
            fig_initial.update_layout(
                height=600,
                showlegend=False,
                title={
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                template='plotly_white',
                xaxis={'tickangle': 45},
                yaxis={'title': 'Poids (%)'},
                bargap=0.2
            )
            st.plotly_chart(fig_initial, use_container_width=True)
        
        # État final
        with weight_col2:
            final_state = history.iloc[-1]['State']
            fig_final = px.bar(
                final_state,
                x=final_state.index,
                y=final_state['Weight'] * 100,
                title='Composition Finale',
                labels={'x': 'Titre', 'y': 'Poids (%)'},
            )
            fig_final.update_traces(marker_color='darkred')
            fig_final.update_layout(
                height=600,
                showlegend=False,
                title={
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                template='plotly_white',
                xaxis={'tickangle': 45},
                yaxis={'title': 'Poids (%)'},
                bargap=0.2
            )
            st.plotly_chart(fig_final, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        
        
        # Tableau des poids sectoriels
        st.markdown("""
            <div class='section-container'>
            <h3 style='color: maroon; text-align: center;'>Analyse Sectorielle</h3>
         """, unsafe_allow_html=True)

        # Calcul des poids sectoriels
        current_sector_weights = calculate_sector_weights(final_state)

        # Création du tableau
        sector_data = {
           'Secteur': list(SECTORS.keys()),
           'Poids Marché': [SECTOR_METRICS[s]['market_weight'] * 100 for s in SECTORS],
           'Cible': [SECTOR_METRICS[s]['target'] * 100 for s in SECTORS],
           'Limite Déviation': [SECTOR_METRICS[s]['deviation'] * 100 for s in SECTORS],
           'Poids Portefeuille': [current_sector_weights[s] * 100 for s in SECTORS]
      }
        
        sector_df = pd.DataFrame(sector_data)
        sector_df = sector_df.round(2)

        # Affichage avec formatage
        st.dataframe(
           sector_df.style
               .format({
                 'Poids Marché': '{:.2f}%',
                 'Cible': '{:.2f}%',
                 'Limite Déviation': '{:.2f}%',
                 'Poids Portefeuille': '{:.2f}%'
            })
               .background_gradient(
                  subset=['Poids Portefeuille'],
                  text_color_threshold=0.5  # Seuil pour changer la couleur du texte

            )
        )

        st.markdown("</div>", unsafe_allow_html=True)
        
        
        
        
        # Graphique de performance
        st.markdown("""
            <div class='section-container'>
                <h3 style='color: maroon; text-align: center;'>Performance Comparée</h3>
        """, unsafe_allow_html=True)
        
        nav_series = strategy.get_nav_series()
        nav_rebased = 100 * nav_series / nav_series.iloc[0]
        benchmark = asset.get_benchmark_data(strategy.start_date, strategy.end_date)
        benchmark_rebased = 100 * benchmark / benchmark.iloc[0]
        
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(
            go.Scatter(
                x=nav_rebased.index,
                y=nav_rebased,
                name=f'Portefeuille {strategy_name}',
                line=dict(color='maroon', width=4)
            )
        )
        fig.add_trace(
            go.Scatter(
                x=benchmark_rebased.index,
                y=benchmark_rebased,
                name='BRVM-C',
                line=dict(color='black', width=4)
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
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métriques de performance
        metrics = strategy.get_performance_metrics()
        
        st.markdown("""
            <div class='section-container'>
                <h3 style='color: maroon; text-align: center;'>Métriques de Performance</h3>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Performance Portefeuille",
                f"{metrics['Performance Portefeuille (%)']:.2f}%",
                delta=f"{metrics['Performance Portefeuille (%)']:.2f}%"
            )
        with col2:
            st.metric(
                "Performance BRVM-C",
                f"{metrics['Performance BRVM-C (%)']:.2f}%",
                delta=f"{metrics['Performance BRVM-C (%)']:.2f}%"
            )
        with col3:
            st.metric(
                "Surperformance",
                f"{metrics['Surperformance (%)']:.2f}%",
                delta=f"{metrics['Surperformance (%)']:.2f}%"
            )
        
        # Indicateurs de risque
        risk_col1, risk_col2 = st.columns(2)
        with risk_col1:
            st.markdown("""
                <div class='metric-container'>
                    <h4 style='color: maroon;'>Indicateurs de Risque</h4>
                    <table style='width: 100%;'>
                        <tr>
                            <td>Volatilité Portefeuille</td>
                            <td style='text-align: right;'>{:.2f}%</td>
                        </tr>
                        <tr>
                            <td>Volatilité Benchmark</td>
                            <td style='text-align: right;'>{:.2f}%</td>
                        </tr>
                        <tr>
                            <td>Tracking Error</td>
                            <td style='text-align: right;'>{:.2f}%</td>
                        </tr>
                        <tr>
                            <td>Beta</td>
                            <td style='text-align: right;'>{:.2f}</td>
                        </tr>
                        <tr>
                            <td>Corrélation</td>
                            <td style='text-align: right;'>{:.2f}</td>
                        </tr>
                    </table>
                </div>
            """.format(
                metrics['Volatilité Portefeuille (%)'],
                metrics['Volatilité Benchmark (%)'],
                metrics['Tracking Error (%)'],
                metrics['Beta'],
                metrics['Corrélation'],
            ), unsafe_allow_html=True)
        
        with risk_col2:
            st.markdown("""
                <div class='metric-container'>
                    <h4 style='color: maroon;'>Autres Métriques</h4>
                    <table style='width: 100%;'>
                        <tr>
                            <td>Ratio de Sharpe</td>
                            <td style='text-align: right;'>{:.2f}</td>
                        </tr>
                        <tr>
                            <td>Ratio de Sortino</td>
                            <td style='text-align: right;'>{:.2f}</td>
                        </tr>
                        <tr>
                            <td>Ratio d'Information</td>
                            <td style='text-align: right;'>{:.2f}</td>
                        </tr>
                        <tr>
                            <td>Nombre de Rebalancements</td>
                            <td style='text-align: right;'>{}</td>
                        </tr>
                    </table>
                </div>
            """.format(
                metrics['Ratio de Sharpe'],
                metrics['Ratio de Sortino'],
                metrics['Ratio d\'Information'],
                metrics['Nombre Rebalancements']
            ), unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        
        # Graphique d'évolution du cash
        st.markdown("""
            <div class='section-container'>
                <h3 style='color: maroon; text-align: center;'>Évolution du Cash</h3>
        """, unsafe_allow_html=True)
        
        cash_series = pd.Series(history['Cash'].values, index=history['Date'])
        
        fig_cash = go.Figure()
        fig_cash.add_trace(
            go.Scatter(
                x=cash_series.index,
                y=cash_series.values,
                name='Cash',
                line=dict(color='maroon', width=4),
                fill='tozeroy'
            )
        )
        
        fig_cash.update_layout(
            title={
                'text': 'Évolution du Cash',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            template='plotly_white',
            height=400,
            yaxis_title='Cash (XOF)',
            showlegend=False
        )
        
        st.plotly_chart(fig_cash, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        
        # Export des données
        st.markdown("""
            <div class='section-container'>
                <h3 style='color: maroon; text-align: center;'>Export des Données</h3>
            </div>
        """, unsafe_allow_html=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Export des états
            all_states = []
            for _, row in history.iterrows():
                state_df = row['State'].copy()
                state_df['Date'] = row['Date']
                state_df['NAV'] = row['NAV']
                state_df['Total_Value'] = row['Total_Value']
                all_states.append(state_df)
            
            states_df = pd.concat(all_states)
            states_df.to_excel(writer, sheet_name='États', index=True)
            
            # Export des transactions
            all_transactions = []
            for _, row in history.iterrows():
                if isinstance(row['Transactions'], pd.DataFrame) and not row['Transactions'].empty:
                    trans_df = row['Transactions'].copy()
                    trans_df['Date'] = row['Date']
                    all_transactions.append(trans_df)
            
            if all_transactions:
                transactions_df = pd.concat(all_transactions)
                transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Export des métriques
            pd.DataFrame([metrics]).to_excel(writer, sheet_name='Métriques', index=False)
        
        st.download_button(
            label="📥 Télécharger les données",
            data=output.getvalue(),
            file_name=f"backtest_{strategy_name.lower()}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")