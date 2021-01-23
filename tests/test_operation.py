# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat,genericStateOfVault
import random
import brownie

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")

def test_add_strategy(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface):
    rate_limit = 1_000_000_000 *1e18
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, rate_limit, 1000, {"from": gov})

def test_deposit(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface):
    test_add_strategy(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface)
    currency.approve(vault, 2 ** 256 - 1, {"from": whale} )
    whalebefore = currency.balanceOf(whale)
    whale_deposit  = 100 *1e18
    vault.deposit(whale_deposit, {"from": whale})

def test_harvest(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface):
    test_deposit(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface)
    strategy.harvest({'from': strategist})

def test_operation(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface):
    test_harvest(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    chain.sleep(2592000)
    chain.mine(1)

    print("~~~ PREPARING STRATEGIST HARVEST ~~~")
    strategy.harvest({'from': strategist})
    steth = interface.ERC20('0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84')

    print("~~~ STRATEGIST HARVEST CONCLUDED ~~~")
    print("steth = ", steth.balanceOf(strategy)/1e18)
    print("eth = ", strategy.balance()/1e18)

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-100*1e18)*12)/(100*1e18)))

def test_withdraw(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface):
    whalebefore = currency.balanceOf(whale)
    print("Vault total supply before:", vault.totalSupply())
    test_operation(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface)
    vault.withdraw({"from": strategist})
    vault.withdraw({"from": whale})
    vault.withdraw({"from": rewards})
    print("Vault total supply after:", vault.totalSupply())
    
    print("\nWithdraw")
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
    print("Whale profit: ", (currency.balanceOf(whale) - whalebefore)/1e18)

def test_reduce_limit(currency, Strategy, strategy, rewards, chain,vault, whale,gov,strategist, interface):
    test_harvest(currency, strategy, rewards, chain, vault, whale, gov, strategist, interface)
    vault.revokeStrategy(strategy, {'from': gov})
    strategy.harvest({'from': strategist})

    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)
