from Asset2 import Asset2
from Strategy2 import Strategy2
import pandas as pd
from tabulate import tabulate
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def format_portfolio_state(state_df):
    """Formater l'état du portefeuille pour l'affichage"""
    formatted_state = state_df.copy()
    formatted_state.index.name = 'Titre'
    
    # Vérification et renommage des colonnes si nécessaire
    if 'Quantity' in formatted_state.columns:
        column_mapping = {
            'Quantity': 'Quantité',
            'Price': 'Prix',
            'Value': 'Valorisation',
            'Weight': 'Poids (%)'
        }
        formatted_state.rename(columns=column_mapping, inplace=True)
    
    # Formatage des valeurs
    formatted_state['Quantité'] = formatted_state['Quantité'].round(2)
    formatted_state['Prix'] = formatted_state['Prix'].map('{:,.2f}'.format)
    formatted_state['Valorisation'] = formatted_state['Valorisation'].map('{:,.2f}'.format)
    formatted_state['Poids (%)'] = (formatted_state['Poids (%)'] * 100).round(2).astype(str) + '%'
    
    return formatted_state

def format_transactions(transactions_df):
    """Formater les transactions pour l'affichage"""
    if transactions_df is None or transactions_df.empty:
        return None
        
    formatted_trans = transactions_df.copy()
    
    # Renommage des colonnes si nécessaire
    if 'Asset' in formatted_trans.columns:
        column_mapping = {
            'Asset': 'Titre',
            'Type': 'Type',
            'Quantity': 'Quantité',
            'Price': 'Prix',
            'Value': 'Montant'
        }
        formatted_trans.rename(columns=column_mapping, inplace=True)
    
    # Formatage des valeurs
    formatted_trans['Quantité'] = formatted_trans['Quantité'].round(2)
    formatted_trans['Prix'] = formatted_trans['Prix'].map('{:,.2f}'.format)
    formatted_trans['Montant'] = formatted_trans['Montant'].map('{:,.2f}'.format)
    
    return formatted_trans

def display_detailed_portfolio_history(history):
    """Afficher l'historique détaillé du portefeuille"""
    print("\nHISTORIQUE DÉTAILLÉ DU PORTEFEUILLE V2")
    print("="*120)
    
    for period, data in [("PREMIERS JOURS", history.head(5)), 
                        ("DERNIERS JOURS", history.tail(5))]:
        print(f"\n--- 5 {period} ---")
        
        for _, row in data.iterrows():
            print(f"\nDATE: {row['Date'].strftime('%d/%m/%Y')}")
            print(f"VALEUR LIQUIDATIVE: {row['NAV']:,.2f}")
            print(f"VALORISATION TOTALE: {row['Total_Value']:,.2f} XOF")
            print(f"CASH: {row['Cash']:,.2f} XOF")
            
            if row['Dividends'] > 0:
                print(f"DIVIDENDES: {row['Dividends']:,.2f} XOF")
            if row['Cash_Injections'] > 0:
                print(f"INJECTION DE CASH: {row['Cash_Injections']:,.2f} XOF")
            
            print("-"*120)
            
            # État du portefeuille
            formatted_state = format_portfolio_state(row['State'])
            print("\nÉTAT DU PORTEFEUILLE:")
            print(tabulate(formatted_state, headers='keys', tablefmt='grid'))
            
            # Transactions (vérification du type et non-vide)
            transactions = row['Transactions']
            if isinstance(transactions, pd.DataFrame) and not transactions.empty:
                formatted_trans = format_transactions(transactions)
                if formatted_trans is not None:
                    print("\nTRANSACTIONS:")
                    print(tabulate(formatted_trans, headers='keys', tablefmt='grid'))

def plot_performance_comparison(strategy):
    """Tracer la comparaison des performances"""
    nav_series = strategy.get_nav_series()
    benchmark = strategy.asset.get_benchmark_data(strategy.start_date, strategy.end_date)
    
    # Normalisation base 100
    nav_rebased = 100 * nav_series / nav_series.iloc[0]
    benchmark_rebased = 100 * benchmark / benchmark.iloc[0]
    
    # Création du graphique
    fig = make_subplots(rows=1, cols=1)
    
    fig.add_trace(go.Scatter(
        x=nav_rebased.index,
        y=nav_rebased,
        name='Portefeuille V2',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=benchmark_rebased.index,
        y=benchmark_rebased,
        name='BRVM-C',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Performance Comparée (Base 100)',
        xaxis_title='Date',
        yaxis_title='Performance (%)',
        template='plotly_white'
    )
    
    fig.show()

def main():
    try:
        print("\nTEST DE LA STRATÉGIE V2")
        print("="*100)
        
        # Initialisation
        asset = Asset2('Cours.xlsx', 'Dividendes.xlsx')
        strategy = Strategy2(
            initial_cash=90000000,
            initial_nav=100,
            start_date='2024-01-02',
            end_date='2024-12-31',
            asset=asset
        )
        
        # Affichage historique détaillé
        history = strategy.get_portfolio_history()
        display_detailed_portfolio_history(history)
        
        # Affichage des métriques de performance
        metrics = strategy.get_performance_metrics()
        print("\nMÉTRIQUES DE PERFORMANCE")
        print("="*100)
        for metric, value in metrics.items():
            if isinstance(value, float):
                print(f"{metric}: {value:,.2f}")
            else:
                print(f"{metric}: {value}")
        
        # Tracé du graphique
        plot_performance_comparison(strategy)
        
    except Exception as e:
        print(f"Erreur lors des tests: {str(e)}")
        raise

if __name__ == "__main__":
    main()