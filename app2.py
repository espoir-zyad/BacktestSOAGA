import streamlit as st
import pandas as pd
import numpy as np
from Asset2 import Asset2
from Strategy2 import Strategy2
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import io
from datetime import datetime
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="SOAGA - Backtesting V2",
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
       <h3>Plateforme de Backtesting SOAGA - BRVM V2</h3>
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
        col1, col2 = st.columns(2)
        with col1:
            uploaded_prices = st.file_uploader("Cours historiques", type=['xlsx'])
        with col2:
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
            min_date = datetime(2024, 1, 1)
            max_date = datetime(2024, 12, 31)
            default_start = datetime(2024, 1, 1)
        
            start_date = st.date_input(
               "Date de début",
                value=default_start,
                min_value=min_date,
                max_value=max_date,
                key='start_date'
            )
        
            # Vérification et correction de la date de début
            if start_date < min_date.date():
               start_date = min_date.date()
               st.warning('Date de début ajustée au 01/01/2024')
            elif start_date > max_date.date():
               start_date = max_date.date()
               st.warning('Date de début ajustée au 31/12/2024')
                
        with col2:
           # La date de fin doit être au moins égale à la date de début
           end_date = st.date_input(
              "Date de fin",
              value=max_date,
              min_value=start_date,
              max_value=max_date,
              key='end_date'
            )
        
           # Vérification et correction de la date de fin
           if end_date < start_date:
              end_date = start_date
              st.warning('Date de fin ajustée à la date de début')
           elif end_date > max_date.date():
              end_date = max_date.date()
              st.warning('Date de fin ajustée au 31/12/2024')
        
        submit_button = st.form_submit_button("Backtester")

# Zone principale
if not submit_button:
    st.markdown("""
    ### Guide d'utilisation
    1. Chargez vos données historiques (cours et dividendes)
    2. Définissez les paramètres initiaux :
       - VL initiale
       - Cash initial
       - Période de backtest
    3. Lancez le backtest
    
    ### Description de la stratégie
    La stratégie V2 consiste à :
    - Maintenir ORAC et SNTS à 18% chacun (36%)
    - Maintenir SGBC et ECOC à 5% chacun (10%)
    - Sélectionner les 16 meilleures actions à dividendes (54%)
    - Rééquilibrage si :
      - Cash ≥ 10% de l'actif total
      - Déviation des poids > ±2%
    """)

else:
    try:
        # Chargement des données et exécution
        asset = Asset2(uploaded_prices, uploaded_dividends)
        strategy = Strategy2(
            initial_cash=initial_cash,
            initial_nav=initial_nav,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            asset=asset
        )
        
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
        
        # Création des graphiques de composition
        st.markdown("""
          <div class='section-container'>
          <h3 style='color: maroon; text-align: center;'>Composition du Portefeuille</h3>
         """, unsafe_allow_html=True)
        # Graphiques côte à côte
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
                xaxis={'tickangle': 45},  # Rotation des labels pour meilleure lisibilité
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
                xaxis={'tickangle': 45},  # Rotation des labels pour meilleure lisibilité
                yaxis={'title': 'Poids (%)'},
                bargap=0.2
           )
            st.plotly_chart(fig_final, use_container_width=True)

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
                name='Portefeuille V2',
                line=dict(color='maroon', width=3)
            )
        )
        fig.add_trace(
            go.Scatter(
                x=benchmark_rebased.index,
                y=benchmark_rebased,
                name='BRVM-C',
                line=dict(color='black', width=3)
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
                   </table>
             </div>
             """.format(
                 metrics['Volatilité Portefeuille (%)'],
                 metrics['Volatilité Benchmark (%)'],
                 metrics['Tracking Error (%)']
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
        
        st.download_button(
            label="📥 Télécharger les données",
            data=output.getvalue(),
            file_name=f"backtest_v2_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    except Exception as e:
        st.error(f"Une erreur s'est produite: {str(e)}")