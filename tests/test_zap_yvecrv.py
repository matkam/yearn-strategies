from brownie import Wei


def test_zap(accounts, ZapYveCRV, interface, chain):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYveCRV)
    sETH = interface.ISynth(zap.sETH())

    delegateApprovals = interface.DelegateApprovals(
        "0x15fd6e554874B9e70F832Ed37f231Ac5E142362f"
    )
    delegateApprovals.approveExchangeOnBehalf(zap, {"from": whale})
    sETH.approve(zap.address, 2 ** 256 - 1, {"from": whale})

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 0)
    print(f"  0 pcnt swap estimate: {lpTokenEstimate}")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 50)
    print(f" 50 pcnt swap estimate: {lpTokenEstimate}")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 50)
    print(f"100 pcnt swap estimate: {lpTokenEstimate}")

    print("")

    zap.swapEthToSeth({"from": whale, "value": Wei("10 ether")})
    sethBalance = sETH.balanceOf(whale)
    print(f"  100 pct Swapped sETH: {sethBalance}")

    chain.sleep(600)
    chain.mine(1)

    zap.zapIn(sethBalance, {"from": whale})
