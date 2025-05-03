import pandas as pd
from Asset2 import Asset2
from tabulate import tabulate

def test_asset2():
    # Configuration initiale
    price_file = "Cours.xlsx"
    dividend_file = "Dividendes.xlsx"
    test_date = "2024-05-27"  # Date de test
    
    try:
        print("\n" + "="*100)
        print("INITIALISATION ET CHARGEMENT DES DONNÉES")
        print("="*100)
        
        # Initialisation de Asset2
        asset = Asset2(price_file, dividend_file)
        print("✓ Initialisation réussie")
        
        print("\n" + "="*100)
        print("TEST DES MÉTHODES DE LA CLASSE")
        print("="*100)
        
        # 1. Test de get_consistent_dividend_payers
        print("\n1. TITRES AVEC DIVIDENDES CONSISTANTS")
        print("-"*100)
        consistent_payers = asset.get_consistent_dividend_payers(test_date)
        print(f"Nombre de titres: {len(consistent_payers)}")
        print("Titres sélectionnés:", ", ".join(consistent_payers))
        
        # 2. Test de get_top_dividend_stocks
        print("\n2. TOP 16 DES TITRES PAR RENDEMENT ET VOLATILITÉ")
        print("-"*100)
        top_stocks = asset.get_top_dividend_stocks(test_date)
        
        # Création d'un DataFrame pour un affichage plus lisible
        top_df = pd.DataFrame.from_dict(top_stocks, orient='index')
        top_df.columns = ['Rendement (%)', 'Volatilité (%)']
        top_df['Rendement (%)'] = top_df['Rendement (%)'].round(2)
        top_df['Volatilité (%)'] = top_df['Volatilité (%)'].round(2)
        print(tabulate(top_df, headers='keys', tablefmt='grid'))
        
        # 3. Test de get_stock_data pour quelques titres
        print("\n3. DONNÉES DÉTAILLÉES DES TITRES")
        print("-"*100)
        for stock in list(top_stocks.keys())[:5]:  # Test sur les 5 premiers titres
            try:
                data = asset.get_stock_data(stock, test_date)
                print(f"\nTitre: {stock}")
                print(f"Prix: {data['price']:,.2f}")
                print(f"Dividende: {data['dividend']:,.2f}")
                print(f"Rendement: {data['div_yield']*100:.2f}%")
            except Exception as e:
                print(f"Erreur pour {stock}: {str(e)}")
        
        # 4. Test de get_current_prices
        print("\n4. PRIX ACTUELS DES TITRES")
        print("-"*100)
        current_prices = asset.get_current_prices(test_date)
        prices_df = pd.DataFrame(current_prices).round(2)
        prices_df.columns = ['Prix']
        print(tabulate(prices_df.head(10), headers='keys', tablefmt='grid'))
        print("... (affichage limité aux 10 premiers titres)")
        
        # 5. Test de get_benchmark_data
        print("\n5. DONNÉES DU BENCHMARK (BRVM-C)")
        print("-"*100)
        start_date = "2024-01-02"
        end_date = "2024-01-31"
        benchmark_data = asset.get_benchmark_data(start_date, end_date)
        bench_df = pd.DataFrame(benchmark_data)
        bench_df.columns = ['BRVM-C']
        print(tabulate(bench_df.head(), headers='keys', tablefmt='grid'))
        print("... (affichage limité aux 5 premiers jours)")
        
        print("\n" + "="*100)
        print("TESTS TERMINÉS AVEC SUCCÈS")
        print("="*100)
        
        return asset
        
    except Exception as e:
        print(f"\nErreur lors du test:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_asset2()