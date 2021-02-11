from brownie import Wei, web3


def test_zap(accounts, ZapYvecrvSwapSeth, vault_ecrv_live):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYvecrvSwapSeth)
    vault_ecrv_live.approve(zap.address, 2 ** 256 - 1, {"from": whale})

    print("Zap In 100 ETH eCRV estimates")
    print("----------------------------")
    lpTokenEstimate, _ = zap.estimateZapIn(Wei("100 ether"), 0)
    lpTokenEstimatePretty = lpTokenEstimate / Wei("1 ether")
    print(f"  0% swap: {lpTokenEstimatePretty} eCRV")

    lpTokenEstimate, _ = zap.estimateZapIn(Wei("100 ether"), 50)
    lpTokenEstimatePretty = lpTokenEstimate / Wei("1 ether")
    print(f" 50% swap: {lpTokenEstimatePretty} eCRV")

    lpTokenEstimate, _ = zap.estimateZapIn(Wei("100 ether"), 100)
    lpTokenEstimatePretty = lpTokenEstimate / Wei("1 ether")
    print(f"100% swap: {lpTokenEstimatePretty} eCRV")

    print("")
    print("Zap In 100 ETH actuals")
    print("----------------------------")

    zap.zapIn(0, {"from": whale, "value": Wei("100 ether")})
    yvTokens = vault_ecrv_live.balanceOf(whale)
    yvTokensPretty = yvTokens / Wei("1 ether")
    print(f"Zap in: {yvTokensPretty} yveCRV")

    startingEthBalance = whale.balance()
    
    zap.zapOut(yvTokens, 0, {"from": whale})
    zappedOutEth = whale.balance() - startingEthBalance
    zappedOutEthPretty = zappedOutEth / Wei("1 ether")
    print(f"Zap out: {zappedOutEthPretty} ETH")
