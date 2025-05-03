import pandas as pd
import numpy as np
from datetime import datetime

class Strategy3:
    def __init__(self, initial_cash, initial_nav, start_date, end_date, asset):
        """Initialisation de la stratégie de gestion de portefeuille"""
        # Paramètres initiaux
        self.initial_cash = initial_cash 
        self.initial_nav = initial_nav
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.asset = asset
        self.cash = initial_cash
        
        # Structure des poids cibles
        self.fixed_weights = {
            # Groupe 1: 40% au total
            'SNTS': 0.15, 'ORAC': 0.15,  # 30%
            'SGBC': 0.05, 'ECOC': 0.05,  # 10%
            # Groupe 2: 9% au total
            'SIBC': 0.03, 'ONTBF': 0.03, 'CBIBF': 0.03
        }
        
        # Autres groupes avec leurs poids initiaux
        self.free_weights = {
            # Groupe 3: 13 titres à 2% chacun
            'BOAB': 0.02, 'BOAC': 0.02, 'BOABF': 0.02, 
            'BOAN': 0.02, 'CIEC': 0.02, 'SDCC': 0.02,
            'PALC': 0.02, 'SDSC': 0.02, 'SOGC': 0.02,
            'CFAC': 0.02, 'PRSC': 0.02, 'TTLC': 0.02,
            'TTLS': 0.02,
            # Groupe 4: 8 titres à 1.25% chacun
            'NTLC': 0.0125, 'STBC': 0.0125, 'NSBC': 0.0125,
            'SMBC': 0.0125, 'NEIC': 0.0125, 'BICC': 0.0125,
            'BOAS': 0.0125, 'SHEC': 0.0125,
            # Groupe 5: 14 titres à 1.07% chacun
            'ETIT': 0.0107, 'UNLC': 0.0107, 'FTSC': 0.0107,
            'BOAM': 0.0107, 'SCRC': 0.0107, 'SPHC': 0.0107,
            'BNBC': 0.0107, 'SICC': 0.0107, 'CABC': 0.0107,
            'SIVC': 0.0107, 'SLBC': 0.0107, 'UNXC': 0.0107,
            'SAFC': 0.0107, 'STAC': 0.0107
        }
        
        # Dates disponibles
        self.available_dates = self.asset.data.index
        self.start_date = self._get_next_available_date(self.start_date)
        if self.start_date is None:
            raise ValueError("Aucune date valide trouvée")
        
        # Structure du portefeuille
        self.portfolio = {
            'Date': [],              # Dates de valorisation
            'State': [],             # États du portefeuille
            'NAV': [],              # Valeurs liquidatives
            'Total_Value': [],      # Valorisations totales
            'Portfolio_Value': [],  # Valorisation sans cash
            'Cash': [],            # Niveau de cash
            'Transactions': [],     # Transactions effectuées
            'Cash_Injections': [],  # Injections de cash
            'Dividends': []         # Dividendes collectés
        }
        
        # Démarrage du backtest
        self._initialize_portfolio()
        self._run_backtest()

    def _get_next_available_date(self, date):
        """Trouve la prochaine date disponible"""
        available_dates = self.available_dates[self.available_dates >= date]
        return available_dates[0] if not available_dates.empty else None

    def _initialize_portfolio(self):
        """Initialisation du portefeuille au premier jour"""
        try:
            # Vérification des prix disponibles
            prices = self.asset.get_current_prices(self.start_date)
            all_stocks = list(self.fixed_weights.keys()) + list(self.free_weights.keys())
            for stock in all_stocks:
                if stock not in prices:
                    raise ValueError(f"Prix manquant pour {stock}")

            # Création du portefeuille initial
            portfolio_state = pd.DataFrame(columns=['Quantity', 'Price', 'Value', 'Weight'])
            portfolio_value = self.initial_cash
            self.cash = 0
            
            # Allocation des titres fixes
            for stock, weight in self.fixed_weights.items():
                value = portfolio_value * weight
                quantity = value / prices[stock]
                portfolio_state.loc[stock] = [
                    quantity,
                    prices[stock],
                    value,
                    weight
                ]
            
            # Allocation des titres libres
            for stock, weight in self.free_weights.items():
                value = portfolio_value * weight
                quantity = value / prices[stock]
                portfolio_state.loc[stock] = [
                    quantity,
                    prices[stock],
                    value,
                    weight
                ]

            # Transactions initiales
            initial_transactions = pd.DataFrame({
                'Asset': portfolio_state.index,
                'Type': 'Acquisition',
                'Quantity': portfolio_state['Quantity'],
                'Price': portfolio_state['Price'],
                'Value': portfolio_state['Value']
            })

            # Enregistrement initial
            self._record_portfolio_state(
                date=self.start_date,
                state=portfolio_state,
                portfolio_value=portfolio_value,
                transactions=initial_transactions,
                dividends=0
            )

        except Exception as e:
            raise ValueError(f"Erreur d'initialisation: {str(e)}")

    def _update_portfolio(self, current_date):
        """Mise à jour quotidienne du portefeuille"""
        try:
            # Conservation de l'état précédent
            prev_state = self.portfolio['State'][-1].copy()
            current_prices = self.asset.get_current_prices(current_date)
            prev_total_value = self.portfolio['Total_Value'][-1]
            transactions = None
            cash_injection = 0
            dividends_collected = 0

            # Mise à jour des prix
            new_state = prev_state.copy()
            new_state['Price'] = current_prices
            new_state['Value'] = new_state['Quantity'] * new_state['Price']
            portfolio_value = new_state['Value'].sum()
            new_state['Weight'] = new_state['Value'] / portfolio_value

            # Collecte des dividendes
            for stock in new_state.index:
                stock_data = self.asset.get_stock_data(stock, current_date)
                if stock_data['dividend'] > 0:
                    dividend = new_state.loc[stock, 'Quantity'] * stock_data['dividend']
                    dividends_collected += dividend
                    self.cash += dividend

            # Valorisation totale
            total_value = portfolio_value + self.cash

            # Vérification des conditions de rééquilibrage
            needs_rebalancing = False
            
            # 1. Vérification des titres fixes (déviation > 2%)
            for stock, target_weight in self.fixed_weights.items():
                current_weight = new_state.loc[stock, 'Weight']
                if abs(current_weight - target_weight) > 0.02:
                    needs_rebalancing = True
                    break
            
            # 2. Vérification des limites à 10% sur les titres libres
            if not needs_rebalancing:
                for stock in self.free_weights.keys():
                    if new_state.loc[stock, 'Weight'] > 0.10:
                        needs_rebalancing = True
                        break

            # Rééquilibrage si nécessaire
            if needs_rebalancing:
                transactions = []
                
                # Rééquilibrage des titres fixes
                for stock, target_weight in self.fixed_weights.items():
                    target_value = portfolio_value * target_weight
                    new_quantity = target_value / current_prices[stock]
                    quantity_diff = new_quantity - new_state.loc[stock, 'Quantity']
                    
                    if abs(quantity_diff) > 0.000001:
                        transactions.append({
                            'Asset': stock,
                            'Type': 'Ajustement',
                            'Quantity': quantity_diff,
                            'Price': current_prices[stock],
                            'Value': abs(quantity_diff * current_prices[stock])
                        })
                        
                        new_state.loc[stock] = [
                            new_quantity,
                            current_prices[stock],
                            target_value,
                            target_weight
                        ]
                
                # Rééquilibrage des titres libres
                for stock, target_weight in self.free_weights.items():
                    target_value = portfolio_value * target_weight
                    new_quantity = target_value / current_prices[stock]
                    quantity_diff = new_quantity - new_state.loc[stock, 'Quantity']
                    
                    if abs(quantity_diff) > 0.000001:
                        transactions.append({
                            'Asset': stock,
                            'Type': 'Ajustement',
                            'Quantity': quantity_diff,
                            'Price': current_prices[stock],
                            'Value': abs(quantity_diff * current_prices[stock])
                        })
                        
                        new_state.loc[stock] = [
                            new_quantity,
                            current_prices[stock],
                            target_value,
                            target_weight
                        ]
                
                if transactions:
                    transactions = pd.DataFrame(transactions)

            # Enregistrement de l'état final
            self._record_portfolio_state(
                date=current_date,
                state=new_state,
                portfolio_value=portfolio_value,
                total_value=total_value,
                prev_total_value=prev_total_value,
                cash_injection=cash_injection,
                transactions=transactions,
                dividends=dividends_collected
            )

        except Exception as e:
            print(f"Erreur de mise à jour ({current_date}): {str(e)}")
            raise

    def _record_portfolio_state(self, date, state, portfolio_value, 
                              transactions=None, total_value=None,
                              prev_total_value=None, cash_injection=0,
                              dividends=0):
        """Enregistrement de l'état du portefeuille"""
        self.portfolio['Date'].append(date)
        self.portfolio['State'].append(state)
        self.portfolio['Portfolio_Value'].append(portfolio_value)
        
        total_value = total_value or (portfolio_value + self.cash)
        self.portfolio['Total_Value'].append(total_value)
        self.portfolio['Cash'].append(self.cash)
        self.portfolio['Cash_Injections'].append(cash_injection)
        self.portfolio['Dividends'].append(dividends)
        
        # Mise à jour de la VL
        prev_nav = self.portfolio['NAV'][-1] if self.portfolio['NAV'] else self.initial_nav
        prev_total_value = prev_total_value or self.initial_cash
        new_nav = prev_nav * (total_value / prev_total_value)
        self.portfolio['NAV'].append(new_nav)
        
        # Enregistrement des transactions
        if transactions is None:
            transactions = pd.DataFrame()
        elif isinstance(transactions, list):
            transactions = pd.DataFrame(transactions)
        
        self.portfolio['Transactions'].append(transactions)

    def _run_backtest(self):
        """Exécution du backtest"""
        backtest_dates = self.available_dates[
            (self.available_dates > self.start_date) & 
            (self.available_dates <= self.end_date)
        ]
        
        for date in backtest_dates:
            try:
                self._update_portfolio(date)
            except Exception as e:
                print(f"Erreur lors du backtest à la date {date}: {str(e)}")
                raise

    def get_portfolio_history(self):
        """Renvoie l'historique complet du portefeuille"""
        return pd.DataFrame({
            'Date': self.portfolio['Date'],
            'NAV': self.portfolio['NAV'],
            'Total_Value': self.portfolio['Total_Value'],
            'Cash': self.portfolio['Cash'],
            'Cash_Injections': self.portfolio['Cash_Injections'],
            'Dividends': self.portfolio['Dividends'],
            'State': self.portfolio['State'],
            'Transactions': self.portfolio['Transactions']
        })

    def get_nav_series(self):
        """Renvoie la série temporelle des VL"""
        return pd.Series(
            data=self.portfolio['NAV'],
            index=self.portfolio['Date'],
            name='Valeur Liquidative'
        )

    def get_performance_metrics(self):
        """Calcul des métriques de performance"""
        nav_series = self.get_nav_series()
        benchmark = self.asset.get_benchmark_data(self.start_date, self.end_date)
        
        # Calcul des rendements
        portfolio_return = (nav_series[-1] / nav_series[0] - 1)
        benchmark_return = (benchmark[-1] / benchmark[0] - 1)
        
        # Rendements quotidiens
        daily_returns = nav_series.pct_change()
        benchmark_returns = benchmark.pct_change()
        
        # Calcul des volatilités
        portfolio_vol = daily_returns.std() * np.sqrt(252)
        benchmark_vol = benchmark_returns.std() * np.sqrt(252)
        
        # Tracking error et autres métriques
        tracking_error = (daily_returns - benchmark_returns).std() * np.sqrt(252)
        sharpe_ratio = (portfolio_return - 0.06) / (portfolio_vol)
        
        # Ratio de Sortino
        negative_returns = daily_returns[daily_returns < 0]
        downside_vol = negative_returns.std() * np.sqrt(252)
        sortino_ratio = (portfolio_return - 0.06) / (downside_vol) if downside_vol != 0 else np.nan
        
        # Ratio d'Information
        information_ratio = (portfolio_return - benchmark_return) / (tracking_error)
        
        return {
            'Performance Portefeuille (%)': portfolio_return*100,
            'Performance BRVM-C (%)': benchmark_return*100,
            'Surperformance (%)': (portfolio_return - benchmark_return)*100,
            'Tracking Error (%)': tracking_error * 100,
            'Ratio de Sharpe': sharpe_ratio,
            'Ratio de Sortino': sortino_ratio,
            'Ratio d\'Information': information_ratio,
            'Volatilité Portefeuille (%)': portfolio_vol * 100,
            'Volatilité Benchmark (%)': benchmark_vol * 100,
            'Total Dividendes': sum(self.portfolio['Dividends']),
            'Total Injections': sum(self.portfolio['Cash_Injections']),
            'Nombre Rebalancements': sum(1 for t in self.portfolio['Transactions'] if not t.empty)
        }