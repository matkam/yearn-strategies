from helpers import genericStateOfStrat, genericStateOfVault
from brownie import Wei


def test_ops_live(token_seth, token_ecrv, strategy_ecrv_live, chain, vault_ecrv_live, dev, whale, gov_live, devychad):
    # proxy = Contract("0x9a3a03c614dc467acc3e81275468e033c98d960e")
    # gauge = "0x3C0FFFF15EA30C35d7A85B85c0782D6c94e1d238"
    # proxy.approveStrategy(gauge, strategy_ecrv_live_new, {"from": gov_live})

    # strategy_ecrv_live.harvest({"from": devychad})
    # vault_ecrv_live.migrateStrategy(strategy_ecrv_live, strategy_ecrv_live, {"from": devychad})
    # strategy_ecrv_live.harvest({"from": devychad})

    # token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    # whalebefore = token_ecrv.balanceOf(whale)
    # vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    assets_before = vault_ecrv_live.totalAssets()
    strategy_ecrv_live.harvest({"from": dev})

    print("sETH = ", token_seth.balanceOf(strategy_ecrv_live) / 1e18)
    print("eCRV = ", strategy_ecrv_live.balance() / 1e18)

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    print(
        "\nEstimated APR: ", "{:.2%}".format((vault_ecrv_live.totalAssets() - assets_before) / assets_before * 12),
    )

    vault_ecrv_live.withdraw({"from": dev})
    print("\nWithdraw")
    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
    # print("Whale profit: ", (token_ecrv.balanceOf(whale) - whalebefore) / 1e18)


def test_migrate_live(
    token_ecrv, StrategyCurveEcrv, strategy_ecrv_live, chain, vault_ecrv_live, whale, dev, devychad,
):
    # token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    # vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    # strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    assets_before = vault_ecrv_live.totalAssets()
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    print(
        "\nEstimated APR: ", "{:.2%}".format((vault_ecrv_live.totalAssets() - assets_before) / assets_before * 12),
    )

    strategy_ecrv2 = dev.deploy(StrategyCurveEcrv, vault_ecrv_live)
    vault_ecrv_live.migrateStrategy(strategy_ecrv_live, strategy_ecrv2, {"from": devychad})
    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfStrat(strategy_ecrv2, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)


def test_revoke_live(token_ecrv, strategy_ecrv_live, vault_ecrv_live, whale, devychad):
    # token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    # vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    # strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    vault_ecrv_live.revokeStrategy(strategy_ecrv_live, {"from": devychad})

    strategy_ecrv_live.harvest({"from": devychad})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
