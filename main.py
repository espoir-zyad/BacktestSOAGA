from Asset import Asset
from Strat import Strategy
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def format_portfolio_state(state_df):
    """Formater l'état du portefeuille pour l'affichage"""
    formatted_state = state_df.copy()
    formatted_state.index.name = 'Titre'
    formatted_state.columns = ['Quantité', 'Prix', 'Valorisation', 'Poids (%)']
    
    formatted_state['Quantité'] = formatted_state['Quantité'].round(2)
    formatted_state['Prix'] = formatted_state['Prix'].map('{:,.2f}'.format)
    formatted_state['Valorisation'] = formatted_state['Valorisation'].map('{:,.2f}'.format)
    formatted_state['Poids (%)'] = (formatted_state['Poids (%)'] * 100).round(2).astype(str) + '%'
    
    return formatted_state

def format_transactions(transactions_df):
    """Formater les transactions pour l'affichage"""
    if transactions_df.empty:
        return None
    
    formatted_trans = transactions_df.copy()
    formatted_trans.columns = ['Titre', 'Type', 'Quantité', 'Prix', 'Montant']
    
    formatted_trans['Quantité'] = formatted_trans['Quantité'].round(2)
    formatted_trans['Prix'] = formatted_trans['Prix'].map('{:,.2f}'.format)
    formatted_trans['Montant'] = formatted_trans['Montant'].map('{:,.2f}'.format)
    
    return formatted_trans





# ... existing code ...

def plot_performance_comparison(strategy, asset):
    """Tracer la comparaison des performances de manière interactive"""
    # Récupération des données NAV
    nav_series = strategy.get_nav_series()
    nav_rebased = 100 * nav_series / nav_series.iloc[0]
    
    # Récupération des données benchmark
    benchmark_data = asset.data.loc[strategy.start_date:strategy.end_date, 'BRVM C']
    benchmark_rebased = 100 * benchmark_data / benchmark_data.iloc[0]
    
    # Création du graphique interactif
    fig = make_subplots(rows=1, cols=1)
    
    # Ajout des courbes
    fig.add_trace(
        go.Scatter(
            x=nav_rebased.index,
            y=nav_rebased.values,
            name='Portefeuille',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='Date: %{x}<br>Performance: %{y:.2f}%<extra></extra>'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=benchmark_rebased.index,
            y=benchmark_rebased.values,
            name='BRVM-C',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            hovertemplate='Date: %{x}<br>Performance: %{y:.2f}%<extra></extra>'
        )
    )
    
    # Personnalisation du graphique
    fig.update_layout(
        title={
            'text': 'Performance Comparée : Portefeuille vs BRVM-C (Base 100)',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20)
        },
        xaxis_title='Date',
        yaxis_title='Performance (%)',
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        template='plotly_white',
        height=700
    )
    
    # Ajout d'une ligne horizontale à 100
    fig.add_hline(
        y=100, 
        line_dash="dot", 
        line_color="gray",
        annotation_text="Base 100",
        annotation_position="bottom right"
    )
    
    # Configuration des axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray',
        showspikes=True,
        spikemode='across',
        spikesnap='cursor',
        showline=True,
        showticklabels=True
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='LightGray',
        showspikes=True,
        spikemode='across',
        spikesnap='cursor',
        showline=True
    )
    
    # Affichage dans le navigateur par défaut
    fig.show()
    
    # Sauvegarde en HTML pour consultation ultérieure
    #fig.write_html("performance_comparison.html")


def display_detailed_portfolio_history(history_data):
    """Afficher l'historique détaillé du portefeuille"""
    print("\nHISTORIQUE DÉTAILLÉ DU PORTEFEUILLE")
    print("="*120)
    print("5 PREMIERS ET 5 DERNIERS JOURS")
    print("="*120)
    
    first_five = history_data.head(5)
    last_five = history_data.tail(5)
    
    def display_day_info(row):
        """Afficher les informations d'une journée"""
        print(f"\nDATE: {row['Date'].strftime('%d/%m/%Y')}")
        print(f"VALEUR LIQUIDATIVE: {row['NAV']:,.2f}")
        print(f"VALORISATION TOTALE: {row['Total_Value']:,.2f} XOF")
        print("-"*120)
        
        state_df = pd.DataFrame.from_dict(row['State'])
        formatted_state = format_portfolio_state(state_df)
        
        print("\nÉTAT DU PORTEFEUILLE:")
        print(tabulate(
            formatted_state,
            headers='keys',
            tablefmt='pretty',
            showindex=True
        ))
        
        if row['Transactions'] is not None and not row['Transactions'].empty:
            formatted_trans = format_transactions(row['Transactions'])
            if formatted_trans is not None:
                print("\nTRANSACTIONS DU JOUR:")
                print(tabulate(
                    formatted_trans,
                    headers='keys',
                    tablefmt='pretty',
                    showindex=False
                ))
        print("-"*120)
    
    print("\n--- 5 PREMIERS JOURS ---")
    for _, row in first_five.iterrows():
        display_day_info(row)
    
    print("\n"+"."*120+"\n")
    
    print("\n--- 5 DERNIERS JOURS ---")
    for _, row in last_five.iterrows():
        display_day_info(row)

def main():
    try:
        # Initialisation
        asset = Asset('Cours.xlsx')
        
        print(f"\n{'='*100}")
        print("PÉRIODE D'ANALYSE")
        print(f"{'='*100}")
        print(f"Du: {asset.data.index.min().strftime('%d/%m/%Y')}")
        print(f"Au: {asset.data.index.max().strftime('%d/%m/%Y')}")
        print(f"{'='*100}\n")
        
        strategy = Strategy(
            initial_cash=90000000,
            initial_nav=100,
            start_date='2023-06-01',
            end_date='2024-12-31',
            asset=asset
        )
        
        # Affichage historique détaillé
        history = strategy.display_portfolio_history()
        display_detailed_portfolio_history(history)
        
        # Tracé du graphique de performance
        plot_performance_comparison(strategy, asset)
        
        # Calcul des performances
        initial_nav = strategy.initial_nav
        final_nav = strategy.portfolio['NAV'][-1]
        total_return = ((final_nav - initial_nav) / initial_nav) * 100
        
        benchmark_start = asset.data.loc[strategy.start_date, 'BRVM C']
        benchmark_end = asset.data.loc[strategy.end_date, 'BRVM C']
        benchmark_return = ((benchmark_end - benchmark_start) / benchmark_start) * 100
        
        # Affichage des performances
        print("\nRÉSUMÉ DES PERFORMANCES")
        print("="*100)
        print(f"VL Initiale: {initial_nav:,.2f}")
        print(f"VL Finale: {final_nav:,.2f}")
        print(f"Performance Portefeuille: {total_return:,.2f}%")
        print(f"Performance BRVM-C: {benchmark_return:,.2f}%")
        print(f"Surperformance: {total_return - benchmark_return:,.2f}%")
        print("="*100)
        
    except ValueError as e:
        print(f"Erreur: {e}")
    except KeyError as e:
        print(f"Erreur: {e}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")

if __name__ == "__main__":
    main()