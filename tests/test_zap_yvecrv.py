from brownie import Wei, web3


def test_zap(accounts, ZapYveCRV, interface, chain):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYveCRV)
    sETH = interface.ISynth(zap.sETH())
    sUSD = interface.ISynth(zap.sUSD())
    synthetixExchanger = interface.IExchanger(zap.SynthetixExchanger())

    delegateApprovals = interface.DelegateApprovals("0x15fd6e554874B9e70F832Ed37f231Ac5E142362f")
    delegateApprovals.approveExchangeOnBehalf(zap, {"from": whale})
    sETH.approve(zap.address, 2 ** 256 - 1, {"from": whale})
    sUSD.approve(zap.address, 2 ** 256 - 1, {"from": whale})

    print("Zap In 10 ETH eCRV estimates")
    print("----------------------------")
    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 0) / Wei("1 ether")
    print(f"  0% swap: {lpTokenEstimate} eCRV")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 50) / Wei("1 ether")
    print(f" 50% swap: {lpTokenEstimate} eCRV")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("10 ether"), 100) / Wei("1 ether")
    print(f"100% swap: {lpTokenEstimate} eCRV")

    print("")
    print("Zap In 10 ETH actuals")
    print("----------------------------")

    zap.swapEthToSeth({"from": whale, "value": Wei("10 ether")})
    sethBalance = sETH.balanceOf(whale) / Wei("1 ether")
    print(f"sETH actual, 100% swap: {sethBalance} sETH")

    waitLeft = synthetixExchanger.maxSecsLeftInWaitingPeriod(whale.address, web3.toBytes(text="sETH"))
    print(f"> Waiting period: {waitLeft} seconds")
    chain.sleep(waitLeft)
    # chain.sleep(600)
    chain.mine(1)

    # zap.zapIn(sethBalance, {"from": whale})
