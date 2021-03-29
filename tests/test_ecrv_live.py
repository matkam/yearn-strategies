from helpers import genericStateOfStrat, genericStateOfVault
from brownie import Wei


def test_ops_live(
    token_seth,
    token_ecrv,
    strategy_ecrv_live_old,
    strategy_ecrv_live,
    chain,
    vault_ecrv_live_old,
    vault_ecrv_live,
    voter_proxy,
    dev,
    whale,
    gov_live,
    devychad,
):
    # vault_ecrv_live_old.updateStrategyDebtRatio(strategy_ecrv_live_old, 0, {"from": devychad})
    # strategy_ecrv_live_old.harvest({"from": dev})

    # gauge = "0x3C0FFFF15EA30C35d7A85B85c0782D6c94e1d238"
    # voter_proxy.approveStrategy(gauge, strategy_ecrv_live, {"from": gov_live})

    # vault_ecrv_live.setDepositLimit(2 ** 256 - 1, {"from": dev})

    # strategy_ecrv_live.harvest({"from": devychad})
    # vault_ecrv_live.migrateStrategy(strategy_ecrv_live, strategy_ecrv_live, {"from": devychad})
    # strategy_ecrv_live.harvest({"from": devychad})

    whalebefore = token_ecrv.balanceOf(whale)
    token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    assets_before = vault_ecrv_live.totalAssets()
    strategy_ecrv_live.harvest({"from": dev})

    print("eCRV = ", strategy_ecrv_live.balance() / 1e18)

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    print(
        "\nEstimated APR: ", "{:.2%}".format((vault_ecrv_live.totalAssets() - assets_before) / assets_before * 12),
    )

    chain.sleep(21600)  # 6 hour sandwitch protection
    vault_ecrv_live.withdraw({"from": whale})
    print("\nWithdraw")
    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
    print("Whale profit: ", (token_ecrv.balanceOf(whale) - whalebefore) / 1e18)


def test_migrate_live(token_ecrv, StrategyCurveEcrv, strategy_ecrv_live, chain, vault_ecrv_live, whale, dev, devychad, gov_live, voter_proxy):
    strategy_ecrv_live.harvest({"from": gov_live})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    vaultAssets = vault_ecrv_live.totalAssets()
    vaultDebt = vault_ecrv_live.totalDebt()
    vaultLoose = token_ecrv.balanceOf(vault_ecrv_live)
    assert vaultAssets == vaultDebt + vaultLoose

    strategy_ecrv2 = dev.deploy(StrategyCurveEcrv, vault_ecrv_live)

    # temporary until actual migration
    vault_ecrv_live.updateStrategyDebtRatio(strategy_ecrv_live, 0, {"from": gov_live})
    strategy_ecrv_live.harvest({"from": gov_live})

    vault_ecrv_live.migrateStrategy(strategy_ecrv_live, strategy_ecrv2, {"from": gov_live})
    voter_proxy.approveStrategy(strategy_ecrv2.gauge(), strategy_ecrv2, {"from": gov_live})
    vault_ecrv_live.updateStrategyDebtRatio(strategy_ecrv2, 9_980, {"from": gov_live})  # temporary
    strategy_ecrv2.harvest({"from": gov_live})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfStrat(strategy_ecrv2, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    assert vault_ecrv_live.totalAssets() >= vaultAssets
    assert vault_ecrv_live.totalAssets() < vaultAssets + Wei("0.1 ether")
    assert vault_ecrv_live.totalDebt() + token_ecrv.balanceOf(vault_ecrv_live) >= vaultDebt + vaultLoose
    assert vault_ecrv_live.totalDebt() + token_ecrv.balanceOf(vault_ecrv_live) < vaultDebt + vaultLoose + Wei("0.1 ether")

    # teardown
    vault_ecrv_live.updateStrategyDebtRatio(strategy_ecrv2, 0, {"from": gov_live})
    strategy_ecrv2.harvest({"from": gov_live})
    voter_proxy.approveStrategy(strategy_ecrv_live.gauge(), strategy_ecrv_live, {"from": gov_live})
    vault_ecrv_live.updateStrategyDebtRatio(strategy_ecrv_live, 1000, {"from": gov_live})


def test_revoke_live(token_ecrv, strategy_ecrv_live, vault_ecrv_live, whale, gov_live):
    token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": gov_live})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    vault_ecrv_live.revokeStrategy(strategy_ecrv_live, {"from": gov_live})
    strategy_ecrv_live.harvest({"from": gov_live})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
