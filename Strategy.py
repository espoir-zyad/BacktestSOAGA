import pandas as pd

class Strategy:
    def __init__(self, initial_cash, initial_nav, start_date, end_date, asset):
        """Initialisation de la stratégie de gestion de portefeuille"""
        self.initial_cash = initial_cash
        self.initial_nav = initial_nav
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.asset = asset
        
        # Dates disponibles dans les données
        self.available_dates = self.asset.data.index
        
        # Vérification de la date de début
        self.start_date = self._get_next_available_date(self.start_date)
        if self.start_date is None:
            raise ValueError("Aucune date valide trouvée dans les données")
        
        # Dictionnaire de suivi du portefeuille
        self.portfolio = {
            'Date': [],              # Dates de valorisation
            'State': [],             # États du portefeuille
            'NAV': [],              # Valeurs liquidatives
            'Total_Value': [],      # Valorisations totales
            'Transactions': []      # Transactions effectuées
        }
        
        # Initialisation et lancement du backtest
        self._initialize_portfolio()
        self._run_backtest()

    def _get_next_available_date(self, date):
        """Trouve la prochaine date disponible"""
        available_dates = self.available_dates[self.available_dates >= date]
        return available_dates[0] if not available_dates.empty else None

    def _initialize_portfolio(self):
        """Initialisation du portefeuille au jour 1"""
        prices = self.asset.get_current_prices(self.start_date)
        portfolio_state = pd.DataFrame(columns=['Quantity', 'Price', 'Value', 'Weight'])
        total_value = self.initial_cash

        # Ajout ORAC et SNTS (20% chacun)
        for fixed_asset in ['ORAC', 'SNTS']:
            value = total_value * 0.20
            quantity = value / prices[fixed_asset]
            portfolio_state.loc[fixed_asset] = [
                quantity,
                prices[fixed_asset],
                value,
                0.20
            ]
        
        # Ajout top 18 (3.33% chacun)
        top_performers = self.asset.get_top_performers(self.start_date)
        individual_weight = 0.0333

        for asset in top_performers.index:
            value = total_value * individual_weight
            quantity = value / prices[asset]
            portfolio_state.loc[asset] = [
                quantity,
                prices[asset],
                value,
                individual_weight
            ]
        
        # Enregistrement état initial
        self.portfolio['Date'].append(self.start_date)
        self.portfolio['State'].append(portfolio_state)
        self.portfolio['NAV'].append(self.initial_nav)
        self.portfolio['Total_Value'].append(total_value)
        
        # Enregistrement transactions initiales
        transactions = pd.DataFrame({
            'Asset': portfolio_state.index,
            'Type': 'Acquisition',
            'Quantity': portfolio_state['Quantity'],
            'Price': portfolio_state['Price'],
            'Value': portfolio_state['Value']
        })
        self.portfolio['Transactions'].append(transactions)

    def _update_portfolio(self, current_date):
        """Mise à jour quotidienne du portefeuille"""
        prev_state = self.portfolio['State'][-1].copy()
        current_prices = self.asset.get_current_prices(current_date)
        transactions = []
        
        # 1. Mise à jour des valorisations et poids
        prev_state['Price'] = current_prices
        prev_state['Value'] = prev_state['Quantity'] * prev_state['Price']
        total_value = prev_state['Value'].sum()
        prev_state['Weight'] = prev_state['Value'] / total_value
        
        # 2. Vérification dépassement 20% pour ORAC ou SNTS
        needs_rebalancing = False
        for fixed_asset in ['ORAC', 'SNTS']:
            if prev_state.loc[fixed_asset, 'Weight'] > 0.20:
                needs_rebalancing = True
                break
        
        if needs_rebalancing:
            # 2.1 Rééquilibrage ORAC et SNTS à 20%
            for fixed_asset in ['ORAC', 'SNTS']:
                target_value = total_value * 0.20
                new_quantity = target_value / current_prices[fixed_asset]
                old_quantity = prev_state.loc[fixed_asset, 'Quantity']
                
                transactions.append({
                    'Asset': fixed_asset,
                    'Type': 'Adjustment',
                    'Quantity': new_quantity - old_quantity,
                    'Price': current_prices[fixed_asset],
                    'Value': (new_quantity - old_quantity) * current_prices[fixed_asset]
                })
                
                prev_state.loc[fixed_asset] = [
                    new_quantity,
                    current_prices[fixed_asset],
                    target_value,
                    0.20
                ]
            
            # 2.2 Rééquilibrage autres titres à 3.33%
            other_assets = [asset for asset in prev_state.index if asset not in ['ORAC', 'SNTS']]
            for asset in other_assets:
                target_value = total_value * 0.0333
                new_quantity = target_value / current_prices[asset]
                old_quantity = prev_state.loc[asset, 'Quantity']
                
                transactions.append({
                    'Asset': asset,
                    'Type': 'Adjustment',
                    'Quantity': new_quantity - old_quantity,
                    'Price': current_prices[asset],
                    'Value': (new_quantity - old_quantity) * current_prices[asset]
                })
                
                prev_state.loc[asset] = [
                    new_quantity,
                    current_prices[asset],
                    target_value,
                    0.0333
                ]
        
        # 3. Gestion du top 18
        top_performers = self.asset.get_top_performers(current_date)
        current_assets = [asset for asset in prev_state.index if asset not in ['ORAC', 'SNTS']]
        available_top = [asset for asset in top_performers.index if asset not in prev_state.index]
        
        # 3.1 Remplacement un par un des titres hors top 18
        for current_asset in current_assets:
            if current_asset not in top_performers.index:
                # Récupération poids et valeur avant retrait
                old_weight = prev_state.loc[current_asset, 'Weight']
                old_value = prev_state.loc[current_asset, 'Value']
                
                # Retrait du titre actuel
                transactions.append({
                    'Asset': current_asset,
                    'Type': 'Cession',
                    'Quantity': -prev_state.loc[current_asset, 'Quantity'],
                    'Price': current_prices[current_asset],
                    'Value': -old_value
                })
                prev_state = prev_state.drop(current_asset)
                
                # Remplacement par le meilleur titre disponible
                if available_top:
                    new_asset = available_top.pop(0)
                    new_quantity = old_value / current_prices[new_asset]
                    
                    transactions.append({
                        'Asset': new_asset,
                        'Type': 'Acquisition',
                        'Quantity': new_quantity,
                        'Price': current_prices[new_asset],
                        'Value': old_value
                    })
                    
                    prev_state.loc[new_asset] = [
                        new_quantity,
                        current_prices[new_asset],
                        old_value,
                        old_weight
                    ]
        
        # 4. Mise à jour des données du portefeuille
        self.portfolio['Date'].append(current_date)
        self.portfolio['State'].append(prev_state)
        self.portfolio['Total_Value'].append(total_value)
        
        # 5. Calcul nouvelle VL
        prev_nav = self.portfolio['NAV'][-1]
        prev_total_value = self.portfolio['Total_Value'][-1]
    
        # Correction du calcul de la VL
        new_nav = prev_nav * (total_value / prev_total_value)
    
        self.portfolio['NAV'].append(new_nav)
        
        # 6. Enregistrement des transactions
        if transactions:
            self.portfolio['Transactions'].append(pd.DataFrame(transactions))
        else:
            self.portfolio['Transactions'].append(pd.DataFrame())

    def _run_backtest(self):
        """Exécution du backtest sur toute la période"""
        mask = (self.available_dates > self.start_date) & (self.available_dates <= self.end_date)
        backtest_dates = self.available_dates[mask]
        
        for date in backtest_dates:
            try:
                self._update_portfolio(date)
            except KeyError as e:
                print(f"Attention: Date {date} ignorée (données manquantes)")
                continue

    def display_portfolio_history(self):
        """Affichage de l'historique du portefeuille"""
        history = pd.DataFrame({
            'Date': self.portfolio['Date'],
            'NAV': self.portfolio['NAV'],
            'State': [state.to_dict() for state in self.portfolio['State']],
            'Total_Value': self.portfolio['Total_Value']
        })
        return history