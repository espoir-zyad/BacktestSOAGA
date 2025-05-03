import pandas as pd
import numpy as np

class Asset:
    def __init__(self, excel_file):
        """Initialisation de la classe des Actifs avec le chargement des données 
        historiques de tous les titres du marché"""
        
        #Chargement du jeu de données
        self.data = pd.read_excel(excel_file)
        #Conversion de la colonne Date du jeu de données en datetime
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        
        #Extraction de la colonne du benchmark avec indexation de la date
        self.benchmark_data = self.data[['Date', 'BRVM C']].set_index('Date')
        
        #Indexation de la date dans le jeu de données des titres 
        self.data = self.data.set_index('Date')
        
        # Extraction des colonnes des titres sauf ceux de la BRVM-C avec conversion des colonnes en numérique
        price_columns = self.data.columns.difference(['BRVM C'])
        self.data[price_columns] = self.data[price_columns].apply(pd.to_numeric, errors='coerce')

    def calculate_performance(self, date, months=6):
        """Calcule de la performance des titres sur les 6 derniers mois sauf 'ORAC', 'SNTS' et 'BRVM C'"""
        
        # Récupération et conversion de la Date actuelle en Datatime
        end_date = pd.to_datetime(date)
        #Identification de la Date exacte de début du calcul
        start_date = end_date - pd.DateOffset(months=months)
        
        #Identification de la période de test
        mask = (self.data.index >= start_date) & (self.data.index <= end_date)
        period_data = self.data[mask]
        
        # Si la période est vide, on ne fait rien
        if period_data.empty:
            raise ValueError(f"No data found between {start_date} and {end_date}")
            
        # Calcul de la performance sur les 6 derniers mois
        start_prices = period_data.iloc[0]
        end_prices = period_data.iloc[-1]
        performance = ((end_prices - start_prices) / start_prices * 100).astype(float)
        
        # Effacer les performances de ORAC, SNTS et BRVM C 
        performance = performance.drop(['ORAC', 'SNTS', 'BRVM C'], errors='ignore')
        
        return performance

    def get_top_performers(self, date, n=18):
        """Récupération du Top 18 Performeurs sans ORAC and SNTS"""
        
        #Appel de la méthode calculate_performance et récupération du Top n avec la fonction nlargest
        performance = self.calculate_performance(date)
        performance = performance.astype(float)
        return performance.nlargest(n)

    def get_current_prices(self, date):
        """Récupération des prix de tous les titres par Date"""
        date = pd.to_datetime(date)
        try:
            #Exclusion de la colonne BRVM C de la récupération
            prices = self.data.loc[date].drop('BRVM C')
            return prices.astype(float)
        except KeyError:
            raise KeyError(f"No data available for date {date}")

    def get_benchmark_data(self, start_date=None, end_date=None):
        """Récupération des cours du benchmark pour une période spécifiée"""
        if start_date and end_date:
           start_date = pd.to_datetime(start_date)
           end_date = pd.to_datetime(end_date)
           mask = (self.data.index >= start_date) & (self.data.index <= end_date)
           benchmark_data = self.data.loc[mask, 'BRVM C']
           # Rebasage à 100 
           benchmark_data = 100 * benchmark_data / benchmark_data.iloc[0]
           return benchmark_data
        return self.data['BRVM C']