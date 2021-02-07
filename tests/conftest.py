import pytest
from brownie import config, Contract


@pytest.fixture
def token_weth(interface):
    yield Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def token_seth(interface):
    yield Contract("0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb")


@pytest.fixture
def token_ecrv(interface, gov):
    yield Contract("0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c", owner=gov)


@pytest.fixture
def andre(accounts, token_ecrv):
    # eCRV Gauge contract
    live_ecrv_whale = accounts.at("0x3C0FFFF15EA30C35d7A85B85c0782D6c94e1d238", force=True)
    live_ecrv_whale_bal = token_ecrv.balanceOf(live_ecrv_whale)

    # Andre, giver of tokens, and maker of yield
    a = accounts[0]

    # Take half of all eCRV
    token_ecrv.transfer(a, live_ecrv_whale_bal // 2, {"from": live_ecrv_whale})

    yield a


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def gov_live(accounts):
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def dev(accounts):
    yield accounts.at("0x7BACf22f747f2f4B983081C0AA76DdDFecd008AB", force=True)


@pytest.fixture
def vault_ecrv(pm, gov, rewards, guardian, token_ecrv):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token_ecrv, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def vault_ecrv_live(pm):
    Vault = pm(config["dependencies"][0]).Vault
    yield Vault.at("0x0e880118C29F095143dDA28e64d95333A9e75A47")


@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def strategy_ecrv(strategist, keeper, vault_ecrv, StrategyCurveEcrv, gov, gov_live, voter_proxy):
    strategy = strategist.deploy(StrategyCurveEcrv, vault_ecrv)
    strategy.setKeeper(keeper)

    debt_ratio = 10_000
    vault_ecrv.addStrategy(strategy, debt_ratio, 0, 1000, {"from": gov})
    voter_proxy.approveStrategy(strategy.gauge(), strategy, {"from": gov_live})

    yield strategy


@pytest.fixture
def strategy_ecrv_live(StrategyCurveEcrv):
    yield StrategyCurveEcrv.at("0x3B1a1AE6052ccD643a250fa843c1fB20F9246E1a")


@pytest.fixture
def voter_proxy(interface):
    yield interface.StrategyProxy("0x9a3a03C614dc467ACC3e81275468e033c98d960E")


@pytest.fixture
def nocoiner(accounts):
    # Has no tokens (DeFi is a ponzi scheme!)
    yield accounts[5]


@pytest.fixture
def pleb(accounts, andre, token_ecrv):
    # Small fish in a big pond
    a = accounts[6]
    # Has 0.01% of tokens (heard about this new DeFi thing!)
    bal = token_ecrv.totalSupply() // 10000
    token_ecrv.transfer(a, bal, {"from": andre})
    # # Unlimited Approvals
    # token_ecrv.approve(vault_ecrv, 2 ** 256 - 1, {"from": a})
    # # Deposit half their stack
    # vault_ecrv.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def chad(accounts, andre, token):
    # Just here to have fun!
    a = accounts[7]
    # Has 0.1% of tokens (somehow makes money trying every new thing)
    bal = token.totalSupply() // 1000
    token.transfer(a, bal, {"from": andre})
    # # Unlimited Approvals
    # token.approve(vault_weth, 2 ** 256 - 1, {"from": a})
    # # Deposit half their stack
    # vault_weth.deposit(bal // 2, {"from": a})
    yield a


@pytest.fixture
def whale(accounts, andre, token_ecrv):
    # Totally in it for the tech
    a = accounts[9]
    # Has 10% of tokens (was in the ICO)
    bal = token_ecrv.totalSupply() // 10
    token_ecrv.transfer(a, bal, {"from": andre})
    # # Unlimited Approvals
    # token_ecrv.approve(vault_ecrv, 2 ** 256 - 1, {"from": a})
    # # Deposit half their stack
    # vault_ecrv.deposit(bal // 2, {"from": a})
    yield a
