from helpers import genericStateOfStrat, genericStateOfVault
from brownie import Wei

# TODO: Add tests here that show the normal operation of this strategy
#       Suggestions to include:
#           - strategy loading and unloading (via Vault addStrategy/revokeStrategy)
#           - change in loading (from low to high and high to low)
#           - strategy operation at different loading levels (anticipated and "extreme")


def test_ops_lvie(
    token_seth, token_ecrv, strategy_ecrv_live, chain, vault_ecrv_live, dev, whale
):
    token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    whalebefore = token_ecrv.balanceOf(whale)
    vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    strategy_ecrv_live.harvest({"from": dev})

    print("sETH = ", token_seth.balanceOf(strategy_ecrv_live) / 1e18)
    print("eCRV = ", strategy_ecrv_live.balance() / 1e18)

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((vault_ecrv_live.totalAssets() - 1000 * 1e18) * 12) / (1000 * 1e18)
        ),
    )

    vault_ecrv_live.withdraw({"from": whale})
    print("\nWithdraw")
    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
    print("Whale profit: ", (token_ecrv.balanceOf(whale) - whalebefore) / 1e18)


def test_migrate_live(
    token_ecrv,
    StrategyCurveEcrv,
    strategy_ecrv_live,
    chain,
    vault_ecrv_live,
    whale,
    dev,
):
    token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((vault_ecrv_live.totalAssets() - 100 * 1e18) * 12) / (100 * 1e18)
        ),
    )

    strategy_ecrv2 = dev.deploy(StrategyCurveEcrv, vault_ecrv_live)
    vault_ecrv_live.migrateStrategy(strategy_ecrv_live, strategy_ecrv2, {"from": dev})
    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfStrat(strategy_ecrv2, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)


def test_revoke_live(token_ecrv, strategy_ecrv_live, vault_ecrv_live, whale, dev):
    token_ecrv.approve(vault_ecrv_live, 2 ** 256 - 1, {"from": whale})
    vault_ecrv_live.deposit(Wei("100 ether"), {"from": whale})
    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)

    vault_ecrv_live.revokeStrategy(strategy_ecrv_live, {"from": dev})

    strategy_ecrv_live.harvest({"from": dev})

    genericStateOfStrat(strategy_ecrv_live, token_ecrv, vault_ecrv_live)
    genericStateOfVault(vault_ecrv_live, token_ecrv)
