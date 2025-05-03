import pandas as pd
import numpy as np
from collections import defaultdict

class Asset2:
    def __init__(self, price_file: str, dividend_file: str):
        """Initialisation de la classe avec chargement des prix et dividendes"""
        # Chargement et préparation des données de prix
        self.data = pd.read_excel(price_file)
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        
        # Séparation et indexation du benchmark BRVM-C
        self.benchmark_data = self.data[['Date', 'BRVM C']].set_index('Date')
        self.data = self.data.set_index('Date')
        
        # Conversion des prix en format numérique (sans BRVM-C)
        price_columns = self.data.columns.difference(['BRVM C'])
        self.data[price_columns] = self.data[price_columns].apply(pd.to_numeric, errors='coerce')
        
        # Initialisation du dictionnaire des dividendes
        self.dividends_data = defaultdict(lambda: defaultdict(dict))
        self.load_dividends(dividend_file)

    
    def load_dividends(self, dividend_file):
        """Chargement des dividendes depuis le fichier Excel multi-feuilles"""
        try:
            xls = pd.ExcelFile(dividend_file)
        
            # Parcours de chaque feuille du fichier Excel
            for sheet_name in xls.sheet_names:
                # Lecture de la feuille avec parsing des dates
                df = pd.read_excel(
                   dividend_file,
                   sheet_name=sheet_name
                )
            
                # Conversion des dates avec format DD/MM/YYYY
                df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
            
                # Vérification et nettoyage des dates invalides
                df = df[pd.notna(df['Date'])]
            
                # Stockage des dividendes par titre et par date
                for _, row in df.iterrows():
                    try:
                        if pd.notna(row['Date']) and pd.notna(row['Montant']):
                            self.dividends_data[row['ISIN']][row['Date']] = {
                               'montant': float(row['Montant']),
                               'yield': float(row['Div Yield'])
                           }
                    except Exception as e:
                       print(f"Erreur lors du traitement de la ligne: {row}")
                       print(f"Error: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Erreur lors du chargement du fichier {dividend_file}")
            print(f"Error: {str(e)}")
    
    
    def get_consistent_dividend_payers(self, date):
        """Sélection des titres ayant:
        1. Versé des dividendes sur 2 années consécutives
        2. Une croissance positive du rendement
        3. Hors SNTS, ORAC, SGBC, ECOC"""
        
        current_date = pd.to_datetime(date)
        excluded_stocks = ['SNTS', 'ORAC', 'SGBC', 'ECOC']
        consistent_payers = []

        # Analyse de chaque titre du marché
        for stock in self.data.columns:
            if stock in excluded_stocks or stock == 'BRVM C':
                continue
            
            # Récupération des dividendes des 2 dernières années
            yearly_dividends = []
            check_years = [current_date.year - 1, current_date.year - 2]
            
            # Recherche des versements de dividendes pour chaque année
            for year in check_years:
                year_payment = None
                for div_date, div_info in self.dividends_data[stock].items():
                    if div_date.year == year and div_info['montant'] > 0:
                        year_payment = div_info
                        break
                
                if year_payment:
                    yearly_dividends.append(year_payment)
            
            # Vérification des critères de sélection
            if (len(yearly_dividends) == 2 and 
                yearly_dividends[0]['yield'] > yearly_dividends[1]['yield']):
                consistent_payers.append(stock)

        return consistent_payers

    def calculate_volatility(self, stock, date, months=12):
        """Calcul de la volatilité annualisée sur une période donnée"""
        end_date = pd.to_datetime(date)
        start_date = end_date - pd.DateOffset(months=months)
        
        # Extraction des données sur la période
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        stock_data = self.data.loc[mask, stock]
        
        # Calcul de la volatilité annualisée
        returns = stock_data.pct_change()
        volatility = returns.std() * np.sqrt(252)  # Annualisation
        return volatility

    def get_top_dividend_stocks(self, date, n=16):
        """Sélection des meilleurs titres selon:
        1. Top n par rendement de dividende de l'année précédente
        2. Tri final par volatilité croissante"""
        
        current_date = pd.to_datetime(date)
        consistent_payers = self.get_consistent_dividend_payers(date)
        
        # Collecte des métriques pour chaque titre
        stock_metrics = {}
        for stock in consistent_payers:
            try:
                # Recherche du dernier dividende
                last_year = current_date.year - 1
                last_year_dividend = None
                
                # Identification du dividende de l'année précédente
                for div_date, div_info in self.dividends_data[stock].items():
                    if div_date.year == last_year and div_info['montant'] > 0:
                        last_year_dividend = div_info
                        break
                
                if last_year_dividend:
                    volatility = self.calculate_volatility(stock, date)
                    stock_metrics[stock] = {
                        'div_yield': last_year_dividend['yield'],
                        'volatility': volatility
                    }
            except:
                continue
        
        # Sélection des n meilleurs rendements
        top_yield_stocks = sorted(stock_metrics.items(), 
                                key=lambda x: x[1]['div_yield'],
                                reverse=True)[:n]
        
        # Tri final par volatilité croissante
        final_ranking = sorted(top_yield_stocks, 
                             key=lambda x: x[1]['volatility'])
        
        return {stock: metrics for stock, metrics in final_ranking}

    def get_stock_data(self, stock, date):
        """Récupération des données complètes d'un titre à une date donnée"""
        date = pd.to_datetime(date)
        try:
            price = self.data.loc[date, stock]
            dividend_info = self.dividends_data[stock].get(date, {'montant': 0, 'yield': 0})
            return {
                'price': price,
                'dividend': dividend_info['montant'],
                'div_yield': dividend_info['yield']
            }
        except KeyError:
            raise KeyError(f"Données non disponibles pour {stock} à la date {date}")

    def get_current_prices(self, date):
        """Récupération des prix de tous les titres à une date donnée"""
        date = pd.to_datetime(date)
        try:
            prices = self.data.loc[date]
            return prices.drop('BRVM C') if 'BRVM C' in prices.index else prices
        except KeyError:
            raise KeyError(f"Aucune donnée disponible pour la date {date}")

    def get_benchmark_data(self, start_date=None, end_date=None):
        """Récupération des données du benchmark BRVM-C"""
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            mask = (self.data.index >= start_date) & (self.data.index <= end_date)
            benchmark_data = self.data.loc[mask, 'BRVM C']
            # Rebasage à 100
            benchmark_data = 100 * benchmark_data / benchmark_data.iloc[0]
            return benchmark_data
        return self.data['BRVM C']