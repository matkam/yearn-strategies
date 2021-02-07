from brownie import Wei, web3


def test_zap(accounts, ZapYvecrv, vault_ecrv_live):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYvecrv)
    vault_ecrv_live.approve(zap.address, 2 ** 256 - 1, {"from": whale})

    zap.zapIn(0, {"from": whale, "value": Wei("100 ether")})
    yvTokens = vault_ecrv_live.balanceOf(whale)
    yvTokensPretty = yvTokens / Wei("1 ether")
    print(f"Zap in 100 ETH: {yvTokensPretty} yveCRV")

    startingEthBalance = whale.balance()
    zap.zapOut(yvTokens, 0, {"from": whale})
    zappedOutEth = whale.balance() - startingEthBalance
    zappedOutEthPretty = zappedOutEth / Wei("1 ether")
    print(f"Zap out all: {zappedOutEthPretty} ETH")
