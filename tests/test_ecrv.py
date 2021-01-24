from helpers import genericStateOfStrat, genericStateOfVault


def test_opsss(
    token_seth, token_ecrv, strategy_ecrv, chain, vault_ecrv, whale, gov, strategist,
):
    rate_limit = 1_000_000_000 * 1e18
    debt_ratio = 10_000
    vault_ecrv.addStrategy(strategy_ecrv, debt_ratio, rate_limit, 1000, {"from": gov})

    token_ecrv.approve(vault_ecrv, 2 ** 256 - 1, {"from": whale})
    whalebefore = token_ecrv.balanceOf(whale)
    whale_deposit = 100 * 1e18
    vault_ecrv.deposit(whale_deposit, {"from": whale})
    strategy_ecrv.harvest({"from": strategist})

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    strategy_ecrv.harvest({"from": strategist})

    print("seth = ", token_seth.balanceOf(strategy_ecrv) / 1e18)
    print("ecrv = ", strategy_ecrv.balance() / 1e18)

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault_ecrv.totalAssets() - 100 * 1e18) * 12) / (100 * 1e18)),
    )

    vault_ecrv.withdraw({"from": whale})
    print("\nWithdraw")
    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)
    print("Whale profit: ", (token_ecrv.balanceOf(whale) - whalebefore) / 1e18)


def test_migrate(
    token_ecrv, Strategy, strategy_ecrv, chain, vault_ecrv, whale, gov, strategist
):
    rate_limit = 1_000_000_000 * 1e18
    debt_ratio = 10_000
    vault_ecrv.addStrategy(strategy_ecrv, debt_ratio, rate_limit, 1000, {"from": gov})

    token_ecrv.approve(vault_ecrv, 2 ** 256 - 1, {"from": whale})
    whale_deposit = 100 * 1e18
    vault_ecrv.deposit(whale_deposit, {"from": whale})
    strategy_ecrv.harvest({"from": strategist})

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)

    chain.sleep(2592000)
    chain.mine(1)

    strategy_ecrv.harvest({"from": strategist})

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault_ecrv.totalAssets() - 100 * 1e18) * 12) / (100 * 1e18)),
    )

    strategy_ecrv2 = strategist.deploy(Strategy, vault_ecrv)
    vault_ecrv.migrateStrategy(strategy_ecrv, strategy_ecrv2, {"from": gov})
    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfStrat(strategy_ecrv2, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)


def test_reduce_limit(token_ecrv, strategy_ecrv, vault_ecrv, whale, gov, strategist):
    rate_limit = 1_000_000_000 * 1e18
    debt_ratio = 10_000
    vault_ecrv.addStrategy(strategy_ecrv, debt_ratio, rate_limit, 1000, {"from": gov})

    token_ecrv.approve(vault_ecrv, 2 ** 256 - 1, {"from": whale})
    whale_deposit = 100 * 1e18
    vault_ecrv.deposit(whale_deposit, {"from": whale})
    strategy_ecrv.harvest({"from": strategist})

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)

    vault_ecrv.revokeStrategy(strategy_ecrv, {"from": gov})

    strategy_ecrv.harvest({"from": strategist})

    genericStateOfStrat(strategy_ecrv, token_ecrv, vault_ecrv)
    genericStateOfVault(vault_ecrv, token_ecrv)
