import pytest
from brownie import config

@pytest.fixture
def currency(interface):
    #curveseth token = 0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c
    yield interface.ERC20('0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c')

@pytest.fixture
def whale(accounts, web3, currency, chain):
    acc = accounts.at('0xceee009efa7166bf4b5475fcd9045f67fc8269b5', force=True)

    assert currency.balanceOf(acc)  > 0
    
    yield acc

@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]

@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract

@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def vault(pm, gov, rewards, guardian, currency):
    Vault = pm(config["dependencies"][0]).Vault
    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]

@pytest.fixture
def live_strategy(Strategy):
    strategy = Strategy.at('0xCa8C5e51e235EF1018B2488e4e78e9205064D736')

    yield strategy

@pytest.fixture
def live_vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0xdCD90C7f6324cfa40d7169ef80b12031770B4325')
    yield vault

@pytest.fixture
def strategy(strategist, keeper, vault, Strategy):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper)
    yield strategy

@pytest.fixture
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]